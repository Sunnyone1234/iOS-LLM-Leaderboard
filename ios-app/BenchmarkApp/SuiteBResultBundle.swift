import Foundation

struct SuiteBResultBundle: Codable, Sendable {
    let schemaVersion: String
    let resultID: String
    let createdAt: Date
    let officialResultEligible: Bool
    let plan: PlanIdentity
    let workload: WorkloadIdentity
    let measurementMode: PilotResultBundle.MeasurementModeIdentity
    let generationConfiguration: PilotResultBundle.GenerationConfiguration
    let model: PilotResultBundle.ModelIdentity
    let runtime: PilotResultBundle.RuntimeIdentity
    let device: PilotResultBundle.DeviceIdentity
    let modelPreparation: ModelPreparationEvidence
    let eligibility: Eligibility
    let bundleSummary: BundleSummary?
    let sessions: [Session]

    struct PlanIdentity: Codable, Sendable {
        let id: String
        let version: String
        let runnerKind: String
        let warmupRuns: Int
        let measuredRuns: Int
        let outputTokenLimit: Int
        let requiredPowerSource: String
        let minimumBatteryLevelPercent: Double
    }

    struct WorkloadIdentity: Codable, Sendable {
        let id: String
        let version: String
        let category: String
        let fixtureSHA256: [String]
    }

    struct Eligibility: Codable, Sendable {
        let sessionValid: Bool
        let officialLeaderboardEligible: Bool
        let reasonCodes: [String]
    }

    struct BundleSummary: Codable, Sendable {
        let firstMeasuredRunIndex: Int?
        let lastMeasuredRunIndex: Int?
        let decodePercentChange: Double?
        let ttftPercentChange: Double?
        let prefillPercentChange: Double?
    }

    struct Session: Codable, Sendable {
        let id: String
        let targetInputTokens: Int?
        let fixtureSHA256: String
        let paddingRepetitions: Int?
        let performanceEligible: Bool
        let qualityEligible: Bool?
        let timingEvidenceRetained: Bool
        let summary: SessionSummary
        let attempts: [Attempt]
    }

    struct SessionSummary: Codable, Sendable {
        let successfulMeasuredRuns: Int
        let failedMeasuredRuns: Int
        let answerContractPassingRuns: Int?
        let modelInputTokens: Int?
        let medianPipelineTTFTMilliseconds: Double?
        let medianUserVisibleTTFTMilliseconds: Double?
        let medianRequestCompletionMilliseconds: Double?
        let medianPrefillTokensPerSecond: Double?
        let medianDecodeTokensPerSecond: Double?
        let medianPeakMemoryMegabytes: Double?
        let finalThermalState: String
    }

    struct Attempt: Codable, Sendable {
        let runIndex: Int
        let role: String
        let outcome: String
        let errorMessage: String?
        let promptTokenCount: Int?
        let outputTokenCount: Int?
        let stopReason: String?
        let visibleText: String?
        let answerContract: ContextAnswerContract?
        let answerEligible: Bool?
        let thermalStateBefore: String
        let thermalStateAfter: String
        let memorySamplingIntervalMilliseconds: Int
        let metrics: AttemptMetrics
        let tokenEvents: [RuntimeToken]
    }

