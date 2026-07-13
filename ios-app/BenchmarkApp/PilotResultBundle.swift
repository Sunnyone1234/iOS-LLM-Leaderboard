import Foundation

struct PilotResultBundle: Codable, Sendable {
    let schemaVersion: String
    let resultID: String
    let createdAt: Date
    let officialResultEligible: Bool
    let plan: PlanIdentity
    let workload: WorkloadIdentity
    let measurementMode: MeasurementModeIdentity
    let generationConfiguration: GenerationConfiguration
    let model: ModelIdentity
    let runtime: RuntimeIdentity
    let device: DeviceIdentity
    let modelPreparation: ModelPreparationEvidence
    let eligibility: Eligibility
    let summary: Summary
    let attempts: [Attempt]

    struct PlanIdentity: Codable, Sendable {
        let id: String
        let version: String
        let promptSHA256: String
        let warmupRuns: Int
        let measuredRuns: Int
        let outputTokenLimit: Int
        let v2ProfileMapping: String
    }

    struct WorkloadIdentity: Codable, Sendable {
        let id: String
        let version: String
        let category: String
        let promptSHA256: String
    }

    struct MeasurementModeIdentity: Codable, Sendable {
        let id: String
        let timingBoundaryVersion: String
        let pipelineTTFTStart: String
        let pipelineTTFTEnd: String
        let userVisibleTTFTAvailable: Bool
        let prefillSource: String
        let decodeFormula: String
        let memoryMetric: String
        let memorySamplingIntervalMilliseconds: Int
    }

    struct GenerationConfiguration: Codable, Sendable {
        enum CodingKeys: String, CodingKey {
            case samplingEnabled
            case temperature
            case topP
            case topK
            case seed
            case repetitionPenalty
            case thinkingMode
            case chatTemplateIdentity
            case includeStopTokenInRawEvents
            case outputTokenLimit
            case contextPolicy
            case modelLoadPolicy
            case kvCachePolicy
        }

        let samplingEnabled: Bool
        let temperature: Double
        let topP: Double?
        let topK: Int?
        let seed: UInt64?
        let repetitionPenalty: Double?
        let thinkingMode: String
        let chatTemplateIdentity: String
        let includeStopTokenInRawEvents: Bool
        let outputTokenLimit: Int
        let contextPolicy: String
        let modelLoadPolicy: String
        let kvCachePolicy: String

        func encode(to encoder: Encoder) throws {
            var container = encoder.container(keyedBy: CodingKeys.self)
            try container.encode(samplingEnabled, forKey: .samplingEnabled)
            try container.encode(temperature, forKey: .temperature)
            if let topP {
                try container.encode(topP, forKey: .topP)
            } else {
                try container.encodeNil(forKey: .topP)
            }
            if let topK {
                try container.encode(topK, forKey: .topK)
            } else {
                try container.encodeNil(forKey: .topK)
            }
            if let seed {
                try container.encode(seed, forKey: .seed)
            } else {
                try container.encodeNil(forKey: .seed)
            }
            if let repetitionPenalty {
                try container.encode(repetitionPenalty, forKey: .repetitionPenalty)
            } else {
                try container.encodeNil(forKey: .repetitionPenalty)
            }
            try container.encode(thinkingMode, forKey: .thinkingMode)
            try container.encode(chatTemplateIdentity, forKey: .chatTemplateIdentity)
            try container.encode(
                includeStopTokenInRawEvents,
                forKey: .includeStopTokenInRawEvents
            )
            try container.encode(outputTokenLimit, forKey: .outputTokenLimit)
            try container.encode(contextPolicy, forKey: .contextPolicy)
            try container.encode(modelLoadPolicy, forKey: .modelLoadPolicy)
            try container.encode(kvCachePolicy, forKey: .kvCachePolicy)
        }
    }

    struct ModelIdentity: Codable, Sendable {
        enum CodingKeys: String, CodingKey {
            case displayName
            case baseModelID
            case artifactID
            case artifactRevision
            case quantization
            case modelFormat
            case artifactContentHash
        }

