import Foundation

enum PowerBenchmarkRelease {
    static let releaseID = "suite-b-power"
    static let releaseVersion = "1.0.0-rc.1"
    static let resultSchemaVersion = "suite-b-power-result-1.0.0-rc.1"
    static let runnerID = "ios-reference-benchmark-app"
    static let minimumRunnerVersion = "0.8.0"

    struct Workload: Sendable, Equatable {
        let id: String
        let category: String
        let fixtureSHA256: String
        let measurementModeID: String
        let outputTokenLimit: Int
        let topP: Double?
        let topK: Int?
        let seed: UInt64?
        let thinkingMode: String
        let chatTemplateIdentity: String
    }

    enum ContractError: LocalizedError, Equatable {
        case incompatiblePlan(String)
        case missingSourceCommit
        case nonPhysicalDevice(String)
        case incompatibleRunnerVersion(String)

        var errorDescription: String? {
            switch self {
            case .incompatiblePlan(let reason):
                "The plan is not compatible with Power \(releaseVersion): \(reason)."
            case .missingSourceCommit:
                "Build the App with a 40-character GIT_COMMIT_SHA before measuring."
            case .nonPhysicalDevice(let identifier):
                "Power evidence requires a physical iPhone; found \(identifier)."
            case .incompatibleRunnerVersion(let version):
                "Reference App \(version) is older than \(minimumRunnerVersion)."
            }
        }
    }

    static let workloads: [Workload] = [
        Workload(
            id: "b-ux-001-short-interaction",
            category: "user-experience",
            fixtureSHA256:
                "69b3cd45fb67e1882dabdc082636298123e01081c097af65b3fd133b19ccbc84",
            measurementModeID: "b-mode-warm-resident-ux-v1",
            outputTokenLimit: 128,
            topP: 1,
            topK: 0,
            seed: 0,
            thinkingMode: "disabled-via-chat-template",
            chatTemplateIdentity:
                "artifact-tokenizer-config-enable-thinking-false"
        ),
        Workload(
            id: "b-pipe-001-sustained-generation",
            category: "pipeline",
            fixtureSHA256:
                "b865ad1a1993bfd7bf097b85f7c5585e44f1384fa291b9c05426c6051caba996",
            measurementModeID: "b-mode-sustained-no-rest-v1",
            outputTokenLimit: 512,
            topP: nil,
            topK: nil,
            seed: nil,
            thinkingMode: "disabled-via-prompt-directive",
            chatTemplateIdentity: "artifact-tokenizer-config"
        ),
    ]

    static func workload(for plan: PilotPlan) throws -> Workload {
        guard plan.planVersion == releaseVersion,
              plan.workload.workloadVersion == releaseVersion else {
            throw ContractError.incompatiblePlan("release version")
        }
        guard let workload = workloads.first(where: {
            $0.id == plan.workload.workloadId
        }) else {
            throw ContractError.incompatiblePlan("workload ID")
        }
        guard plan.workload.category == workload.category,
              plan.workload.promptSha256 == workload.fixtureSHA256,
              plan.workload.outputTokenLimit == workload.outputTokenLimit,
              plan.measurementMode.measurementModeId == workload.measurementModeID,
              plan.measurementMode.memoryMetric
                == "TASK_VM_INFO.phys_footprint",
              plan.measurementMode.memorySamplingIntervalMilliseconds == 50,
              plan.procedure.warmupRuns == 1,
              plan.procedure.measuredRuns == 5,
              plan.procedure.minimumSuccessfulRunsForSummary == 3,
              plan.procedure.restIntervalSeconds == 0,
              plan.generation.samplingEnabled == false,
              plan.generation.temperature == 0,
              plan.generation.topP == workload.topP,
              plan.generation.topK == workload.topK,
              plan.generation.seed == workload.seed,
              plan.generation.repetitionPenalty == nil,
              plan.generation.thinkingMode == workload.thinkingMode,
              plan.generation.chatTemplateIdentity
                == workload.chatTemplateIdentity,
              plan.generation.includeStopTokenInRawEvents == false,
              plan.generation.modelLoadPolicy == "load-once-before-warmup",
              plan.generation.contextPolicy
                == "fresh-conversation-per-attempt",
              plan.generation.kvCachePolicy
                == "fresh-kv-cache-per-attempt" else {
            throw ContractError.incompatiblePlan("frozen execution settings")
        }
        return workload
    }

    static func validateExecutionEnvironment(
        _ environment: DeviceEnvironment
    ) throws -> String {
        guard isPhysicalIPhone(environment.modelIdentifier) else {
            throw ContractError.nonPhysicalDevice(environment.modelIdentifier)
        }
        guard let sourceCommit = environment.appSourceCommit,
              isSourceCommit(sourceCommit) else {
            throw ContractError.missingSourceCommit
        }
        guard version(environment.appVersion, isAtLeast: minimumRunnerVersion) else {
            throw ContractError.incompatibleRunnerVersion(environment.appVersion)
        }
        return sourceCommit
    }

