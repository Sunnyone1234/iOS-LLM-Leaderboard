import Foundation
import PowerEvidence
import PowerRunnerCore
import PowerTextProgram

public struct PowerRunCheckpointContext: Codable, Sendable, Equatable {
    public let resultID: UUID
    public let program: PowerVersionedIdentity
    public let target: PowerVersionedIdentity
    public let runnerCertificateID: String
    public let appRelease: PowerAppReleaseIdentity
    public let model: PowerModelIdentity
    public let workload: PowerTextWorkload
    public let workloadSHA256: String
    public let thermalAssistance: PowerThermalAssistance

    public init(
        resultID: UUID,
        program: PowerVersionedIdentity,
        target: PowerVersionedIdentity,
        runnerCertificateID: String,
        appRelease: PowerAppReleaseIdentity,
        model: PowerModelIdentity,
        workload: PowerTextWorkload,
        workloadSHA256: String,
        thermalAssistance: PowerThermalAssistance
    ) {
        self.resultID = resultID
        self.program = program
        self.target = target
        self.runnerCertificateID = runnerCertificateID
        self.appRelease = appRelease
        self.model = model
        self.workload = workload
        self.workloadSHA256 = workloadSHA256
        self.thermalAssistance = thermalAssistance
    }
}

public struct PowerRunCheckpointRecovery: Sendable, Equatable {
    public let envelope: PowerEvidenceEnvelope?
    public let notice: String

    public init(
        envelope: PowerEvidenceEnvelope?,
        notice: String
    ) {
        self.envelope = envelope
        self.notice = notice
    }
}

