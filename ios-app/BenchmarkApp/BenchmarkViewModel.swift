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

    struct InputSweepPointSummary: Equatable {
        let targetTokenCount: Int
        let actualTokenCount: Int
        let promptSHA256: String
        let successfulMeasuredRuns: Int
        let medianPipelineTTFTMilliseconds: Double?
        let medianPrefillTokensPerSecond: Double?
        let medianPeakMemoryMegabytes: Double?
        let finalThermalState: String
    }

    struct ContextPointSummary: Equatable {
        let targetTokenCount: Int
        let successfulMeasuredRuns: Int
        let contractPassingRuns: Int
        let medianPipelineTTFTMilliseconds: Double?
        let medianUserVisibleTTFTMilliseconds: Double?
        let medianRequestCompletionMilliseconds: Double?
        let medianPeakMemoryMegabytes: Double?
        let sampleOutput: String?
        let finalThermalState: String
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
    private(set) var inputSweepResults: [InputSweepPointSummary] = []
    private(set) var inputSweepError: String?
    private(set) var isRunningInputSweep = false
    private(set) var contextCalibrations: [InputLengthFixtureCalibration] = []
    private(set) var contextCalibrationError: String?
    private(set) var isCalibratingContext = false
    private(set) var contextResults: [ContextPointSummary] = []
    private(set) var contextRunError: String?
    private(set) var isRunningContext = false
    private(set) var workloadRegistry: SuiteBPlanRegistry?
    private(set) var latestUnifiedResult: SuiteBResultBundle?
    private(set) var submissionFileURL: URL?
    private(set) var submissionError: String?
    var contributorName = ""
    var reviewedResult = false
    var confirmsNoPersonalData = false
    var agreesToRepositoryLicense = false

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
        do {
            workloadRegistry = try SuiteBPlanRegistryLoader.load()
        } catch {
            configurationError = String(describing: error)
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
            && workloadRegistry?.plan(workloadID: "b-pipe-002-input-length-sweep") != nil
    }

    var canRunInputSweep: Bool {
        canRun && inputLengthCalibrations.map(\.targetTokenCount)
            == workloadRegistry?.plan(workloadID: "b-pipe-002-input-length-sweep")?.targetInputTokens
            && !isRunningInputSweep
    }

    var canCalibrateContext: Bool {
        preparationPhase == .ready && phase != .running && !isCalibratingContext
            && workloadRegistry?.plan(workloadID: "b-ux-002-context-assistance") != nil
    }

    var canRunContext: Bool {
        canRun && contextCalibrations.map(\.targetTokenCount)
            == workloadRegistry?.plan(workloadID: "b-ux-002-context-assistance")?.targetInputTokens
            && !isRunningContext
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

    var canGenerateSubmission: Bool {
        latestUnifiedResult != nil
            && !contributorName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && reviewedResult && confirmsNoPersonalData && agreesToRepositoryLicense
    }

    func generateCommunitySubmission() async {
        guard canGenerateSubmission, let latestUnifiedResult else { return }
        do {
            let submission = try CommunitySubmissionBundle.make(
                result: latestUnifiedResult,
                contributorName: contributorName,
                declarations: .init(
                    reviewedResult: reviewedResult,
                    confirmsNoPersonalData: confirmsNoPersonalData,
                    agreesToRepositoryLicense: agreesToRepositoryLicense
                )
            )
            submissionFileURL = try await resultStore.save(submission)
            submissionError = nil
        } catch {
            submissionError = String(describing: error)
        }
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
                guard let registryPlan = workloadRegistry?.plan(
                    workloadID: loadedPlan.plan.workload.workloadId
                ) else { throw SuiteBPlanRegistryLoader.RegistryError.missing }
                let unified = SuiteBResultBundle.common(
                    registryPlan: registryPlan,
                    basePlan: loadedPlan.plan,
                    environment: sessionEnvironment,
                    modelPreparation: modelPreparation,
                    sessions: [SuiteBResultBundle.session(
                        id: "default",
                        target: nil,
                        fixtureSHA256: registryPlan.fixtureSha256[0],
                        padding: nil,
                        benchmarkSession: session,
                        memoryInterval: loadedPlan.plan.measurementMode.memorySamplingIntervalMilliseconds,
                        minimumSuccessfulRuns: loadedPlan.plan.procedure.minimumSuccessfulRunsForSummary,
                        includeQuality: false
                    )]
                )
                resultFileURL = try await resultStore.save(unified)
                latestUnifiedResult = unified
                submissionFileURL = nil
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
            guard let registryPlan = workloadRegistry?.plan(
                workloadID: loadedPlan.plan.workload.workloadId
            ) else { throw SuiteBPlanRegistryLoader.RegistryError.missing }
            let degradation = bundle.summary.degradation
            let unified = SuiteBResultBundle.common(
                registryPlan: registryPlan,
                basePlan: loadedPlan.plan,
                environment: sessionEnvironment,
                modelPreparation: modelPreparation,
                sessions: [SuiteBResultBundle.session(
                    id: "default",
                    target: nil,
                    fixtureSHA256: registryPlan.fixtureSha256[0],
                    padding: nil,
                    benchmarkSession: session,
                    memoryInterval: loadedPlan.plan.measurementMode.memorySamplingIntervalMilliseconds,
                    minimumSuccessfulRuns: loadedPlan.plan.procedure.minimumSuccessfulRunsForSummary,
                    includeQuality: false
                )],
                bundleSummary: .init(
                    firstMeasuredRunIndex: degradation.firstMeasuredRunIndex,
                    lastMeasuredRunIndex: degradation.lastMeasuredRunIndex,
                    decodePercentChange: degradation.decodePercentChange,
                    ttftPercentChange: degradation.ttftPercentChange,
                    prefillPercentChange: degradation.prefillPercentChange
                )
            )
            resultFileURL = try await resultStore.save(unified)
            latestUnifiedResult = unified
            submissionFileURL = nil
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
            guard let plan = workloadRegistry?.plan(
                workloadID: "b-pipe-002-input-length-sweep"
            ) else { throw SuiteBPlanRegistryLoader.RegistryError.missing }
            inputLengthCalibrations = try await runtime.calibrateInputLengthFixtures(
                targets: plan.targetInputTokens
            )
        } catch {
            inputLengthCalibrations = []
            inputLengthCalibrationError = String(describing: error)
        }
        isCalibratingInputLengths = false
    }

    func runInputSweep() async {
        guard canRunInputSweep,
              let sweepPlan = workloadRegistry?.plan(
                workloadID: "b-pipe-002-input-length-sweep"
              ) else { return }
        isRunningInputSweep = true
        inputSweepError = nil
        inputSweepResults = []
        var calibratedSessions: [(InputLengthFixtureCalibration, BenchmarkSession)] = []

        for calibration in inputLengthCalibrations {
            guard SystemMeasurements.thermalState == "nominal" else {
                inputSweepError = "Target \(calibration.targetTokenCount) was not started because thermal state was not nominal. Cool the iPhone, then start a new sweep."
                isRunningInputSweep = false
                return
            }
            let prompt = InputLengthFixtureGenerator.prompt(
                paddingRepetitions: calibration.paddingRepetitions
            )
            let session = await BenchmarkRunner(
                runtime: runtime,
                procedure: BenchmarkProcedure(
                    warmupRuns: sweepPlan.warmupRuns,
                    measuredRuns: sweepPlan.measuredRuns,
                    outputTokenLimit: sweepPlan.outputTokenLimit
                )
            ).run(prompt: prompt)
            let completed = session.measuredAttempts.compactMap { attempt -> (RuntimeGenerationResult, AttemptMetrics)? in
                guard case .completed(let generation) = attempt.outcome else { return nil }
                return (generation, AttemptMetrics.calculate(for: attempt))
            }
            guard completed.count >= 3,
                  completed.allSatisfy({ $0.0.promptTokenCount == calibration.targetTokenCount }) else {
                inputSweepError = "Target \(calibration.targetTokenCount) failed exact-token or successful-run admission."
                isRunningInputSweep = false
                return
            }
            inputSweepResults.append(
                InputSweepPointSummary(
                    targetTokenCount: calibration.targetTokenCount,
                    actualTokenCount: completed[0].0.promptTokenCount,
                    promptSHA256: calibration.promptSHA256,
                    successfulMeasuredRuns: completed.count,
                    medianPipelineTTFTMilliseconds: AttemptMetrics.median(
                        completed.map { $0.1.ttftMilliseconds }
                    ),
                    medianPrefillTokensPerSecond: AttemptMetrics.median(
                        completed.map { $0.1.prefillTokensPerSecond }
                    ),
                    medianPeakMemoryMegabytes: AttemptMetrics.median(
                        completed.map { $0.1.peakMemoryMegabytes }
                    ),
                    finalThermalState: session.attempts.last?.thermalStateAfter
                        ?? SystemMeasurements.thermalState
                )
            )
            calibratedSessions.append((calibration, session))
            if SystemMeasurements.thermalState == "critical" {
                inputSweepError = "Thermal state became critical; remaining points were not run."
                isRunningInputSweep = false
                return
            }
        }
        if let modelPreparation {
            let sessions = calibratedSessions.map { calibration, benchmarkSession in
                SuiteBResultBundle.session(
                    id: "input-\(calibration.targetTokenCount)",
                    target: calibration.targetTokenCount,
                    fixtureSHA256: calibration.promptSHA256,
                    padding: calibration.paddingRepetitions,
                    benchmarkSession: benchmarkSession,
                    memoryInterval: loadedPlan!.plan.measurementMode.memorySamplingIntervalMilliseconds,
                    minimumSuccessfulRuns: 3,
                    includeQuality: false
                )
            }
            let bundle = SuiteBResultBundle.common(
                registryPlan: sweepPlan,
                basePlan: loadedPlan!.plan,
                environment: DeviceEnvironment.current,
                modelPreparation: modelPreparation,
                sessions: sessions
            )
            do {
                resultFileURL = try await resultStore.save(bundle)
                latestUnifiedResult = bundle
                submissionFileURL = nil
            } catch {
                inputSweepError = "Sweep completed but export failed: \(error)"
            }
        }
        currentThermalState = SystemMeasurements.thermalState
        isRunningInputSweep = false
    }

    func calibrateContextAssistance() async {
        guard canCalibrateContext else { return }
        isCalibratingContext = true
        contextCalibrationError = nil
        do {
            guard let documentURL = Bundle.main.url(
                forResource: "b-ux-002-context-assistance-document",
                withExtension: "txt"
            ), let questionURL = Bundle.main.url(
                forResource: "b-ux-002-context-assistance-question",
                withExtension: "txt"
            ) else {
                throw CocoaError(.fileNoSuchFile)
            }
            let document = try String(contentsOf: documentURL, encoding: .utf8)
            let question = try String(contentsOf: questionURL, encoding: .utf8)
            guard let plan = workloadRegistry?.plan(
                workloadID: "b-ux-002-context-assistance"
            ) else { throw SuiteBPlanRegistryLoader.RegistryError.missing }
            contextCalibrations = try await runtime.calibrateContextAssistanceFixtures(
                document: document,
                question: question,
                targets: plan.targetInputTokens
            )
        } catch {
            contextCalibrations = []
            contextCalibrationError = String(describing: error)
        }
        isCalibratingContext = false
    }

    func runContextAssistance() async {
        guard canRunContext,
              let contextPlan = workloadRegistry?.plan(
                workloadID: "b-ux-002-context-assistance"
              ) else { return }
        isRunningContext = true
        contextResults = []
        contextRunError = nil
        var calibratedSessions: [(InputLengthFixtureCalibration, BenchmarkSession)] = []
        do {
            guard let documentURL = Bundle.main.url(forResource: "b-ux-002-context-assistance-document", withExtension: "txt"),
                  let questionURL = Bundle.main.url(forResource: "b-ux-002-context-assistance-question", withExtension: "txt") else {
                throw CocoaError(.fileNoSuchFile)
            }
            let document = try String(contentsOf: documentURL, encoding: .utf8)
            let question = try String(contentsOf: questionURL, encoding: .utf8)
            for calibration in contextCalibrations {
                guard SystemMeasurements.thermalState == "nominal" else {
                    contextRunError = "Target \(calibration.targetTokenCount) was not started because thermal state was not nominal."
                    isRunningContext = false
                    return
                }
                let prompt = ContextAssistanceFixtureGenerator.prompt(
                    document: document,
                    question: question,
                    paddingRepetitions: calibration.paddingRepetitions
                )
                let session = await BenchmarkRunner(
                    runtime: runtime,
                    procedure: .init(
                        warmupRuns: contextPlan.warmupRuns,
                        measuredRuns: contextPlan.measuredRuns,
                        outputTokenLimit: contextPlan.outputTokenLimit
                    )
                ).run(prompt: prompt)
                let completed = session.measuredAttempts.compactMap { attempt -> (RuntimeGenerationResult, AttemptMetrics)? in
                    guard case .completed(let generation) = attempt.outcome else { return nil }
                    return (generation, .calculate(for: attempt))
                }
                guard completed.count >= 3,
                      completed.allSatisfy({ $0.0.promptTokenCount == calibration.targetTokenCount }) else {
                    contextRunError = "Target \(calibration.targetTokenCount) failed exact-token or run-count admission."
                    isRunningContext = false
                    return
                }
                let passing = completed.filter {
                    ContextAnswerContract.evaluate($0.0.generatedText).passed
                }.count
                contextResults.append(.init(
                    targetTokenCount: calibration.targetTokenCount,
                    successfulMeasuredRuns: completed.count,
                    contractPassingRuns: passing,
                    medianPipelineTTFTMilliseconds: AttemptMetrics.median(completed.map { $0.1.ttftMilliseconds }),
                    medianUserVisibleTTFTMilliseconds: AttemptMetrics.median(completed.map { $0.1.userVisibleTTFTMilliseconds }),
                    medianRequestCompletionMilliseconds: AttemptMetrics.median(completed.map { $0.1.requestCompletionMilliseconds }),
                    medianPeakMemoryMegabytes: AttemptMetrics.median(completed.map { $0.1.peakMemoryMegabytes }),
                    sampleOutput: completed.first?.0.generatedText,
                    finalThermalState: session.attempts.last?.thermalStateAfter ?? "unknown"
                ))
                calibratedSessions.append((calibration, session))
            }
            if let modelPreparation {
                let sessions = calibratedSessions.map { calibration, benchmarkSession in
                    SuiteBResultBundle.session(
                        id: "context-\(calibration.targetTokenCount)",
                        target: calibration.targetTokenCount,
                        fixtureSHA256: calibration.promptSHA256,
                        padding: calibration.paddingRepetitions,
                        benchmarkSession: benchmarkSession,
                        memoryInterval: loadedPlan!.plan.measurementMode.memorySamplingIntervalMilliseconds,
                        minimumSuccessfulRuns: 3,
                        includeQuality: true
                    )
                }
                let bundle = SuiteBResultBundle.common(
                    registryPlan: contextPlan,
                    basePlan: loadedPlan!.plan,
                    environment: DeviceEnvironment.current,
                    modelPreparation: modelPreparation,
                    sessions: sessions
                )
                resultFileURL = try await resultStore.save(bundle)
                latestUnifiedResult = bundle
                submissionFileURL = nil
            }
        } catch {
            contextRunError = String(describing: error)
        }
        currentThermalState = SystemMeasurements.thermalState
        isRunningContext = false
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
