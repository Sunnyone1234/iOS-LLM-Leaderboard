import Foundation
import PowerEvidence

public struct PowerRunner: Sendable {
    private let runtime: any PowerRuntimeAdapter
    private let target: any PowerTargetAdapter
    private let clock: any PowerMonotonicClock
    private let checkpointSink: (any PowerAttemptCheckpointSink)?
    private let timestamp: @Sendable () -> String
    private let memorySamplingInterval: Duration

    public init(
        runtime: any PowerRuntimeAdapter,
        target: any PowerTargetAdapter,
        clock: any PowerMonotonicClock = ContinuousPowerMonotonicClock(),
        checkpointSink: (any PowerAttemptCheckpointSink)? = nil,
        memorySamplingInterval: Duration = .milliseconds(50),
        timestamp: @escaping @Sendable () -> String = {
            PowerEvidenceTimestamp.string(from: Date())
        }
    ) {
        self.runtime = runtime
        self.target = target
        self.clock = clock
        self.checkpointSink = checkpointSink
        self.timestamp = timestamp
        self.memorySamplingInterval = memorySamplingInterval
    }

    public func run(
        requests: [PowerRunnerAttemptRequest]
    ) async throws -> PowerRunnerSession {
        let startedAt = timestamp()
        let targetAtStart = try await target.captureStart()
        let runtimeIdentity = await runtime.identity
        var attempts: [PowerRunnerAttemptRecord] = []
        var stopReason: PowerAttemptFailure?
        try await checkpointSink?.beginSession(
            .init(
                startedAt: startedAt,
                targetAtStart: targetAtStart,
                runtimeIdentity: runtimeIdentity,
                expectedAttemptCount: requests.count
            )
        )

        for request in requests {
            if let stopReason {
                let state = await target.currentThermalState()
                let record = notRun(
                    request,
                    thermalState: state,
                    failure: stopReason
                )
                attempts.append(record)
                try await checkpointSink?.record(record)
                continue
            }

            let thermalAtStart = await target.currentThermalState()
            if thermalAtStart == .critical {
                let failure = PowerAttemptFailure(
                    code: "thermal_state_critical_before_attempt",
                    message: "The attempt was not started at critical thermal state."
                )
                stopReason = failure
                let record = notRun(
                    request,
                    thermalState: thermalAtStart,
                    failure: failure
                )
                attempts.append(record)
                try await checkpointSink?.record(record)
                continue
            }

            let attemptStartedAt = timestamp()
            do {
                try await checkpointSink?.markAttemptStarted(
                    index: request.index,
                    phase: request.phase,
                    startedAt: attemptStartedAt,
                    thermalStateAtStart: thermalAtStart
                )
            } catch {
                let failure = PowerAttemptFailure(
                    code: "evidence_checkpoint_unavailable",
                    message: String(describing: error)
                )
                stopReason = failure
                attempts.append(
                    failedBeforeExecution(
                        request,
                        startedAt: attemptStartedAt,
                        thermalState: thermalAtStart,
                        failure: failure
                    )
                )
                continue
            }

            var record = await execute(
                request,
                startedAt: attemptStartedAt,
                thermalStateAtStart: thermalAtStart
            )
            do {
                try await checkpointSink?.record(record)
            } catch {
                let failure = PowerAttemptFailure(
                    code: "evidence_checkpoint_unavailable",
                    message: String(describing: error)
                )
                record = PowerRunnerAttemptRecord(
                    index: record.index,
                    phase: record.phase,
                    outcome: .failed,
                    startedAt: record.startedAt,
                    endedAt: record.endedAt,
                    requestAcceptedNanoseconds:
                        record.requestAcceptedNanoseconds,
                    firstTokenNanoseconds: record.firstTokenNanoseconds,
                    firstRenderableNanoseconds:
                        record.firstRenderableNanoseconds,
                    completedNanoseconds: record.completedNanoseconds,
                    promptEvaluationNanoseconds:
                        record.promptEvaluationNanoseconds,
                    decodeNanoseconds: record.decodeNanoseconds,
                    inputTokenCount: record.inputTokenCount,
                    outputTokenCount: record.outputTokenCount,
                    tokenEvents: record.tokenEvents,
                    generatedText: record.generatedText,
                    peakPhysicalFootprintBytes:
                        record.peakPhysicalFootprintBytes,
                    memorySamples: record.memorySamples,
                    thermalStateAtStart: record.thermalStateAtStart,
                    thermalStateAtEnd: record.thermalStateAtEnd,
                    thermalTransitions: record.thermalTransitions,
                    failure: failure
                )
                stopReason = failure
            }
            attempts.append(record)
        }

        let completion = PowerRunnerSessionCompletion(
            endedAt: timestamp(),
            thermalStateAtEnd: await target.currentThermalState()
        )
        try await checkpointSink?.finishSession(completion)
        return PowerRunnerSession(
            startedAt: startedAt,
            endedAt: completion.endedAt,
            targetAtStart: targetAtStart,
            thermalStateAtEnd: completion.thermalStateAtEnd,
            runtimeIdentity: runtimeIdentity,
            attempts: attempts
        )
    }

