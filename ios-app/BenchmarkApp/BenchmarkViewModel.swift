import Foundation
import Observation

@MainActor
@Observable
final class BenchmarkViewModel {
    struct UXValidationSummary: Equatable {
        let promptTokenCount: Int?
        let medianPipelineTTFTMilliseconds: Double?
        let medianUserVisibleTTFTMilliseconds: Double?
        let medianRequestCompletionMilliseconds: Double?
        let sampleOutput: String?
        let outputTokenCount: Int?
        let stopReason: String?
        let measuredMetrics: [AttemptMetrics]
    }
    enum PreparationPhase: Equatable {
        case notPrepared
        case preparing
        case ready
        case restartRequired
        case blocked(message: String)
        case failed(message: String)
    }

    enum Phase: Equatable {
        case ready
        case running
        case completed(measuredAttempts: Int, failedAttempts: Int)
        case failed(message: String)
    }

    private(set) var phase: Phase = .ready
    private(set) var preparationPhase: PreparationPhase = .notPrepared
    private(set) var modelPreparation: ModelPreparationEvidence?
    private(set) var result: PilotResultBundle?
    private(set) var resultFileURL: URL?
    private(set) var uxValidationSummary: UXValidationSummary?
    private(set) var currentThermalState = SystemMeasurements.thermalState
    private(set) var debuggerAttached = DebuggerStatus.isAttached
    private(set) var lowPowerModeEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled
    private(set) var buildConfiguration = BuildMetadata.configuration
    private(set) var configurationError: String?
    private(set) var inputLengthCalibrations: [InputLengthFixtureCalibration] = []
    private(set) var inputLengthCalibrationError: String?
    private(set) var isCalibratingInputLengths = false

    let loadedPlan: LoadedPilotPlan?

    private let runtime: any ModelPreparingRuntime
    private let resultStore = ResultStore()

    init(
        runtime: any ModelPreparingRuntime = MLXSwiftRuntime(),
        loadedPlan: LoadedPilotPlan? = nil
    ) {
        self.runtime = runtime
        if let loadedPlan {
            self.loadedPlan = loadedPlan
        } else {
            do {
                self.loadedPlan = try PilotPlanLoader.load()
            } catch {
                self.loadedPlan = nil
                configurationError = String(describing: error)
            }
        }
    }

    var canPrepare: Bool {
        loadedPlan != nil
            && preparationPhase != .preparing
            && phase != .running
            && preparationPhase != .restartRequired
    }

    var canRun: Bool {
        phase != .running && admissionReasonCodes.isEmpty
    }

    var canCalibrateInputLengths: Bool {
        preparationPhase == .ready && phase != .running && !isCalibratingInputLengths
    }

    var admissionReasonCodes: [String] {
        guard let plan = loadedPlan?.plan else { return ["plan_not_loaded"] }
        return BenchmarkAdmission.reasonCodes(
            preparation: modelPreparation,
            environment: .init(
                debuggerAttached: debuggerAttached,
                buildConfiguration: buildConfiguration,
                lowPowerModeEnabled: lowPowerModeEnabled,
                thermalState: currentThermalState
            ),
            requirements: plan.environmentRequirements
        )
    }

    var statusText: String {
        if let configurationError {
            return "Configuration error: \(configurationError)"
        }
        switch preparationPhase {
        case .notPrepared:
            return "Prepare the pinned model before measuring."
        case .preparing:
            return "Checking the pinned revision, downloading if needed, then loading the model…"
        case .restartRequired:
            return "Model downloaded — restart required before measuring."
        case .blocked(let message), .failed(let message):
            return message
        case .ready:
            break
        }
        if debuggerAttached {
            return "Debugger attached. In Edit Scheme → Run → Info, turn off Debug executable before measuring."
        }
        if buildConfiguration != "Release" {
            return "Use the Release build configuration before measuring."
        }
        if lowPowerModeEnabled {
            return "Turn off Low Power Mode before measuring."
        }
        if currentThermalState != "nominal" {
            return "Wait for this iPhone to cool to nominal, then pull down to refresh."
        }
        return switch phase {
        case .ready:
            "Model prepared from a verified cache. Ready to measure."
        case .running:
            "Running \(loadedPlan?.plan.procedure.warmupRuns ?? 0) warm-up and \(loadedPlan?.plan.procedure.measuredRuns ?? 0) measured attempts…"
        case .completed(let measuredAttempts, let failedAttempts):
            "Saved \(measuredAttempts) measured records; \(failedAttempts) did not complete."
        case .failed(let message):
            "Run failed: \(message)"
        }
    }

    func prepareModel() async {
        guard canPrepare, let plan = loadedPlan?.plan else { return }
        preparationPhase = .preparing
        let evidence = await runtime.prepare(plan: plan)
        modelPreparation = evidence
        preparationPhase = Self.preparationPhase(for: evidence)
    }

    static func preparationPhase(
        for evidence: ModelPreparationEvidence
    ) -> PreparationPhase {
        if evidence.downloadOccurredDuringSession {
            return .restartRequired
        } else if evidence.eligibleForPerformanceMeasurement {
            return .ready
        } else if evidence.reasonCodes.contains("model_preparation_failed")
            || evidence.reasonCodes.contains("model_load_failed") {
            return .failed(
                message: "Model preparation failed: \(evidence.reasonCodes.joined(separator: ", "))"
            )
        } else {
            return .blocked(
                message: "Model preparation blocked: \(evidence.reasonCodes.joined(separator: ", "))"
            )
        }
    }

