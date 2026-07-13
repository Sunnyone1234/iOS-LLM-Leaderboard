import Foundation

struct ContextAssistanceResultBundle: Codable, Sendable {
    let schemaVersion: String
    let resultID: String
    let createdAt: Date
    let officialResultEligible: Bool
    let workloadID: String
    let workloadVersion: String
    let documentSHA256: String
    let questionSHA256: String
    let pointOrder: [Int]
    let outputTokenLimit: Int
    let model: PilotResultBundle.ModelIdentity
    let runtime: PilotResultBundle.RuntimeIdentity
    let device: PilotResultBundle.DeviceIdentity
    let modelPreparation: ModelPreparationEvidence
    let points: [Point]

    struct Point: Codable, Sendable {
        let targetInputTokens: Int
        let fixtureSHA256: String
        let paddingRepetitions: Int
        let successfulMeasuredRuns: Int
        let answerContractPassingRuns: Int
        let uxPerformanceEligible: Bool
        let timingEvidenceRetained: Bool
        let medianPipelineTTFTMilliseconds: Double?
        let medianUserVisibleTTFTMilliseconds: Double?
        let medianRequestCompletionMilliseconds: Double?
        let medianPeakMemoryMegabytes: Double?
        let finalThermalState: String
        let attempts: [Attempt]
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
        let answerEligible: Bool
        let thermalStateBefore: String
        let thermalStateAfter: String
        let metrics: AttemptMetrics
        let tokenEvents: [RuntimeToken]
    }

    @MainActor
    static func make(
        calibratedSessions: [(InputLengthFixtureCalibration, BenchmarkSession)],
        environment: DeviceEnvironment,
        plan: PilotPlan,
        modelPreparation: ModelPreparationEvidence
    ) -> ContextAssistanceResultBundle {
        let points = calibratedSessions.map { calibration, session in
            let attempts = session.attempts.map { attempt in
                let generation: RuntimeGenerationResult?
                let outcome: String
                let error: String?
                switch attempt.outcome {
                case .completed(let value):
                    generation = value; outcome = "completed"; error = nil
                case .failed(let message):
                    generation = nil; outcome = "failed"; error = message
                case .notRun(let reason):
                    generation = nil; outcome = "notRun"; error = reason
                }
                let contract = generation.map { ContextAnswerContract.evaluate($0.generatedText) }
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
                    answerEligible: contract?.passed == true,
                    thermalStateBefore: attempt.thermalStateBefore,
                    thermalStateAfter: attempt.thermalStateAfter,
                    metrics: .calculate(for: attempt),
                    tokenEvents: attempt.tokens
                )
            }
            let successful = attempts.filter {
                $0.role == "measured" && $0.outcome == "completed"
            }
            let passing = successful.filter(\.answerEligible).count
            return Point(
                targetInputTokens: calibration.targetTokenCount,
                fixtureSHA256: calibration.promptSHA256,
                paddingRepetitions: calibration.paddingRepetitions,
                successfulMeasuredRuns: successful.count,
                answerContractPassingRuns: passing,
                uxPerformanceEligible: successful.count == 5 && passing == 5,
                timingEvidenceRetained: true,
                medianPipelineTTFTMilliseconds: AttemptMetrics.median(successful.map { $0.metrics.ttftMilliseconds }),
                medianUserVisibleTTFTMilliseconds: AttemptMetrics.median(successful.map { $0.metrics.userVisibleTTFTMilliseconds }),
                medianRequestCompletionMilliseconds: AttemptMetrics.median(successful.map { $0.metrics.requestCompletionMilliseconds }),
                medianPeakMemoryMegabytes: AttemptMetrics.median(successful.map { $0.metrics.peakMemoryMegabytes }),
                finalThermalState: attempts.last?.thermalStateAfter ?? "unknown",
                attempts: attempts
            )
        }
        return ContextAssistanceResultBundle(
            schemaVersion: "suite-b-context-assistance-bundle-0.1",
            resultID: UUID().uuidString.lowercased(),
            createdAt: Date(),
            officialResultEligible: false,
            workloadID: "b-ux-002-context-assistance",
            workloadVersion: "0.2.0-pilot",
            documentSHA256: "e13b4b66f137ac415bf525898f0b111d5d493d47a0a227164bba6e08f38674b4",
            questionSHA256: "86aecb086f2f2d9097b9464825249359bf08d6dc413c059756d2f850ba05f84b",
            pointOrder: calibratedSessions.map { $0.0.targetTokenCount },
            outputTokenLimit: 128,
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
            points: points
        )
    }
}