    private func execute(
        _ request: PowerRunnerAttemptRequest,
        startedAt: String,
        thermalStateAtStart: PowerThermalState
    ) async -> PowerRunnerAttemptRecord {
        let requestAccepted = clock.nowNanoseconds()
        let collector = AttemptCollector(
            requestAcceptedNanoseconds: requestAccepted,
            clock: clock,
            target: target,
            initialThermalState: thermalStateAtStart
        )
        await collector.sampleEnvironment()
        let samplingTask = Task {
            await collector.sampleEnvironmentUntilCancelled(
                interval: memorySamplingInterval
            )
        }

        let outcome: PowerAttemptOutcome
        let result: PowerRuntimeGenerationResult?
        let failure: PowerAttemptFailure?

        do {
            let value = try await runtime.generate(
                request: request.runtimeRequest
            ) { token in
                await collector.record(token)
            } onRenderability: { probe in
                await collector.record(probe)
            }
            result = value
            outcome = .succeeded
            failure = nil
        } catch is CancellationError {
            result = nil
            outcome = .cancelled
            failure = .init(
                code: "execution_cancelled",
                message: "The attempt was cancelled before completion."
            )
        } catch {
            result = nil
            switch Self.classify(error) {
            case .failed(let code):
                outcome = .failed
                failure = .init(code: code, message: String(describing: error))
            case .outOfMemory(let code):
                outcome = .oom
                failure = .init(code: code, message: String(describing: error))
            }
        }

        samplingTask.cancel()
        await samplingTask.value
        await collector.sampleEnvironment()

        let completed = clock.nowNanoseconds().subtractingWithoutUnderflow(
            requestAccepted
        )
        let thermalAtEnd = await target.currentThermalState()
        return PowerRunnerAttemptRecord(
            index: request.index,
            phase: request.phase,
            outcome: outcome,
            startedAt: startedAt,
            endedAt: timestamp(),
            requestAcceptedNanoseconds: 0,
            firstTokenNanoseconds: await collector.firstTokenNanoseconds,
            firstRenderableNanoseconds:
                await collector.firstRenderableNanoseconds,
            completedNanoseconds: outcome == .succeeded ? completed : nil,
            promptEvaluationNanoseconds:
                result?.promptEvaluationNanoseconds,
            decodeNanoseconds: await collector.decodeNanoseconds,
            inputTokenCount: result?.inputTokenCount ?? 0,
            outputTokenCount: result?.outputTokenCount ?? 0,
            tokenEvents: await collector.tokenEvents,
            generatedText: result?.generatedText ?? "",
            peakPhysicalFootprintBytes:
                await collector.peakPhysicalFootprintBytes,
            memorySamples: await collector.memorySamples,
            thermalStateAtStart: thermalStateAtStart,
            thermalStateAtEnd: thermalAtEnd,
            thermalTransitions: await collector.thermalTransitions,
            failure: failure
        )
    }