    static func common(
        registryPlan: SuiteBPlanRegistry.Plan,
        basePlan: PilotPlan,
        environment: DeviceEnvironment,
        modelPreparation: ModelPreparationEvidence,
        sessions: [Session],
        bundleSummary: BundleSummary? = nil
    ) -> SuiteBResultBundle {
        let sessionValid = modelPreparation.eligibleForPerformanceMeasurement
            && !environment.debuggerAttached
            && environment.buildConfiguration == "Release"
            && !environment.lowPowerModeEnabled
            && environment.batteryState == registryPlan.requiredPowerSource
            && environment.batteryLevelPercent.map {
                $0 >= registryPlan.minimumBatteryLevelPercent
            } == true
        var reasonCodes = ["pilot_protocol_not_official"]
        if environment.batteryState == "unknown" { reasonCodes.append("power_source_unknown") }
        else if environment.batteryState != registryPlan.requiredPowerSource { reasonCodes.append("external_power_connected") }
        if environment.batteryLevelPercent == nil { reasonCodes.append("battery_level_unknown") }
        else if environment.batteryLevelPercent! < registryPlan.minimumBatteryLevelPercent { reasonCodes.append("battery_level_below_minimum") }
        return SuiteBResultBundle(
            schemaVersion: "suite-b-result-bundle-0.2",
            resultID: UUID().uuidString.lowercased(),
            createdAt: Date(),
            officialResultEligible: false,
            plan: .init(
                id: registryPlan.planId,
                version: registryPlan.planVersion,
                runnerKind: registryPlan.runnerKind,
                warmupRuns: registryPlan.warmupRuns,
                measuredRuns: registryPlan.measuredRuns,
                outputTokenLimit: registryPlan.outputTokenLimit,
                requiredPowerSource: registryPlan.requiredPowerSource,
                minimumBatteryLevelPercent: registryPlan.minimumBatteryLevelPercent
            ),
            workload: .init(
                id: registryPlan.workloadId,
                version: registryPlan.workloadVersion,
                category: registryPlan.category,
                fixtureSHA256: registryPlan.fixtureSha256
            ),
            measurementMode: .init(
                id: basePlan.measurementMode.measurementModeId,
                timingBoundaryVersion: basePlan.measurementMode.timingBoundaryVersion,
                pipelineTTFTStart: basePlan.measurementMode.pipelineTtftStart,
                pipelineTTFTEnd: basePlan.measurementMode.pipelineTtftEnd,
                userVisibleTTFTAvailable: registryPlan.userVisibleTtftAvailable,
                prefillSource: basePlan.measurementMode.prefillSource,
                decodeFormula: basePlan.measurementMode.decodeFormula,
                memoryMetric: basePlan.measurementMode.memoryMetric,
                memorySamplingIntervalMilliseconds: basePlan.measurementMode.memorySamplingIntervalMilliseconds
            ),
            generationConfiguration: .init(
                samplingEnabled: basePlan.generation.samplingEnabled,
                temperature: basePlan.generation.temperature,
                topP: basePlan.generation.topP,
                topK: basePlan.generation.topK,
                seed: basePlan.generation.seed,
                repetitionPenalty: basePlan.generation.repetitionPenalty,
                thinkingMode: registryPlan.thinkingMode,
                chatTemplateIdentity: basePlan.generation.chatTemplateIdentity,
                includeStopTokenInRawEvents: basePlan.generation.includeStopTokenInRawEvents,
                outputTokenLimit: registryPlan.outputTokenLimit,
                contextPolicy: basePlan.generation.contextPolicy,
                modelLoadPolicy: basePlan.generation.modelLoadPolicy,
                kvCachePolicy: basePlan.generation.kvCachePolicy
            ),
            model: modelIdentity(basePlan),
            runtime: runtimeIdentity(basePlan),
            device: deviceIdentity(environment),
            modelPreparation: modelPreparation,
            eligibility: .init(
                sessionValid: sessionValid,
                officialLeaderboardEligible: false,
                reasonCodes: sessionValid ? reasonCodes : ["session_environment_ineligible"] + reasonCodes
            ),
            bundleSummary: bundleSummary,
            sessions: sessions
        )
    }

    static func attempts(
        _ session: BenchmarkSession,
        memoryInterval: Int,
        includeQuality: Bool
    ) -> [Attempt] {
        session.attempts.map { attempt in
            let generation: RuntimeGenerationResult?
            let outcome: String
            let error: String?
            switch attempt.outcome {
            case .completed(let value): generation = value; outcome = "completed"; error = nil
            case .failed(let message): generation = nil; outcome = "failed"; error = message
            case .notRun(let reason): generation = nil; outcome = "notRun"; error = reason
            }
            let contract = includeQuality && generation != nil
                ? ContextAnswerContract.evaluate(generation?.generatedText) : nil
            return Attempt(
                runIndex: attempt.index,
                role: attempt.role.rawValue,
                outcome: outcome,
                errorMessage: error,
                promptTokenCount: generation?.promptTokenCount,
                outputTokenCount: generation?.outputTokenCount,
                stopReason: generation?.stopReason.rawValue,
                visibleText: generation?.generatedText,
                answerContract: contract,
                answerEligible: includeQuality ? contract?.passed == true : nil,
                thermalStateBefore: attempt.thermalStateBefore,
                thermalStateAfter: attempt.thermalStateAfter,
                memorySamplingIntervalMilliseconds: memoryInterval,
                metrics: .calculate(for: attempt),
                tokenEvents: attempt.tokens
            )
        }
    }