    static func isSourceCommit(_ value: String) -> Bool {
        value.count == 40 && value.allSatisfy {
            $0.isNumber || "abcdef".contains($0)
        }
    }

    static func isPhysicalIPhone(_ value: String) -> Bool {
        value.range(
            of: #"^iPhone[0-9]+,[0-9]+$"#,
            options: .regularExpression
        ) != nil
    }

    private static func version(_ actual: String, isAtLeast minimum: String) -> Bool {
        let actualParts = actual.split(separator: ".").compactMap { Int($0) }
        let minimumParts = minimum.split(separator: ".").compactMap { Int($0) }
        guard actualParts.count == actual.split(separator: ".").count,
              minimumParts.count == minimum.split(separator: ".").count else {
            return false
        }
        let width = max(actualParts.count, minimumParts.count)
        for index in 0..<width {
            let actualPart = index < actualParts.count ? actualParts[index] : 0
            let minimumPart = index < minimumParts.count ? minimumParts[index] : 0
            if actualPart != minimumPart {
                return actualPart > minimumPart
            }
        }
        return true
    }
}

struct PowerExecutionEnvironmentSnapshot: Codable, Sendable, Equatable {
    let modelIdentifier: String
    let deviceDisplayName: String
    let systemName: String
    let systemVersion: String
    let systemBuild: String
    let physicalMemoryBytes: UInt64
    let debuggerAttached: Bool
    let buildConfiguration: String
    let appVersion: String
    let appBuild: String
    let appSourceCommit: String
    let lowPowerModeEnabled: Bool
    let batteryLevelPercent: Double?
    let batteryState: String

    init(_ environment: DeviceEnvironment) throws {
        appSourceCommit = try PowerBenchmarkRelease
            .validateExecutionEnvironment(environment)
        modelIdentifier = environment.modelIdentifier
        deviceDisplayName = environment.deviceDescription
        systemName = environment.systemName
        systemVersion = environment.systemVersion
        systemBuild = environment.systemBuild
        physicalMemoryBytes = environment.physicalMemoryBytes
        debuggerAttached = environment.debuggerAttached
        buildConfiguration = environment.buildConfiguration
        appVersion = environment.appVersion
        appBuild = environment.appBuild
        lowPowerModeEnabled = environment.lowPowerModeEnabled
        batteryLevelPercent = environment.batteryLevelPercent
        batteryState = environment.batteryState
    }
}

struct PowerExecutionContext: Codable, Sendable, Equatable {
    let plan: PilotPlan
    let environment: PowerExecutionEnvironmentSnapshot
    let modelPreparation: ModelPreparationEvidence
}

struct RecoveredPowerSession: Sendable, Equatable {
    let context: PowerExecutionContext
    let session: BenchmarkSession
}