        let displayName: String
        let baseModelID: String
        let artifactID: String
        let artifactRevision: String
        let quantization: String
        let modelFormat: String
        let artifactContentHash: String?

        func encode(to encoder: Encoder) throws {
            var container = encoder.container(keyedBy: CodingKeys.self)
            try container.encode(displayName, forKey: .displayName)
            try container.encode(baseModelID, forKey: .baseModelID)
            try container.encode(artifactID, forKey: .artifactID)
            try container.encode(artifactRevision, forKey: .artifactRevision)
            try container.encode(quantization, forKey: .quantization)
            try container.encode(modelFormat, forKey: .modelFormat)
            if let artifactContentHash {
                try container.encode(artifactContentHash, forKey: .artifactContentHash)
            } else {
                try container.encodeNil(forKey: .artifactContentHash)
            }
        }
    }

    struct RuntimeIdentity: Codable, Sendable {
        let name: String
        let version: String
        let resolvedRevision: String
        let backend: String
        let mlxSwiftVersion: String
        let mlxSwiftRevision: String
        let downloaderPackage: String
        let tokenizerPackage: String
    }

    struct DeviceIdentity: Codable, Sendable {
        enum CodingKeys: String, CodingKey {
            case displayName
            case machineIdentifier
            case systemName
            case systemVersion
            case systemBuild
            case debuggerAttached
            case buildConfiguration
            case appVersion
            case appBuild
            case appSourceCommit
            case lowPowerModeEnabled
            case batteryLevelPercent
            case batteryState
        }

        let displayName: String
        let machineIdentifier: String
        let systemName: String
        let systemVersion: String
        let systemBuild: String
        let debuggerAttached: Bool
        let buildConfiguration: String
        let appVersion: String
        let appBuild: String
        let appSourceCommit: String?
        let lowPowerModeEnabled: Bool
        let batteryLevelPercent: Double?
        let batteryState: String

        func encode(to encoder: Encoder) throws {
            var container = encoder.container(keyedBy: CodingKeys.self)
            try container.encode(displayName, forKey: .displayName)
            try container.encode(machineIdentifier, forKey: .machineIdentifier)
            try container.encode(systemName, forKey: .systemName)
            try container.encode(systemVersion, forKey: .systemVersion)
            try container.encode(systemBuild, forKey: .systemBuild)
            try container.encode(debuggerAttached, forKey: .debuggerAttached)
            try container.encode(buildConfiguration, forKey: .buildConfiguration)
            try container.encode(appVersion, forKey: .appVersion)
            try container.encode(appBuild, forKey: .appBuild)
            if let appSourceCommit {
                try container.encode(appSourceCommit, forKey: .appSourceCommit)
            } else {
                try container.encodeNil(forKey: .appSourceCommit)
            }
            try container.encode(lowPowerModeEnabled, forKey: .lowPowerModeEnabled)
            if let batteryLevelPercent {
                try container.encode(batteryLevelPercent, forKey: .batteryLevelPercent)
            } else {
                try container.encodeNil(forKey: .batteryLevelPercent)
            }
            try container.encode(batteryState, forKey: .batteryState)
        }
    }

    struct Eligibility: Codable, Sendable, Equatable {
        let sessionValidity: Decision
        let coldPerformance: Decision
        let sustainedPerformance: Decision
        let thermalStability: Decision
        let officialLeaderboard: Decision

        struct Decision: Codable, Sendable, Equatable {
            let eligible: Bool
            let reasonCodes: [String]
        }

