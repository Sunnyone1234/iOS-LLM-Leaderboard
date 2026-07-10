import Foundation

struct BenchmarkProcedure: Sendable, Equatable {
    let warmupRuns: Int
    let measuredRuns: Int
    let outputTokenLimit: Int

}

struct BenchmarkAttempt: Sendable, Equatable {
    enum Role: String, Sendable {
        case warmup
        case measured
    }

    enum Outcome: Sendable, Equatable {
        case completed(RuntimeGenerationResult)
        case failed(message: String)
        case notRun(reason: String)
    }

    let index: Int
    let role: Role
    let tokens: [RuntimeToken]
    let peakMemoryBytes: UInt64?
    let thermalStateBefore: String
    let thermalStateAfter: String
    let outcome: Outcome
}

struct BenchmarkSession: Sendable, Equatable {
    let runtimeIdentity: String
    let attempts: [BenchmarkAttempt]

    var measuredAttempts: [BenchmarkAttempt] {
        attempts.filter { $0.role == .measured }
    }
}

struct BenchmarkRunner: Sendable {
    let runtime: any LanguageModelRuntime
    let procedure: BenchmarkProcedure
    var thermalState: @Sendable () -> String = {
        SystemMeasurements.thermalState
    }

    func run(prompt: String) async -> BenchmarkSession {
        var attempts: [BenchmarkAttempt] = []
        let totalRuns = procedure.warmupRuns + procedure.measuredRuns
        var stoppedForCriticalThermalState = false

        for index in 0..<totalRuns {
            let role: BenchmarkAttempt.Role =
                index < procedure.warmupRuns ? .warmup : .measured
            let thermalStateBefore = thermalState()
            if thermalStateBefore == "critical" {
                stoppedForCriticalThermalState = true
            }
            if stoppedForCriticalThermalState {
                attempts.append(
                    BenchmarkAttempt(
                        index: index,
                        role: role,
                        tokens: [],
                        peakMemoryBytes: nil,
                        thermalStateBefore: thermalStateBefore,
                        thermalStateAfter: thermalStateBefore,
                        outcome: .notRun(
                            reason: "thermal_state_critical_before_attempt"
                        )
                    )
                )
                continue
            }
            let collector = TokenCollector()
            let memorySamplingTask = await collector.startMemorySampling()

            do {
                let result = try await runtime.generate(
                    prompt: prompt,
                    outputTokenLimit: procedure.outputTokenLimit
                ) { token in
                    await collector.append(token)
                }
                memorySamplingTask.cancel()
                await memorySamplingTask.value
                await collector.sampleMemory()
                attempts.append(
                    BenchmarkAttempt(
                        index: index,
                        role: role,
                        tokens: await collector.values,
                        peakMemoryBytes: await collector.peakMemoryBytes,
                        thermalStateBefore: thermalStateBefore,
                        thermalStateAfter: thermalState(),
                        outcome: .completed(result)
                    )
                )
            } catch {
                memorySamplingTask.cancel()
                await memorySamplingTask.value
                await collector.sampleMemory()
                attempts.append(
                    BenchmarkAttempt(
                        index: index,
                        role: role,
                        tokens: await collector.values,
                        peakMemoryBytes: await collector.peakMemoryBytes,
                        thermalStateBefore: thermalStateBefore,
                        thermalStateAfter: thermalState(),
                        outcome: .failed(message: String(describing: error))
                    )
                )
            }
        }

        return BenchmarkSession(
            runtimeIdentity: runtime.identity,
            attempts: attempts
        )
    }
}

private actor TokenCollector {
    private(set) var values: [RuntimeToken] = []
    private(set) var peakMemoryBytes: UInt64?

    func append(_ token: RuntimeToken) {
        values.append(token)
    }

    func startMemorySampling() -> Task<Void, Never> {
        Task { [weak self] in
            while !Task.isCancelled {
                await self?.sampleMemory()
                try? await Task.sleep(for: .milliseconds(50))
            }
        }
    }

    func sampleMemory() {
        record(ProcessMemory.physicalFootprintBytes())
    }

    private func record(_ bytes: UInt64?) {
        guard let bytes else { return }
        peakMemoryBytes = max(peakMemoryBytes ?? 0, bytes)
    }
}
