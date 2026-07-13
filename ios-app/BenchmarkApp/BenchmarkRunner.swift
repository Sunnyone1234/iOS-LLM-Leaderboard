import Darwin
import Foundation

struct BenchmarkProcedure: Sendable, Equatable {
    let warmupRuns: Int
    let measuredRuns: Int
    let outputTokenLimit: Int
}

struct ProcessMemorySample: Codable, Sendable, Equatable {
    let elapsedNanoseconds: UInt64
    let physicalFootprintBytes: UInt64
}

struct ThermalTransition: Codable, Sendable, Equatable {
    let elapsedNanoseconds: UInt64
    let state: String
}

enum BenchmarkFailureClassification: Sendable, Equatable {
    case failed(reasonCode: String)
    case outOfMemory(reasonCode: String)
}

protocol BenchmarkFailureClassifyingError: Error {
    var benchmarkFailureClassification: BenchmarkFailureClassification { get }
}

struct BenchmarkAttempt: Codable, Sendable, Equatable {
    enum Role: String, Codable, Sendable {
        case warmup
        case measured
    }

    enum Outcome: Sendable, Equatable {
        case completed(RuntimeGenerationResult)
        case failed(message: String, reasonCode: String)
        case cancelled(reasonCode: String, partial: RuntimeGenerationResult?)
        case outOfMemory(reasonCode: String, partial: RuntimeGenerationResult?)
        case notRun(reason: String)

        var generation: RuntimeGenerationResult? {
            switch self {
            case .completed(let value): value
            case .cancelled(_, let partial), .outOfMemory(_, let partial): partial
            case .failed, .notRun: nil
            }
        }

        var reasonCodes: [String] {
            switch self {
            case .completed: []
            case .failed(_, let reasonCode),
                 .cancelled(let reasonCode, _),
                 .outOfMemory(let reasonCode, _): [reasonCode]
            case .notRun(let reason): [reason]
            }
        }
    }

    let index: Int
    let role: Role
    let tokens: [RuntimeToken]
    let peakMemoryBytes: UInt64?
    let memorySamples: [ProcessMemorySample]
    let thermalStateBefore: String
    let thermalStateAfter: String
    let thermalTransitions: [ThermalTransition]
    let outcome: Outcome

    init(
        index: Int,
        role: Role,
        tokens: [RuntimeToken],
        peakMemoryBytes: UInt64?,
        memorySamples: [ProcessMemorySample] = [],
        thermalStateBefore: String,
        thermalStateAfter: String,
        thermalTransitions: [ThermalTransition] = [],
        outcome: Outcome
    ) {
        self.index = index
        self.role = role
        self.tokens = tokens
        self.peakMemoryBytes = peakMemoryBytes
        self.memorySamples = memorySamples
        self.thermalStateBefore = thermalStateBefore
        self.thermalStateAfter = thermalStateAfter
        self.thermalTransitions = thermalTransitions
        self.outcome = outcome
    }
}

extension BenchmarkAttempt.Outcome: Codable {
    private enum CodingKeys: String, CodingKey {
        case type
        case generation
        case message
        case reasonCode
    }

    private enum Kind: String, Codable {
        case completed
        case failed
        case cancelled
        case outOfMemory
        case notRun
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let kind = try container.decode(Kind.self, forKey: .type)
        switch kind {
        case .completed:
            self = .completed(
                try container.decode(RuntimeGenerationResult.self, forKey: .generation)
            )
        case .failed:
            self = .failed(
                message: try container.decode(String.self, forKey: .message),
                reasonCode: try container.decode(String.self, forKey: .reasonCode)
            )
        case .cancelled:
            self = .cancelled(
                reasonCode: try container.decode(String.self, forKey: .reasonCode),
                partial: try container.decodeIfPresent(
                    RuntimeGenerationResult.self,
                    forKey: .generation
                )
            )
        case .outOfMemory:
            self = .outOfMemory(
                reasonCode: try container.decode(String.self, forKey: .reasonCode),
                partial: try container.decodeIfPresent(
                    RuntimeGenerationResult.self,
                    forKey: .generation
                )
            )
        case .notRun:
            self = .notRun(
                reason: try container.decode(String.self, forKey: .reasonCode)
            )
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        switch self {
        case .completed(let generation):
            try container.encode(Kind.completed, forKey: .type)
            try container.encode(generation, forKey: .generation)
        case .failed(let message, let reasonCode):
            try container.encode(Kind.failed, forKey: .type)
            try container.encode(message, forKey: .message)
            try container.encode(reasonCode, forKey: .reasonCode)
        case .cancelled(let reasonCode, let partial):
            try container.encode(Kind.cancelled, forKey: .type)
            try container.encodeIfPresent(partial, forKey: .generation)
            try container.encode(reasonCode, forKey: .reasonCode)
        case .outOfMemory(let reasonCode, let partial):
            try container.encode(Kind.outOfMemory, forKey: .type)
            try container.encodeIfPresent(partial, forKey: .generation)
            try container.encode(reasonCode, forKey: .reasonCode)
        case .notRun(let reason):
            try container.encode(Kind.notRun, forKey: .type)
            try container.encode(reason, forKey: .reasonCode)
        }
    }
}

struct BenchmarkSession: Sendable, Equatable {
    let sessionID: UUID
    let startedAt: Date
    let endedAt: Date
    let thermalStateAtStart: String
    let thermalStateAtEnd: String
    let runtimeIdentity: String
    let attempts: [BenchmarkAttempt]