/// Persists the active Power run independently from the final result store.
/// A process termination can therefore be represented as failed and not-run
/// attempts on the next launch without inventing a successful measurement.
public actor PowerRunCheckpointStore: PowerAttemptCheckpointSink {
    public enum StoreError: Error, LocalizedError {
        case activeCheckpointExists(URL)
        case invalidCheckpoint(URL)
        case sessionAlreadyStarted
        case sessionNotStarted
        case invalidAttemptSequence(Int)
        case sessionAlreadyFinished

        public var errorDescription: String? {
            switch self {
            case .activeCheckpointExists(let url):
                "An unfinished Power run already exists at \(url.path)."
            case .invalidCheckpoint(let url):
                "The active Power run checkpoint is invalid: \(url.path)."
            case .sessionAlreadyStarted:
                "The Power run checkpoint session has already started."
            case .sessionNotStarted:
                "The Power run checkpoint session has not started."
            case .invalidAttemptSequence(let index):
                "Power attempt \(index) is out of checkpoint sequence."
            case .sessionAlreadyFinished:
                "The Power run checkpoint session is already finished."
            }
        }
    }

    private struct ActiveAttempt: Codable, Sendable, Equatable {
        let index: Int
        let phase: PowerAttemptPhase
        let startedAt: String
        let thermalStateAtStart: PowerThermalState
    }

    private struct Snapshot: Codable, Sendable, Equatable {
        let schemaVersion: String
        let context: PowerRunCheckpointContext
        var sessionStart: PowerRunnerSessionStart?
        var activeAttempt: ActiveAttempt?
        var attempts: [PowerRunnerAttemptRecord]
        var completion: PowerRunnerSessionCompletion?
    }

    private static let schemaVersion =
        "power-active-run-checkpoint-1.0.0"
    private static let filename = "active-run.json"

    private let directory: URL
    private let fileURL: URL
    private let fileManager: FileManager
    private var snapshot: Snapshot

    public init(
        directory: URL,
        context: PowerRunCheckpointContext,
        fileManager: FileManager = .default
    ) throws {
        self.directory = directory
        self.fileURL = Self.checkpointURL(in: directory)
        self.fileManager = fileManager
        self.snapshot = Snapshot(
            schemaVersion: Self.schemaVersion,
            context: context,
            sessionStart: nil,
            activeAttempt: nil,
            attempts: [],
            completion: nil
        )
        guard !fileManager.fileExists(atPath: fileURL.path) else {
            throw StoreError.activeCheckpointExists(fileURL)
        }
        try Self.write(
            snapshot,
            to: fileURL,
            directory: directory,
            fileManager: fileManager
        )
    }

    public func beginSession(
        _ start: PowerRunnerSessionStart
    ) async throws {
        guard snapshot.sessionStart == nil else {
            throw StoreError.sessionAlreadyStarted
        }
        guard start.expectedAttemptCount > 0 else {
            throw StoreError.invalidAttemptSequence(
                start.expectedAttemptCount
            )
        }
        snapshot.sessionStart = start
        try persist()
    }

    public func markAttemptStarted(
        index: Int,
        phase: PowerAttemptPhase,
        startedAt: String,
        thermalStateAtStart: PowerThermalState
    ) async throws {
        guard let start = snapshot.sessionStart else {
            throw StoreError.sessionNotStarted
        }
        guard snapshot.completion == nil else {
            throw StoreError.sessionAlreadyFinished
        }
        guard
            snapshot.activeAttempt == nil,
            index == snapshot.attempts.count,
            index < start.expectedAttemptCount
        else {
            throw StoreError.invalidAttemptSequence(index)
        }
        snapshot.activeAttempt = ActiveAttempt(
            index: index,
            phase: phase,
            startedAt: startedAt,
            thermalStateAtStart: thermalStateAtStart
        )
        try persist()
    }

    public func record(
        _ attempt: PowerRunnerAttemptRecord
    ) async throws {
        guard let start = snapshot.sessionStart else {
            throw StoreError.sessionNotStarted
        }
        guard snapshot.completion == nil else {
            throw StoreError.sessionAlreadyFinished
        }
        guard
            attempt.index == snapshot.attempts.count,
            attempt.index < start.expectedAttemptCount,
            snapshot.activeAttempt == nil
                || snapshot.activeAttempt?.index == attempt.index
        else {
            throw StoreError.invalidAttemptSequence(attempt.index)
        }
        snapshot.attempts.append(attempt)
        snapshot.activeAttempt = nil
        try persist()
    }

    public func finishSession(
        _ completion: PowerRunnerSessionCompletion
    ) async throws {
        guard let start = snapshot.sessionStart else {
            throw StoreError.sessionNotStarted
        }
        guard
            snapshot.completion == nil,
            snapshot.activeAttempt == nil,
            snapshot.attempts.count == start.expectedAttemptCount
        else {
            throw StoreError.invalidAttemptSequence(
                snapshot.attempts.count
            )
        }
        snapshot.completion = completion
        try persist()
    }

    public func discard() throws {
        if fileManager.fileExists(atPath: fileURL.path) {
            try fileManager.removeItem(at: fileURL)
        }
    }

    public static func recover(
        from directory: URL,
        recoveredAt: String = PowerEvidenceTimestamp.string(
            from: Date()
        ),
        fileManager: FileManager = .default
    ) throws -> PowerRunCheckpointRecovery? {
        let url = checkpointURL(in: directory)
        guard fileManager.fileExists(atPath: url.path) else {
            return nil
        }
        let snapshot: Snapshot
        do {
            snapshot = try JSONDecoder().decode(
                Snapshot.self,
                from: Data(contentsOf: url)
            )
        } catch {
            throw StoreError.invalidCheckpoint(url)
        }
        guard snapshot.schemaVersion == schemaVersion else {
            throw StoreError.invalidCheckpoint(url)
        }
        guard let start = snapshot.sessionStart else {
            return PowerRunCheckpointRecovery(
                envelope: nil,
                notice: "Discarded an interrupted model preparation. "
                    + "No benchmark attempt had started."
            )
        }
        let expectedCount =
            snapshot.context.workload.procedure.warmupAttempts
            + snapshot.context.workload.procedure.measuredAttempts
        guard
            start.expectedAttemptCount == expectedCount,
            expectedCount > 0
        else {
            throw StoreError.invalidCheckpoint(url)
        }

        var attemptsByIndex = Dictionary(
            uniqueKeysWithValues: snapshot.attempts.map {
                ($0.index, $0)
            }
        )
        if attemptsByIndex.count != snapshot.attempts.count {
            throw StoreError.invalidCheckpoint(url)
        }
        if let active = snapshot.activeAttempt {
            guard
                active.index >= 0,
                active.index < expectedCount,
                attemptsByIndex[active.index] == nil
            else {
                throw StoreError.invalidCheckpoint(url)
            }
            attemptsByIndex[active.index] = interruptedAttempt(
                active,
                recoveredAt: recoveredAt
            )
        }
        for index in 0..<expectedCount where attemptsByIndex[index] == nil {
            attemptsByIndex[index] = notRunAttempt(
                index: index,
                phase: index
                    < snapshot.context.workload.procedure.warmupAttempts
                    ? .warmup
                    : .measured,
                recoveredAt: recoveredAt,
                thermalState: start.targetAtStart.thermalState
            )
        }
        let attempts = (0..<expectedCount).compactMap {
            attemptsByIndex[$0]
        }
        guard attempts.count == expectedCount else {
            throw StoreError.invalidCheckpoint(url)
        }
        let completion = snapshot.completion
            ?? PowerRunnerSessionCompletion(
                endedAt: recoveredAt,
                thermalStateAtEnd:
                    snapshot.activeAttempt?.thermalStateAtStart ?? .unknown
            )
        let session = PowerRunnerSession(
            startedAt: start.startedAt,
            endedAt: completion.endedAt,
            targetAtStart: start.targetAtStart,
            thermalStateAtEnd: completion.thermalStateAtEnd,
            runtimeIdentity: start.runtimeIdentity,
            attempts: attempts
        )
        let context = snapshot.context
        let payload = try PowerTextProgramModule.makePayload(
            workload: context.workload,
            workloadSHA256: context.workloadSHA256,
            session: session
        )
        let target = start.targetAtStart
        let envelope = PowerEvidenceEnvelope(
            resultID: context.resultID,
            createdAt: start.startedAt,
            program: context.program,
            target: context.target,
            runnerCertificateID: context.runnerCertificateID,
            appRelease: context.appRelease,
            model: context.model,
            runtime: start.runtimeIdentity,
            device: target.device,
            environment: .init(
                batteryLevelAtStart: target.batteryLevel,
                batteryStateAtStart: target.batteryState,
                lowPowerModeAtStart: target.lowPowerModeEnabled,
                thermalStateAtStart: target.thermalState,
                thermalStateAtEnd: completion.thermalStateAtEnd,
                thermalAssistance: context.thermalAssistance
            ),
            artifacts: [],
            payload: payload
        )
        return PowerRunCheckpointRecovery(
            envelope: envelope,
            notice: snapshot.completion == nil
                ? "Recovered an interrupted Power run. The active attempt "
                    + "is retained as failed and later attempts as not-run."
                : "Recovered a completed Power run that had not yet reached "
                    + "the final result store."
        )
    }

    public static func discardCheckpoint(
        in directory: URL,
        fileManager: FileManager = .default
    ) throws {
        let url = checkpointURL(in: directory)
        if fileManager.fileExists(atPath: url.path) {
            try fileManager.removeItem(at: url)
        }
    }

    private func persist() throws {
        try Self.write(
            snapshot,
            to: fileURL,
            directory: directory,
            fileManager: fileManager
        )
    }

    private static func checkpointURL(in directory: URL) -> URL {
        directory.appendingPathComponent(
            filename,
            isDirectory: false
        )
    }

    private static func write(
        _ snapshot: Snapshot,
        to url: URL,
        directory: URL,
        fileManager: FileManager
    ) throws {
        try fileManager.createDirectory(
            at: directory,
            withIntermediateDirectories: true
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(snapshot).write(to: url, options: [.atomic])
    }

    private static func interruptedAttempt(
        _ active: ActiveAttempt,
        recoveredAt: String
    ) -> PowerRunnerAttemptRecord {
        PowerRunnerAttemptRecord(
            index: active.index,
            phase: active.phase,
            outcome: .failed,
            startedAt: active.startedAt,
            endedAt: recoveredAt,
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
            thermalStateAtStart: active.thermalStateAtStart,
            thermalStateAtEnd: .unknown,
            thermalTransitions: [],
            failure: .init(
                code: "process_terminated_during_attempt",
                message: "The App process ended before the attempt "
                    + "could write a terminal record."
            )
        )
    }

    private static func notRunAttempt(
        index: Int,
        phase: PowerAttemptPhase,
        recoveredAt: String,
        thermalState: PowerThermalState
    ) -> PowerRunnerAttemptRecord {
        PowerRunnerAttemptRecord(
            index: index,
            phase: phase,
            outcome: .notRun,
            startedAt: recoveredAt,
            endedAt: recoveredAt,
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
            failure: .init(
                code: "run_interrupted_before_attempt",
                message: "The attempt was not started because the App "
                    + "process ended during the run."
            )
        )
    }
}