actor PowerSessionCheckpointStore {
    enum CheckpointError: LocalizedError {
        case missingSession
        case activeSessionExists
        case incompatibleCheckpoint

        var errorDescription: String? {
            switch self {
            case .missingSession: "No active Power checkpoint exists."
            case .activeSessionExists:
                "An unresolved Power checkpoint already exists and must not be overwritten."
            case .incompatibleCheckpoint:
                "The saved Power checkpoint is not compatible with this App."
            }
        }
    }

    private struct Checkpoint: Codable {
        enum State: String, Codable { case running, readyForExport }

        let schemaVersion: String
        let context: PowerExecutionContext
        let sessionID: UUID
        let startedAt: Date
        let thermalStateAtStart: String
        var state: State
        var activeAttemptIndex: Int?
        var activeAttemptRole: BenchmarkAttempt.Role?
        var activeThermalStateBefore: String?
        var attempts: [BenchmarkAttempt]
        var endedAt: Date?
        var thermalStateAtEnd: String?
    }

    private static let schemaVersion = "power-session-checkpoint-1.0"
    private let fileURL: URL
    private var checkpoint: Checkpoint?

    init(fileURL: URL? = nil) {
        self.fileURL = fileURL ?? Self.defaultURL()
    }

    func begin(
        context: PowerExecutionContext,
        sessionID: UUID,
        startedAt: Date,
        thermalStateAtStart: String
    ) throws {
        try loadIfNeeded()
        guard checkpoint == nil else {
            throw CheckpointError.activeSessionExists
        }
        checkpoint = Checkpoint(
            schemaVersion: Self.schemaVersion,
            context: context,
            sessionID: sessionID,
            startedAt: startedAt,
            thermalStateAtStart: thermalStateAtStart,
            state: .running,
            attempts: []
        )
        try persist()
    }

    func markAttemptStarted(
        index: Int,
        role: BenchmarkAttempt.Role,
        thermalStateBefore: String
    ) throws {
        try loadIfNeeded()
        guard checkpoint != nil else { throw CheckpointError.missingSession }
        checkpoint?.activeAttemptIndex = index
        checkpoint?.activeAttemptRole = role
        checkpoint?.activeThermalStateBefore = thermalStateBefore
        try persist()
    }

    func record(_ attempt: BenchmarkAttempt) throws {
        try loadIfNeeded()
        guard checkpoint != nil else { throw CheckpointError.missingSession }
        checkpoint?.attempts.removeAll { $0.index == attempt.index }
        checkpoint?.attempts.append(attempt)
        checkpoint?.attempts.sort { $0.index < $1.index }
        checkpoint?.activeAttemptIndex = nil
        checkpoint?.activeAttemptRole = nil
        checkpoint?.activeThermalStateBefore = nil
        try persist()
    }

    func markReadyForExport(
        endedAt: Date,
        thermalStateAtEnd: String
    ) throws {
        try loadIfNeeded()
        guard checkpoint != nil else { throw CheckpointError.missingSession }
        checkpoint?.state = .readyForExport
        checkpoint?.endedAt = endedAt
        checkpoint?.thermalStateAtEnd = thermalStateAtEnd
        try persist()
    }

    func recoverInterrupted(
        thermalState currentThermalState: String
    ) throws -> RecoveredPowerSession? {
        try loadIfNeeded()
        guard var value = checkpoint else { return nil }
        guard value.schemaVersion == Self.schemaVersion,
              (try? PowerBenchmarkRelease.workload(for: value.context.plan))
                != nil else {
            throw CheckpointError.incompatibleCheckpoint
        }

        if value.state == .running {
            var attempts = value.attempts
            let recorded = Set(attempts.map(\.index))
            if let activeIndex = value.activeAttemptIndex,
               !recorded.contains(activeIndex) {
                attempts.append(
                    BenchmarkAttempt(
                        index: activeIndex,
                        role: value.activeAttemptRole
                            ?? (activeIndex == 0 ? .warmup : .measured),
                        tokens: [],
                        peakMemoryBytes: nil,
                        thermalStateBefore:
                            value.activeThermalStateBefore ?? currentThermalState,
                        thermalStateAfter: currentThermalState,
                        outcome: .failed(
                            message: "The App process ended during this attempt.",
                            reasonCode: "process_terminated_unclassified"
                        )
                    )
                )
            }
            let afterRecovery = Set(attempts.map(\.index))
            for index in 0..<6 where !afterRecovery.contains(index) {
                attempts.append(
                    BenchmarkAttempt(
                        index: index,
                        role: index == 0 ? .warmup : .measured,
                        tokens: [],
                        peakMemoryBytes: nil,
                        thermalStateBefore: currentThermalState,
                        thermalStateAfter: currentThermalState,
                        outcome: .notRun(reason: "prior_attempt_unrecoverable")
                    )
                )
            }
            value.attempts = attempts.sorted { $0.index < $1.index }
            value.state = .readyForExport
            value.endedAt = Date()
            value.thermalStateAtEnd = currentThermalState
            value.activeAttemptIndex = nil
            value.activeAttemptRole = nil
            value.activeThermalStateBefore = nil
            checkpoint = value
            try persist()
        }

        guard value.attempts.count == 6,
              let endedAt = value.endedAt,
              let thermalStateAtEnd = value.thermalStateAtEnd else {
            throw CheckpointError.incompatibleCheckpoint
        }
        return RecoveredPowerSession(
            context: value.context,
            session: BenchmarkSession(
                sessionID: value.sessionID,
                startedAt: value.startedAt,
                endedAt: endedAt,
                thermalStateAtStart: value.thermalStateAtStart,
                thermalStateAtEnd: thermalStateAtEnd,
                runtimeIdentity: value.context.plan.runtimeProfile.runtimeName,
                attempts: value.attempts
            )
        )
    }

    func clear() throws {
        checkpoint = nil
        if FileManager.default.fileExists(atPath: fileURL.path) {
            try FileManager.default.removeItem(at: fileURL)
        }
    }

    private func loadIfNeeded() throws {
        guard checkpoint == nil,
              FileManager.default.fileExists(atPath: fileURL.path) else { return }
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        checkpoint = try decoder.decode(
            Checkpoint.self,
            from: Data(contentsOf: fileURL)
        )
    }

    private func persist() throws {
        guard let checkpoint else { throw CheckpointError.missingSession }
        let directory = fileURL.deletingLastPathComponent()
        try FileManager.default.createDirectory(
            at: directory,
            withIntermediateDirectories: true
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(checkpoint).write(to: fileURL, options: .atomic)
    }

    private nonisolated static func defaultURL() -> URL {
        let base = (try? FileManager.default.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )) ?? FileManager.default.temporaryDirectory
        return base
            .appending(path: "PowerBenchmark", directoryHint: .isDirectory)
            .appending(path: "active-session.json", directoryHint: .notDirectory)
    }
}