    var measuredAttempts: [BenchmarkAttempt] {
        attempts.filter { $0.role == .measured }
    }
}

struct BenchmarkRunner: Sendable {
    let runtime: any LanguageModelRuntime
    let procedure: BenchmarkProcedure
    var sessionID = UUID()
    var checkpointStore: PowerSessionCheckpointStore?
    var thermalState: @Sendable () -> String = {
        SystemMeasurements.thermalState
    }
    var memoryFootprint: @Sendable () -> UInt64? = {
        ProcessMemory.physicalFootprintBytes()
    }

    func run(prompt: String) async -> BenchmarkSession {
        let startedAt = Date()
        let sessionThermalStart = thermalState()
        var attempts: [BenchmarkAttempt] = []
        let totalRuns = procedure.warmupRuns + procedure.measuredRuns
        var stoppedForCriticalThermalState = false
        var checkpointUnavailable = false

        for index in 0..<totalRuns {
            let role: BenchmarkAttempt.Role =
                index < procedure.warmupRuns ? .warmup : .measured
            let thermalStateBefore = thermalState()
            if thermalStateBefore == "critical" {
                stoppedForCriticalThermalState = true
            }
            if checkpointUnavailable || stoppedForCriticalThermalState {
                let reason = checkpointUnavailable
                    ? "prior_attempt_unrecoverable"
                    : "thermal_state_critical_before_attempt"
                let attempt = BenchmarkAttempt(
                    index: index,
                    role: role,
                    tokens: [],
                    peakMemoryBytes: nil,
                    thermalStateBefore: thermalStateBefore,
                    thermalStateAfter: thermalStateBefore,
                    outcome: .notRun(reason: reason)
                )
                attempts.append(attempt)
                try? await checkpointStore?.record(attempt)
                continue
            }

            do {
                try await checkpointStore?.markAttemptStarted(
                    index: index,
                    role: role,
                    thermalStateBefore: thermalStateBefore
                )
            } catch {
                checkpointUnavailable = true
                let attempt = BenchmarkAttempt(
                    index: index,
                    role: role,
                    tokens: [],
                    peakMemoryBytes: nil,
                    thermalStateBefore: thermalStateBefore,
                    thermalStateAfter: thermalState(),
                    outcome: .failed(
                        message: String(describing: error),
                        reasonCode: "evidence_capture_error"
                    )
                )
                attempts.append(attempt)
                continue
            }

            let collector = TokenCollector(
                initialThermalState: thermalStateBefore,
                memoryFootprint: memoryFootprint,
                thermalState: thermalState
            )
            let evidenceSamplingTask = await collector.startSampling()
            let outcome: BenchmarkAttempt.Outcome

            do {
                let result = try await runtime.generate(
                    prompt: prompt,
                    outputTokenLimit: procedure.outputTokenLimit
                ) { token in
                    await collector.append(token)
                }
                if result.stopReason == .cancelled {
                    outcome = .cancelled(
                        reasonCode: "system_cancelled",
                        partial: result
                    )
                } else {
                    outcome = .completed(result)
                }
            } catch is CancellationError {
                outcome = .cancelled(reasonCode: "user_cancelled", partial: nil)
            } catch {
                switch Self.classify(error) {
                case .failed(let reasonCode):
                    outcome = .failed(
                        message: String(describing: error),
                        reasonCode: reasonCode
                    )
                case .outOfMemory(let reasonCode):
                    outcome = .outOfMemory(reasonCode: reasonCode, partial: nil)
                }
            }

            evidenceSamplingTask.cancel()
            await evidenceSamplingTask.value
            await collector.sample()
            var attempt = BenchmarkAttempt(
                index: index,
                role: role,
                tokens: await collector.tokens,
                peakMemoryBytes: await collector.peakMemoryBytes,
                memorySamples: await collector.memorySamples,
                thermalStateBefore: thermalStateBefore,
                thermalStateAfter: thermalState(),
                thermalTransitions: await collector.thermalTransitions,
                outcome: outcome
            )

            do {
                try await checkpointStore?.record(attempt)
            } catch {
                checkpointUnavailable = true
                attempt = BenchmarkAttempt(
                    index: index,
                    role: role,
                    tokens: attempt.tokens,
                    peakMemoryBytes: attempt.peakMemoryBytes,
                    memorySamples: attempt.memorySamples,
                    thermalStateBefore: attempt.thermalStateBefore,
                    thermalStateAfter: attempt.thermalStateAfter,
                    thermalTransitions: attempt.thermalTransitions,
                    outcome: .failed(
                        message: String(describing: error),
                        reasonCode: "evidence_capture_error"
                    )
                )
                try? await checkpointStore?.record(attempt)
            }
            attempts.append(attempt)
        }

        let endedAt = Date()
        let thermalStateAtEnd = thermalState()
        try? await checkpointStore?.markReadyForExport(
            endedAt: endedAt,
            thermalStateAtEnd: thermalStateAtEnd
        )
        return BenchmarkSession(
            sessionID: sessionID,
            startedAt: startedAt,
            endedAt: endedAt,
            thermalStateAtStart: sessionThermalStart,
            thermalStateAtEnd: thermalStateAtEnd,
            runtimeIdentity: runtime.identity,
            attempts: attempts
        )
    }