    private func notRun(
        _ request: PowerRunnerAttemptRequest,
        thermalState: PowerThermalState,
        failure: PowerAttemptFailure
    ) -> PowerRunnerAttemptRecord {
        let instant = timestamp()
        return PowerRunnerAttemptRecord(
            index: request.index,
            phase: request.phase,
            outcome: .notRun,
            startedAt: instant,
            endedAt: instant,
            requestAcceptedNanoseconds: 0,
            firstTokenNanoseconds: nil,
            firstRenderableNanoseconds: nil,
            completedNanoseconds: nil,
            promptEvaluationNanoseconds: nil,
            decodeNanoseconds: nil,
            inputTokenCount: 0,
            outputTokenCount: 0,
            tokenEvents: [],
            generatedText: "",
            peakPhysicalFootprintBytes: nil,
            memorySamples: [],
            thermalStateAtStart: thermalState,
            thermalStateAtEnd: thermalState,
            thermalTransitions: [],
            failure: failure
        )
    }

    private func failedBeforeExecution(
        _ request: PowerRunnerAttemptRequest,
        startedAt: String,
        thermalState: PowerThermalState,
        failure: PowerAttemptFailure
    ) -> PowerRunnerAttemptRecord {
        PowerRunnerAttemptRecord(
            index: request.index,
            phase: request.phase,
            outcome: .failed,
            startedAt: startedAt,
            endedAt: timestamp(),
            requestAcceptedNanoseconds: 0,
            firstTokenNanoseconds: nil,
            firstRenderableNanoseconds: nil,
            completedNanoseconds: nil,
            promptEvaluationNanoseconds: nil,
            decodeNanoseconds: nil,
            inputTokenCount: 0,
            outputTokenCount: 0,
            tokenEvents: [],
            generatedText: "",
            peakPhysicalFootprintBytes: nil,
            memorySamples: [],
            thermalStateAtStart: thermalState,
            thermalStateAtEnd: thermalState,
            thermalTransitions: [],
            failure: failure
        )
    }

    private static func classify(_ error: Error) -> PowerRuntimeFailureKind {
        if let classified =
            error as? any PowerRuntimeFailureClassifyingError
        {
            return classified.powerRuntimeFailureKind
        }
        let value = error as NSError
        if value.domain == NSPOSIXErrorDomain && value.code == Int(ENOMEM) {
            return .outOfMemory(code: "runtime_out_of_memory")
        }
        return .failed(code: "runtime_error")
    }
}

