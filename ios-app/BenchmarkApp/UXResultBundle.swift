import Foundation

struct UXResultBundle: Codable, Sendable {
    let schemaVersion: String
    let resultID: String
    let createdAt: Date
    let officialResultEligible: Bool
    let plan: PilotResultBundle.PlanIdentity
    let workload: PilotResultBundle.WorkloadIdentity
    let measurementMode: PilotResultBundle.MeasurementModeIdentity
    let generationConfiguration: PilotResultBundle.GenerationConfiguration
    let model: PilotResultBundle.ModelIdentity
    let runtime: PilotResultBundle.RuntimeIdentity
    let device: PilotResultBundle.DeviceIdentity
    let modelPreparation: ModelPreparationEvidence
    let eligibility: PilotResultBundle.Eligibility
    let summary: Summary
    let attempts: [Attempt]

    struct Summary: Codable, Sendable {
        let successfulMeasuredRuns: Int
        let failedMeasuredRuns: Int
        let modelInputTokens: Int?
        let medianPipelineTTFTMilliseconds: Double?
        let medianUserVisibleTTFTMilliseconds: Double?
        let medianRequestCompletionMilliseconds: Double?
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
        let thermalStateBefore: String
        let thermalStateAfter: String
        let metrics: AttemptMetrics
        let tokenEvents: [RuntimeToken]
    }

    @MainActor
    static func make(
        session: BenchmarkSession,
        environment: DeviceEnvironment,
        plan: PilotPlan,
        modelPreparation: ModelPreparationEvidence
    ) -> UXResultBundle {
        let attempts = session.attempts.map { attempt in
            let generation: RuntimeGenerationResult?
            let outcome: String
            let error: String?
            switch attempt.outcome {
            case .completed(let value):
                generation = value
                outcome = "completed"
                error = nil
            case .failed(let message, _):
                generation = nil
                outcome = "failed"
                error = message
            case .cancelled(_, let partial):
                generation = partial
                outcome = "cancelled"
                error = "cancelled"
            case .outOfMemory(_, let partial):
                generation = partial
                outcome = "outOfMemory"
                error = "outOfMemory"
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
                visibleText: generation?.generatedText,
                thermalStateBefore: attempt.thermalStateBefore,
                thermalStateAfter: attempt.thermalStateAfter,
                metrics: .calculate(for: attempt),
                tokenEvents: attempt.tokens
            )
        }
        let successful = attempts.filter {
            $0.role == "measured" && $0.outcome == "completed"
        }
        let failed = attempts.filter { $0.role == "measured" }.count
            - successful.count

        return UXResultBundle(
            schemaVersion: "suite-b-ux-bundle-0.1",
            resultID: UUID().uuidString.lowercased(),
            createdAt: Date(),
            officialResultEligible: false,
            plan: .init(
                id: plan.planId,
                version: plan.planVersion,
                promptSHA256: plan.workload.promptSha256,
                warmupRuns: plan.procedure.warmupRuns,
                measuredRuns: plan.procedure.measuredRuns,
                outputTokenLimit: plan.workload.outputTokenLimit,
                v2ProfileMapping: plan.workload.v2ProfileMapping
            ),
            workload: .init(
                id: plan.workload.workloadId,
                version: plan.workload.workloadVersion,
                category: plan.workload.category,
                promptSHA256: plan.workload.promptSha256
            ),
            measurementMode: .init(
                id: plan.measurementMode.measurementModeId,
                timingBoundaryVersion: plan.measurementMode.timingBoundaryVersion,
                pipelineTTFTStart: plan.measurementMode.pipelineTtftStart,
                pipelineTTFTEnd: plan.measurementMode.pipelineTtftEnd,
                userVisibleTTFTAvailable: true,
                prefillSource: plan.measurementMode.prefillSource,
                decodeFormula: plan.measurementMode.decodeFormula,
                memoryMetric: plan.measurementMode.memoryMetric,
                memorySamplingIntervalMilliseconds:
                    plan.measurementMode.memorySamplingIntervalMilliseconds
            ),
            generationConfiguration: .init(
                samplingEnabled: plan.generation.samplingEnabled,
                temperature: plan.generation.temperature,
                topP: plan.generation.topP,
                topK: plan.generation.topK,
                seed: plan.generation.seed,
                repetitionPenalty: plan.generation.repetitionPenalty,
                thinkingMode: plan.generation.thinkingMode,
                chatTemplateIdentity: plan.generation.chatTemplateIdentity,
                includeStopTokenInRawEvents: plan.generation.includeStopTokenInRawEvents,
                outputTokenLimit: plan.workload.outputTokenLimit,
                contextPolicy: plan.generation.contextPolicy,
                modelLoadPolicy: plan.generation.modelLoadPolicy,
                kvCachePolicy: plan.generation.kvCachePolicy
            ),
            model: .init(
                displayName: plan.modelProfile.displayName,
                baseModelID: plan.modelProfile.baseModelId,
                artifactID: plan.modelProfile.artifactId,
                artifactRevision: plan.modelProfile.artifactRevision,
                quantization: plan.modelProfile.quantization,
                modelFormat: plan.modelProfile.modelFormat,
                artifactContentHash: plan.modelProfile.artifactContentHash
            ),
            runtime: .init(
                name: plan.runtimeProfile.runtimeName,
                version: plan.runtimeProfile.packageVersion,
                resolvedRevision: plan.runtimeProfile.packageRevision,
                backend: plan.runtimeProfile.backend,
                mlxSwiftVersion: plan.runtimeProfile.mlxSwiftVersion,
                mlxSwiftRevision: plan.runtimeProfile.mlxSwiftRevision,
                downloaderPackage: plan.runtimeProfile.downloaderPackage,
                tokenizerPackage: plan.runtimeProfile.tokenizerPackage
            ),
            device: .init(
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
                attempts: attempts.map { attempt in
                    PilotResultBundle.Attempt(
                        runIndex: attempt.runIndex,
                        role: attempt.role,
                        outcome: attempt.outcome,
                        errorMessage: attempt.errorMessage,
                        promptTokenCount: attempt.promptTokenCount,
                        outputTokenCount: attempt.outputTokenCount,
                        stopReason: attempt.stopReason,
                        thermalStateBefore: attempt.thermalStateBefore,
                        thermalStateAfter: attempt.thermalStateAfter,
                        memorySamplingIntervalMilliseconds:
                            plan.measurementMode.memorySamplingIntervalMilliseconds,
                        metrics: attempt.metrics,
                        tokenEvents: attempt.tokenEvents
                    )
                },
                modelPreparation: modelPreparation,
                debuggerAttached: environment.debuggerAttached,
                buildConfiguration: environment.buildConfiguration,
                lowPowerModeEnabled: environment.lowPowerModeEnabled,
                plannedMeasuredRuns: plan.procedure.measuredRuns
            ),
            summary: Summary(
                successfulMeasuredRuns: successful.count,
                failedMeasuredRuns: failed,
                modelInputTokens: successful.first?.promptTokenCount,
                medianPipelineTTFTMilliseconds: AttemptMetrics.median(
                    successful.map { $0.metrics.ttftMilliseconds }
                ),
                medianUserVisibleTTFTMilliseconds: AttemptMetrics.median(
                    successful.map { $0.metrics.userVisibleTTFTMilliseconds }
                ),
                medianRequestCompletionMilliseconds: AttemptMetrics.median(
                    successful.map { $0.metrics.requestCompletionMilliseconds }
                ),
                finalThermalState: attempts.last?.thermalStateAfter
                    ?? environment.thermalState
            ),
            attempts: attempts
        )
    }
}
