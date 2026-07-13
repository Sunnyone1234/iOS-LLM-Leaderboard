import Foundation

struct InputSweepResultBundle: Codable, Sendable {
    let schemaVersion: String
    let resultID: String
    let createdAt: Date
    let officialResultEligible: Bool
    let workloadID: String
    let workloadVersion: String
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
        let medianPipelineTTFTMilliseconds: Double?
        let medianPrefillTokensPerSecond: Double?
        let medianPeakMemoryMegabytes: Double?
        let finalThermalState: String
        let attempts: [PilotResultBundle.Attempt]
    }

    @MainActor
    static func make(
        calibratedSessions: [(InputLengthFixtureCalibration, BenchmarkSession)],
        environment: DeviceEnvironment,
        plan: PilotPlan,
        modelPreparation: ModelPreparationEvidence
    ) -> InputSweepResultBundle {
        let points = calibratedSessions.map { calibration, session in
            let attempts = session.attempts.map { attempt in
                let generation: RuntimeGenerationResult?
                let outcome: String
                let error: String?
                switch attempt.outcome {
                case .completed(let value):
                    generation = value; outcome = "completed"; error = nil
                case .failed(let message, _):
                    generation = nil; outcome = "failed"; error = message
                case .cancelled(_, let partial):
                    generation = partial; outcome = "cancelled"; error = "cancelled"
                case .outOfMemory(_, let partial):
                    generation = partial; outcome = "outOfMemory"; error = "outOfMemory"
                case .notRun(let reason):
                    generation = nil; outcome = "notRun"; error = reason
                }
                return PilotResultBundle.Attempt(
                    runIndex: attempt.index,
                    role: attempt.role.rawValue,
                    outcome: outcome,
                    errorMessage: error,
                    promptTokenCount: generation?.promptTokenCount,
                    outputTokenCount: generation?.outputTokenCount,
                    stopReason: generation?.stopReason.rawValue,
                    thermalStateBefore: attempt.thermalStateBefore,
                    thermalStateAfter: attempt.thermalStateAfter,
                    memorySamplingIntervalMilliseconds: 50,
                    metrics: .calculate(for: attempt),
                    tokenEvents: attempt.tokens
                )
            }
            let successful = attempts.filter {
                $0.role == "measured" && $0.outcome == "completed"
            }
            return Point(
                targetInputTokens: calibration.targetTokenCount,
                fixtureSHA256: calibration.promptSHA256,
                paddingRepetitions: calibration.paddingRepetitions,
                successfulMeasuredRuns: successful.count,
                medianPipelineTTFTMilliseconds: AttemptMetrics.median(
                    successful.map { $0.metrics.ttftMilliseconds }
                ),
                medianPrefillTokensPerSecond: AttemptMetrics.median(
                    successful.map { $0.metrics.prefillTokensPerSecond }
                ),
                medianPeakMemoryMegabytes: AttemptMetrics.median(
                    successful.map { $0.metrics.peakMemoryMegabytes }
                ),
                finalThermalState: attempts.last?.thermalStateAfter ?? "unknown",
                attempts: attempts
            )
        }
        return InputSweepResultBundle(
            schemaVersion: "suite-b-input-sweep-bundle-0.1",
            resultID: UUID().uuidString.lowercased(),
            createdAt: Date(),
            officialResultEligible: false,
            workloadID: "b-pipe-002-input-length-sweep",
            workloadVersion: "0.2.0-pilot",
            pointOrder: calibratedSessions.map { $0.0.targetTokenCount },
            outputTokenLimit: 32,
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