private actor AttemptCollector {
    private struct MutableTokenEvent {
        let index: Int
        let tokenID: Int
        let receivedNanoseconds: UInt64
        var decodedAtNanoseconds: UInt64?
        var decodedPrefix: String?
        var isSpecial: Bool?
        var isRenderable: Bool?
    }

    private let requestAcceptedNanoseconds: UInt64
    private let clock: any PowerMonotonicClock
    private let target: any PowerTargetAdapter
    private var rawTokenEvents: [Int: MutableTokenEvent] = [:]
    private var lastThermalState: PowerThermalState
    private var renderabilityProbeCount = 0

    private(set) var firstTokenNanoseconds: UInt64?
    private(set) var firstRenderableNanoseconds: UInt64?
    private(set) var memorySamples: [PowerMemorySample] = []
    private(set) var thermalTransitions: [PowerThermalTransition] = []

    var tokenEvents: [PowerTokenEvent] {
        rawTokenEvents.values
            .sorted { $0.index < $1.index }
            .map {
                PowerTokenEvent(
                    index: $0.index,
                    tokenID: $0.tokenID,
                    receivedNanoseconds: $0.receivedNanoseconds,
                    decodedAtNanoseconds: $0.decodedAtNanoseconds,
                    decodedPrefix: $0.decodedPrefix,
                    isSpecial: $0.isSpecial,
                    isRenderable: $0.isRenderable
                )
            }
    }

    var peakPhysicalFootprintBytes: UInt64? {
        memorySamples.map(\.physicalFootprintBytes).max()
    }

    var decodeNanoseconds: UInt64? {
        let events = rawTokenEvents.values.sorted {
            $0.receivedNanoseconds < $1.receivedNanoseconds
        }
        guard let first = events.first,
              let last = events.last,
              events.count >= 2,
              last.receivedNanoseconds >= first.receivedNanoseconds
        else {
            return nil
        }
        return last.receivedNanoseconds - first.receivedNanoseconds
    }

    init(
        requestAcceptedNanoseconds: UInt64,
        clock: any PowerMonotonicClock,
        target: any PowerTargetAdapter,
        initialThermalState: PowerThermalState
    ) {
        self.requestAcceptedNanoseconds = requestAcceptedNanoseconds
        self.clock = clock
        self.target = target
        self.lastThermalState = initialThermalState
    }

    func record(_ token: PowerRuntimeToken) {
        let elapsed = clock.nowNanoseconds().subtractingWithoutUnderflow(
            requestAcceptedNanoseconds
        )
        rawTokenEvents[token.index] = MutableTokenEvent(
            index: token.index,
            tokenID: token.tokenID,
            receivedNanoseconds: elapsed,
            decodedAtNanoseconds: nil,
            decodedPrefix: nil,
            isSpecial: nil,
            isRenderable: nil
        )
        if firstTokenNanoseconds == nil {
            firstTokenNanoseconds = elapsed
        }
    }

    func record(_ probe: PowerRuntimeRenderability) -> Bool {
        guard
            firstRenderableNanoseconds == nil,
            renderabilityProbeCount
                < PowerRunnerLimits.maximumRenderabilityProbeEvents,
            var event = rawTokenEvents[probe.tokenIndex],
            event.decodedAtNanoseconds == nil
        else {
            return false
        }
        renderabilityProbeCount += 1
        let elapsed = clock.nowNanoseconds().subtractingWithoutUnderflow(
            requestAcceptedNanoseconds
        )
        let renderable =
            !probe.isSpecial
            && probe.decodedPrefix.unicodeScalars.contains(
                where: { !$0.properties.isWhitespace }
            )
        event.decodedAtNanoseconds = elapsed
        event.decodedPrefix = probe.decodedPrefix
        event.isSpecial = probe.isSpecial
        event.isRenderable = renderable
        rawTokenEvents[probe.tokenIndex] = event
        if firstRenderableNanoseconds == nil, renderable {
            firstRenderableNanoseconds = elapsed
        }
        return !renderable
            && renderabilityProbeCount
                < PowerRunnerLimits.maximumRenderabilityProbeEvents
    }

    func sampleEnvironment() async {
        let elapsed = clock.nowNanoseconds().subtractingWithoutUnderflow(
            requestAcceptedNanoseconds
        )
        if let value = await target.currentPhysicalFootprintBytes() {
            memorySamples.append(
                .init(
                    elapsedNanoseconds: elapsed,
                    physicalFootprintBytes: value
                )
            )
        }
        let thermalState = await target.currentThermalState()
        if thermalState != lastThermalState {
            thermalTransitions.append(
                .init(elapsedNanoseconds: elapsed, state: thermalState)
            )
            lastThermalState = thermalState
        }
    }

    func sampleEnvironmentUntilCancelled(interval: Duration) async {
        while !Task.isCancelled {
            await sampleEnvironment()
            do {
                try await Task.sleep(for: interval)
            } catch {
                return
            }
        }
    }
}

private extension UInt64 {
    func subtractingWithoutUnderflow(_ other: UInt64) -> UInt64 {
        self >= other ? self - other : 0
    }
}