    func run() async {
        debuggerAttached = DebuggerStatus.isAttached
        lowPowerModeEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled
        buildConfiguration = BuildMetadata.configuration
        guard canRun,
              let loadedPlan,
              let modelPreparation else { return }
        let sessionEnvironment = DeviceEnvironment.current
        phase = .running
        currentThermalState = SystemMeasurements.thermalState

        do {
            let session = await BenchmarkRunner(
                runtime: runtime,
                procedure: BenchmarkProcedure(
                    warmupRuns: loadedPlan.plan.procedure.warmupRuns,
                    measuredRuns: loadedPlan.plan.procedure.measuredRuns,
                    outputTokenLimit: loadedPlan.plan.workload.outputTokenLimit
                )
            ).run(prompt: loadedPlan.prompt)

            guard !session.measuredAttempts.isEmpty else {
                let message = session.attempts.first.map(Self.failureMessage)
                    ?? "No attempts were recorded."
                phase = .failed(message: message)
                return
            }

            let failures = session.measuredAttempts.filter { attempt in
                if case .completed = attempt.outcome { return false }
                return true
            }.count
            if loadedPlan.plan.workload.category == "user-experience" {
                let completed = session.measuredAttempts.compactMap { attempt -> (RuntimeGenerationResult, AttemptMetrics)? in
                    guard case .completed(let generation) = attempt.outcome else { return nil }
                    return (generation, AttemptMetrics.calculate(for: attempt))
                }
                uxValidationSummary = UXValidationSummary(
                    promptTokenCount: completed.first?.0.promptTokenCount,
                    medianPipelineTTFTMilliseconds: AttemptMetrics.median(
                        completed.map { $0.1.ttftMilliseconds }
                    ),
                    medianUserVisibleTTFTMilliseconds: AttemptMetrics.median(
                        completed.map { $0.1.userVisibleTTFTMilliseconds }
                    ),
                    medianRequestCompletionMilliseconds: AttemptMetrics.median(
                        completed.map { $0.1.requestCompletionMilliseconds }
                    ),
                    sampleOutput: completed.first?.0.generatedText,
                    outputTokenCount: completed.first?.0.outputTokenCount,
                    stopReason: completed.first?.0.stopReason.rawValue,
                    measuredMetrics: completed.map(\.1)
                )
                result = nil
                let uxBundle = UXResultBundle.make(
                    session: session,
                    environment: sessionEnvironment,
                    plan: loadedPlan.plan,
                    modelPreparation: modelPreparation
                )
                resultFileURL = try await resultStore.save(uxBundle)
                currentThermalState = session.measuredAttempts.last?.thermalStateAfter
                    ?? SystemMeasurements.thermalState
                phase = .completed(
                    measuredAttempts: session.measuredAttempts.count,
                    failedAttempts: failures
                )
                return
            }
            let bundle = PilotResultBundle.make(
                session: session,
                environment: sessionEnvironment,
                plan: loadedPlan.plan,
                modelPreparation: modelPreparation
            )
            resultFileURL = try await resultStore.save(bundle)
            result = bundle
            currentThermalState = bundle.summary.finalThermalState
            phase = .completed(
                measuredAttempts: session.measuredAttempts.count,
                failedAttempts: failures
            )
        } catch {
            currentThermalState = SystemMeasurements.thermalState
            phase = .failed(message: String(describing: error))
        }
    }

    func refreshThermalState() {
        currentThermalState = SystemMeasurements.thermalState
        debuggerAttached = DebuggerStatus.isAttached
        lowPowerModeEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled
        buildConfiguration = BuildMetadata.configuration
    }

    func calibrateInputLengths() async {
        guard canCalibrateInputLengths else { return }
        isCalibratingInputLengths = true
        inputLengthCalibrationError = nil
        do {
            inputLengthCalibrations = try await runtime.calibrateInputLengthFixtures(
                targets: [32, 128, 512, 2048]
            )
        } catch {
            inputLengthCalibrations = []
            inputLengthCalibrationError = String(describing: error)
        }
        isCalibratingInputLengths = false
    }

    func metricText(_ value: Double?, unit: String) -> String {
        guard let value else { return "Unavailable" }
        return "\(value.formatted(.number.precision(.fractionLength(1)))) \(unit)"
    }

    func percentText(_ value: Double?) -> String {
        guard let value else { return "Unavailable" }
        return value.formatted(
            .number
                .sign(strategy: .always())
                .precision(.fractionLength(1))
        ) + "%"
    }

    var measuredAttemptRecords: [PilotResultBundle.Attempt] {
        result?.attempts.filter { $0.role == "measured" } ?? []
    }

    var warmupAttemptRecord: PilotResultBundle.Attempt? {
        result?.attempts.first { $0.role == "warmup" }
    }

    private static func failureMessage(_ attempt: BenchmarkAttempt) -> String {
        switch attempt.outcome {
        case .completed:
            "The runner stopped before measured attempts."
        case .failed(let message):
            message
        case .notRun(let reason):
            reason
        }
    }
}