        static func evaluate(
            attempts: [Attempt],
            modelPreparation: ModelPreparationEvidence,
            debuggerAttached: Bool,
            buildConfiguration: String,
            lowPowerModeEnabled: Bool,
            plannedMeasuredRuns: Int
        ) -> Eligibility {
            let measured = attempts.filter { $0.role == "measured" }
            let successful = measured.filter { $0.outcome == "completed" }
            let initialThermal = attempts.first?.thermalStateBefore
            let startsNominal = initialThermal == "nominal"
            let hasAllAttemptRecords = measured.count == plannedMeasuredRuns
            let hasNotRun = measured.contains { $0.outcome == "notRun" }
            let hasThreeSuccessful = successful.count >= 3
            let nominalMeasured = successful.filter {
                $0.thermalStateBefore == "nominal"
                    && $0.thermalStateAfter == "nominal"
            }

            var sessionReasons: [String] = []
            if !modelPreparation.eligibleForPerformanceMeasurement {
                sessionReasons.append(contentsOf: modelPreparation.reasonCodes)
            }
            if modelPreparation.downloadOccurredDuringSession {
                sessionReasons.append("model_download_during_session")
            }
            if modelPreparation.cacheStateBeforePreparation == .unknown {
                sessionReasons.append("model_cache_state_unknown")
            }
            if debuggerAttached { sessionReasons.append("debugger_attached") }
            if buildConfiguration != "Release" {
                sessionReasons.append("non_release_build")
            }
            if lowPowerModeEnabled {
                sessionReasons.append("low_power_mode_enabled")
            }
            if !startsNominal {
                sessionReasons.append("initial_thermal_state_not_nominal")
            }
            if !hasAllAttemptRecords {
                sessionReasons.append("incomplete_attempt_records")
            }
            if !hasThreeSuccessful {
                sessionReasons.append("insufficient_successful_measured_runs")
            }
            if hasNotRun { sessionReasons.append("planned_attempt_not_run") }

            var coldReasons: [String] = []
            if !startsNominal {
                coldReasons.append("initial_thermal_state_not_nominal")
            }
            if nominalMeasured.isEmpty {
                coldReasons.append("no_nominal_measured_run")
            }

            var sustainedReasons: [String] = []
            if !startsNominal {
                sustainedReasons.append("initial_thermal_state_not_nominal")
            }
            if !hasThreeSuccessful {
                sustainedReasons.append("insufficient_successful_measured_runs")
            }
            if hasNotRun { sustainedReasons.append("sequence_stopped_early") }

            var thermalReasons: [String] = []
            if !hasThreeSuccessful {
                thermalReasons.append("insufficient_successful_measured_runs")
            }
            if measured.contains(where: {
                $0.thermalStateBefore == "unknown"
                    || $0.thermalStateAfter == "unknown"
            }) {
                thermalReasons.append("thermal_state_unavailable")
            }

            return Eligibility(
                sessionValidity: Decision(
                    eligible: sessionReasons.isEmpty,
                    reasonCodes: Array(Set(sessionReasons)).sorted()
                ),
                coldPerformance: Decision(
                    eligible: coldReasons.isEmpty,
                    reasonCodes: coldReasons
                ),
                sustainedPerformance: Decision(
                    eligible: sustainedReasons.isEmpty,
                    reasonCodes: sustainedReasons
                ),
                thermalStability: Decision(
                    eligible: thermalReasons.isEmpty,
                    reasonCodes: thermalReasons
                ),
                officialLeaderboard: Decision(
                    eligible: false,
                    reasonCodes: ["pilot_protocol_not_official"]
                )
            )
        }
    }

    struct Summary: Codable, Sendable {
        let successfulMeasuredRuns: Int
        let failedMeasuredRuns: Int
        let medianTTFTMilliseconds: Double?
        let medianPrefillTokensPerSecond: Double?
        let medianDecodeTokensPerSecond: Double?
        let medianPeakMemoryMegabytes: Double?
        let finalThermalState: String
        let degradation: Degradation
    }

    struct Degradation: Codable, Sendable {
        let firstMeasuredRunIndex: Int?
        let lastMeasuredRunIndex: Int?
        let decodePercentChange: Double?
        let ttftPercentChange: Double?
        let prefillPercentChange: Double?