    static func session(
        id: String,
        target: Int?,
        fixtureSHA256: String,
        padding: Int?,
        benchmarkSession: BenchmarkSession,
        memoryInterval: Int,
        minimumSuccessfulRuns: Int,
        includeQuality: Bool
    ) -> Session {
        let records = attempts(benchmarkSession, memoryInterval: memoryInterval, includeQuality: includeQuality)
        let successful = records.filter { $0.role == "measured" && $0.outcome == "completed" }
        let passing = includeQuality ? successful.filter { $0.answerEligible == true }.count : nil
        let qualityEligible = passing.map { $0 == successful.count && successful.count == 5 }
        return Session(
            id: id,
            targetInputTokens: target,
            fixtureSHA256: fixtureSHA256,
            paddingRepetitions: padding,
            performanceEligible: successful.count >= minimumSuccessfulRuns && (qualityEligible ?? true),
            qualityEligible: qualityEligible,
            timingEvidenceRetained: true,
            summary: .init(
                successfulMeasuredRuns: successful.count,
                failedMeasuredRuns: 5 - successful.count,
                answerContractPassingRuns: passing,
                modelInputTokens: successful.first?.promptTokenCount,
                medianPipelineTTFTMilliseconds: AttemptMetrics.median(successful.map { $0.metrics.ttftMilliseconds }),
                medianUserVisibleTTFTMilliseconds: AttemptMetrics.median(successful.map { $0.metrics.userVisibleTTFTMilliseconds }),
                medianRequestCompletionMilliseconds: AttemptMetrics.median(successful.map { $0.metrics.requestCompletionMilliseconds }),
                medianPrefillTokensPerSecond: AttemptMetrics.median(successful.map { $0.metrics.prefillTokensPerSecond }),
                medianDecodeTokensPerSecond: AttemptMetrics.median(successful.map { $0.metrics.decodeTokensPerSecond }),
                medianPeakMemoryMegabytes: AttemptMetrics.median(successful.map { $0.metrics.peakMemoryMegabytes }),
                finalThermalState: records.last?.thermalStateAfter ?? "unknown"
            ),
            attempts: records
        )
    }

    private static func modelIdentity(_ plan: PilotPlan) -> PilotResultBundle.ModelIdentity {
        .init(displayName: plan.modelProfile.displayName, baseModelID: plan.modelProfile.baseModelId, artifactID: plan.modelProfile.artifactId, artifactRevision: plan.modelProfile.artifactRevision, quantization: plan.modelProfile.quantization, modelFormat: plan.modelProfile.modelFormat, artifactContentHash: plan.modelProfile.artifactContentHash)
    }

    private static func runtimeIdentity(_ plan: PilotPlan) -> PilotResultBundle.RuntimeIdentity {
        .init(name: plan.runtimeProfile.runtimeName, version: plan.runtimeProfile.packageVersion, resolvedRevision: plan.runtimeProfile.packageRevision, backend: plan.runtimeProfile.backend, mlxSwiftVersion: plan.runtimeProfile.mlxSwiftVersion, mlxSwiftRevision: plan.runtimeProfile.mlxSwiftRevision, downloaderPackage: plan.runtimeProfile.downloaderPackage, tokenizerPackage: plan.runtimeProfile.tokenizerPackage)
    }

    private static func deviceIdentity(_ environment: DeviceEnvironment) -> PilotResultBundle.DeviceIdentity {
        .init(displayName: environment.deviceDescription, machineIdentifier: environment.modelIdentifier, systemName: environment.systemName, systemVersion: environment.systemVersion, systemBuild: environment.systemBuild, debuggerAttached: environment.debuggerAttached, buildConfiguration: environment.buildConfiguration, appVersion: environment.appVersion, appBuild: environment.appBuild, appSourceCommit: environment.appSourceCommit, lowPowerModeEnabled: environment.lowPowerModeEnabled, batteryLevelPercent: environment.batteryLevelPercent, batteryState: environment.batteryState)
    }
}