    private static func classify(_ error: Error) -> BenchmarkFailureClassification {
        if let classified = error as? any BenchmarkFailureClassifyingError {
            return classified.benchmarkFailureClassification
        }
        let cocoa = error as NSError
        if cocoa.domain == NSPOSIXErrorDomain && cocoa.code == Int(ENOMEM) {
            return .outOfMemory(reasonCode: "runtime_out_of_memory")
        }
        return .failed(reasonCode: "runtime_error")
    }
}

private actor TokenCollector {
    private let startedAt = ContinuousClock.now
    private let memoryFootprint: @Sendable () -> UInt64?
    private let thermalState: @Sendable () -> String
    private var lastThermalState: String

    private(set) var tokens: [RuntimeToken] = []
    private(set) var memorySamples: [ProcessMemorySample] = []
    private(set) var thermalTransitions: [ThermalTransition] = []

    var peakMemoryBytes: UInt64? {
        memorySamples.map(\.physicalFootprintBytes).max()
    }

    init(
        initialThermalState: String,
        memoryFootprint: @escaping @Sendable () -> UInt64?,
        thermalState: @escaping @Sendable () -> String
    ) {
        self.lastThermalState = initialThermalState
        self.memoryFootprint = memoryFootprint
        self.thermalState = thermalState
    }

    func append(_ token: RuntimeToken) {
        tokens.append(token)
    }

    func startSampling() -> Task<Void, Never> {
        Task { [weak self] in
            while !Task.isCancelled {
                await self?.sample()
                try? await Task.sleep(for: .milliseconds(50))
            }
        }
    }

    func sample() {
        let elapsed = startedAt.duration(to: .now).benchmarkNanoseconds
        if let bytes = memoryFootprint(), bytes > 0 {
            memorySamples.append(
                .init(
                    elapsedNanoseconds: elapsed,
                    physicalFootprintBytes: bytes
                )
            )
        }
        let current = thermalState()
        if current != lastThermalState {
            thermalTransitions.append(
                .init(elapsedNanoseconds: elapsed, state: current)
            )
            lastThermalState = current
        }
    }
}

private extension Duration {
    var benchmarkNanoseconds: UInt64 {
        let components = self.components
        let seconds = max(components.seconds, 0)
        let attoseconds = max(components.attoseconds, 0)
        return UInt64(seconds) * 1_000_000_000
            + UInt64(attoseconds / 1_000_000_000)
    }
}