        static func calculate(first: Attempt?, last: Attempt?) -> Degradation {
            Degradation(
                firstMeasuredRunIndex: first?.runIndex,
                lastMeasuredRunIndex: last?.runIndex,
                decodePercentChange: percentChange(
                    from: first?.metrics.decodeTokensPerSecond,
                    to: last?.metrics.decodeTokensPerSecond
                ),
                ttftPercentChange: percentChange(
                    from: first?.metrics.ttftMilliseconds,
                    to: last?.metrics.ttftMilliseconds
                ),
                prefillPercentChange: percentChange(
                    from: first?.metrics.prefillTokensPerSecond,
                    to: last?.metrics.prefillTokensPerSecond
                )
            )
        }

        private static func percentChange(from first: Double?, to last: Double?) -> Double? {
            guard let first, let last, first != 0 else { return nil }
            return (last / first - 1) * 100
        }
    }

    struct Attempt: Codable, Sendable {
        let runIndex: Int
        let role: String
        let outcome: String
        let errorMessage: String?
        let promptTokenCount: Int?
        let outputTokenCount: Int?
        let stopReason: String?
        let thermalStateBefore: String
        let thermalStateAfter: String
        let memorySamplingIntervalMilliseconds: Int
        let metrics: AttemptMetrics
        let tokenEvents: [RuntimeToken]
    }

    @MainActor
    static func make(
        session: BenchmarkSession,
        environment: DeviceEnvironment,
        plan: PilotPlan,
        modelPreparation: ModelPreparationEvidence
    ) -> PilotResultBundle {
        let attemptRecords = session.attempts.map { attempt in
            let generation: RuntimeGenerationResult?
            let outcome: String
            let error: String?
            switch attempt.outcome {
            case .completed(let result):
                generation = result
                outcome = "completed"
                error = nil
            case .failed(let message):
                generation = nil
                outcome = "failed"
                error = message
            case .notRun(let reason):
                generation = nil
                outcome = "notRun"
                error = reason
            }
            return Attempt(
                runIndex: attempt.index,
                role: attempt.role.rawValue,
                outcome: outcome,
                errorMessage: error,
                promptTokenCount: generation?.promptTokenCount,
                outputTokenCount: generation?.outputTokenCount,
                stopReason: generation?.stopReason.rawValue,
                thermalStateBefore: attempt.thermalStateBefore,
                thermalStateAfter: attempt.thermalStateAfter,
                memorySamplingIntervalMilliseconds:
                    plan.measurementMode.memorySamplingIntervalMilliseconds,
                metrics: .calculate(for: attempt),
                tokenEvents: attempt.tokens
            )
        }

        let measured = zip(session.measuredAttempts, attemptRecords.filter {
            $0.role == BenchmarkAttempt.Role.measured.rawValue
        })
        let successful = measured.filter { pair in
            if case .completed = pair.0.outcome { return true }
            return false
        }.map(\.1)
        let failedCount = session.measuredAttempts.count - successful.count

        return PilotResultBundle(
            schemaVersion: "suite-b-pilot-bundle-0.6",
            resultID: UUID().uuidString.lowercased(),
            createdAt: Date(),
            officialResultEligible: false,
            plan: PlanIdentity(
                id: plan.planId,
                version: plan.planVersion,
                promptSHA256: plan.workload.promptSha256,
                warmupRuns: plan.procedure.warmupRuns,
                measuredRuns: plan.procedure.measuredRuns,
                outputTokenLimit: plan.workload.outputTokenLimit,
                v2ProfileMapping: plan.workload.v2ProfileMapping
            ),
            workload: WorkloadIdentity(
                id: plan.workload.workloadId,
                version: plan.workload.workloadVersion,
                category: plan.workload.category,
                promptSHA256: plan.workload.promptSha256
            ),
            measurementMode: MeasurementModeIdentity(
                id: plan.measurementMode.measurementModeId,
                timingBoundaryVersion: plan.measurementMode.timingBoundaryVersion,
                pipelineTTFTStart: plan.measurementMode.pipelineTtftStart,
                pipelineTTFTEnd: plan.measurementMode.pipelineTtftEnd,
                userVisibleTTFTAvailable:
                    plan.measurementMode.userVisibleTtftAvailable,
                prefillSource: plan.measurementMode.prefillSource,
                decodeFormula: plan.measurementMode.decodeFormula,
                memoryMetric: plan.measurementMode.memoryMetric,
                memorySamplingIntervalMilliseconds:
                    plan.measurementMode.memorySamplingIntervalMilliseconds
            ),
            generationConfiguration: GenerationConfiguration(
                samplingEnabled: plan.generation.samplingEnabled,
                temperature: plan.generation.temperature,
                topP: plan.generation.topP,
                topK: plan.generation.topK,
                seed: plan.generation.seed,
                repetitionPenalty: plan.generation.repetitionPenalty,
                thinkingMode: plan.generation.thinkingMode,
                chatTemplateIdentity: plan.generation.chatTemplateIdentity,
                includeStopTokenInRawEvents:
                    plan.generation.includeStopTokenInRawEvents,
                outputTokenLimit: plan.workload.outputTokenLimit,
                contextPolicy: plan.generation.contextPolicy,
                modelLoadPolicy: plan.generation.modelLoadPolicy,
                kvCachePolicy: plan.generation.kvCachePolicy
            ),
            model: ModelIdentity(
                displayName: plan.modelProfile.displayName,
                baseModelID: plan.modelProfile.baseModelId,
                artifactID: plan.modelProfile.artifactId,
                artifactRevision: plan.modelProfile.artifactRevision,
                quantization: plan.modelProfile.quantization,
                modelFormat: plan.modelProfile.modelFormat,
                artifactContentHash: plan.modelProfile.artifactContentHash
            ),
            runtime: RuntimeIdentity(
                name: plan.runtimeProfile.runtimeName,
                version: plan.runtimeProfile.packageVersion,
                resolvedRevision: plan.runtimeProfile.packageRevision,
                backend: plan.runtimeProfile.backend,
                mlxSwiftVersion: plan.runtimeProfile.mlxSwiftVersion,
                mlxSwiftRevision: plan.runtimeProfile.mlxSwiftRevision,
                downloaderPackage: plan.runtimeProfile.downloaderPackage,
                tokenizerPackage: plan.runtimeProfile.tokenizerPackage
            ),
            device: DeviceIdentity(
                displayName: environment.deviceDescription,
                machineIdentifier: environment.modelIdentifier,
                systemName: environment.systemName,
                systemVersion: environment.systemVersion,
                systemBuild: environment.systemBuild,
                debuggerAttached: environment.debuggerAttached,
                buildConfiguration: environment.buildConfiguration,
                appVersion: environment.appVersion,
                appBuild: environment.appBuild,
                appSourceCommit: environment.appSourceCommit,
                lowPowerModeEnabled: environment.lowPowerModeEnabled,
                batteryLevelPercent: environment.batteryLevelPercent,
                batteryState: environment.batteryState
            ),
            modelPreparation: modelPreparation,
            eligibility: .evaluate(
                attempts: attemptRecords,
                modelPreparation: modelPreparation,
                debuggerAttached: environment.debuggerAttached,
                buildConfiguration: environment.buildConfiguration,
                lowPowerModeEnabled: environment.lowPowerModeEnabled,
                plannedMeasuredRuns: plan.procedure.measuredRuns
            ),
            summary: Summary(
                successfulMeasuredRuns: successful.count,
                failedMeasuredRuns: failedCount,
                medianTTFTMilliseconds: AttemptMetrics.median(
                    successful.map { $0.metrics.ttftMilliseconds }
                ),
                medianPrefillTokensPerSecond: AttemptMetrics.median(
                    successful.map { $0.metrics.prefillTokensPerSecond }
                ),
                medianDecodeTokensPerSecond: AttemptMetrics.median(
                    successful.map { $0.metrics.decodeTokensPerSecond }
                ),
                medianPeakMemoryMegabytes: AttemptMetrics.median(
                    successful.map { $0.metrics.peakMemoryMegabytes }
                ),
                finalThermalState: attemptRecords.last?.thermalStateAfter
                    ?? environment.thermalState,
                degradation: .calculate(
                    first: successful.first,
                    last: successful.last
                )
            ),
            attempts: attemptRecords
        )
    }
}
