import Foundation
import Observation

@MainActor
@Observable
final class BenchmarkViewModel {
    enum GitHubSubmissionPhase: Equatable {
        case idle
        case authorizing(code: String, verificationURL: URL)
        case publishing
        case completed(pullRequestURL: URL)
        case failed(message: String)
    }

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
    private(set) var batteryState = DeviceEnvironment.current.batteryState
    private(set) var batteryLevelPercent = DeviceEnvironment.current.batteryLevelPercent
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
    private(set) var latestPowerResult: PowerResultBundle?
    private(set) var storedPowerResults: [ResultStore.StoredPowerResult] = []
    private(set) var recoveryNotice: String?
    private(set) var submissionFileURL: URL?
    private(set) var submissionError: String?
    private(set) var powerSubmissionPackageURL: URL?
    private(set) var githubSubmissionPhase: GitHubSubmissionPhase = .idle
    private(set) var currentRunnerEligibility: PowerEligibility = .checking
    var submissionConflictCategory: SubmissionConflictCategory = .none
    var submissionConflictStatement = ""
    var submissionThermalAssistance: SubmissionThermalAssistance = .none
    var submissionEnvironmentNotes = ""
    var acceptsPowerSubmissionDeclarations = false
    var contributorName = ""
    var reviewedResult = false
    var confirmsNoPersonalData = false
    var agreesToRepositoryLicense = false

    private(set) var loadedPlan: LoadedPilotPlan?
    private(set) var selectedModelProfile: ProductionModelProfile = .small

    private let runtime: any ModelPreparingRuntime
    private let resultStore: ResultStore
    private let compatibilityPolicyFetcher: any PowerCompatibilityPolicyFetching
    private let powerCheckpointStore = PowerSessionCheckpointStore()
    private var compatibilityPolicy: PowerCompatibilityPolicy?

    init(
        runtime: any ModelPreparingRuntime = MLXSwiftRuntime(),
        loadedPlan: LoadedPilotPlan? = nil,
        resultStore: ResultStore = ResultStore(),
        compatibilityPolicyFetcher: any PowerCompatibilityPolicyFetching = GitHubPowerCompatibilityPolicyClient()
    ) {
        self.runtime = runtime
        self.resultStore = resultStore
        self.compatibilityPolicyFetcher = compatibilityPolicyFetcher
        if let loadedPlan {
            self.loadedPlan = loadedPlan
            selectedModelProfile = ProductionModelProfile.matching(
                loadedPlan.plan.modelProfile
            ) ?? .small
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
            && currentRunnerEligibility.isApproved
            && preparationPhase != .preparing
            && phase != .running
            && preparationPhase != .restartRequired
    }

    var canSelectBenchmarkPlan: Bool {
        preparationPhase != .preparing
            && preparationPhase != .restartRequired
            && phase != .running
            && !isCalibratingInputLengths
            && !isRunningInputSweep
            && !isCalibratingContext
            && !isRunningContext
    }

    var canSelectModelProfile: Bool { canSelectBenchmarkPlan }

    var canRun: Bool {
        phase != .running
            && currentRunnerEligibility.isApproved
            && !isCalibratingInputLengths
            && !isRunningInputSweep
            && !isCalibratingContext
            && !isRunningContext
            && admissionReasonCodes.isEmpty
            && powerContractError == nil
    }

    // Experimental registry entries remain for historical compatibility, but
    // current production Apps cannot execute them through the Power control
    // surface.
    var canCalibrateInputLengths: Bool {
        false
    }

    var canRunInputSweep: Bool {
        false
    }

    var canCalibrateContext: Bool {
        false
    }

    var canRunContext: Bool {
        false
    }

    var admissionReasonCodes: [String] {
        guard let plan = loadedPlan?.plan else { return ["plan_not_loaded"] }
        return BenchmarkAdmission.reasonCodes(
            preparation: modelPreparation,
            environment: .init(
                debuggerAttached: debuggerAttached,
                buildConfiguration: buildConfiguration,
                lowPowerModeEnabled: lowPowerModeEnabled,
                thermalState: currentThermalState,
                batteryState: batteryState,
                batteryLevelPercent: batteryLevelPercent
            ),
            requirements: plan.environmentRequirements
        )
    }

    var powerContractError: String? {
        guard let plan = loadedPlan?.plan else { return "Power plan is unavailable." }
        do {
            _ = try PowerBenchmarkRelease.workload(for: plan)
            _ = try PowerBenchmarkRelease.validateExecutionEnvironment(
                DeviceEnvironment.current
            )
            return nil
        } catch {
            return error.localizedDescription
        }
    }

    var canGenerateSubmission: Bool {
        latestUnifiedResult != nil
            && !contributorName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && reviewedResult && confirmsNoPersonalData && agreesToRepositoryLicense
    }

    var githubSubmissionConfigured: Bool {
        guard let clientID = Bundle.main.object(
            forInfoDictionaryKey: "GitHubOAuthClientID"
        ) as? String else { return false }
        return !clientID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !clientID.contains("$(")
    }

    var canSubmitLatestPowerResultToGitHub: Bool {
        let disclosureComplete = submissionConflictCategory == .none
            || !submissionConflictStatement.trimmingCharacters(
                in: .whitespacesAndNewlines
            ).isEmpty
        let submissionIdle: Bool
        switch githubSubmissionPhase {
        case .authorizing, .publishing, .completed:
            submissionIdle = false
        case .idle, .failed:
            submissionIdle = true
        }
        return latestPowerResult != nil
            && resultFileURL != nil
            && selectedResultEligibility.isApproved
            && acceptsPowerSubmissionDeclarations
            && githubSubmissionConfigured
            && disclosureComplete
            && submissionIdle
    }

    var selectedPowerResultID: UUID? { latestPowerResult?.resultID }

    var selectedResultEligibility: PowerEligibility {
        guard let latestPowerResult else { return .noResult }
        switch currentRunnerEligibility {
        case .checking:
            return .checking
        case .unavailable(let message):
            return .unavailable(message: message)
        case .approved, .notApproved:
            guard let compatibilityPolicy else {
                return .unavailable(
                    message: "No verified Power compatibility policy is loaded."
                )
            }
            let identity = PowerRunnerIdentity(result: latestPowerResult)
            if let approval = compatibilityPolicy.approval(for: identity) {
                return .approved(
                    policyVersion: compatibilityPolicy.policyVersion,
                    approvalID: approval.approvalID
                )
            }
            return .notApproved(policyVersion: compatibilityPolicy.policyVersion)
        case .noResult:
            return .noResult
        }
    }

    var canSelectStoredPowerResult: Bool {
        guard phase != .running else { return false }
        switch githubSubmissionPhase {
        case .authorizing, .publishing:
            return false
        case .idle, .completed, .failed:
            return true
        }
    }

    func selectStoredPowerResult(id: UUID) {
        guard canSelectStoredPowerResult,
              id != selectedPowerResultID,
              let stored = storedPowerResults.first(where: { $0.id == id })
        else { return }
        applyStoredPowerResult(
            stored,
            notice: "Selected a validated saved Power result. GitHub submission will reuse its original JSON bytes."
        )
    }

    func submitLatestPowerResultToGitHub() async {
        guard let result = latestPowerResult,
              let resultFileURL,
              acceptsPowerSubmissionDeclarations else { return }
        await refreshCompatibilityPolicy()
        guard selectedResultEligibility.isApproved else { return }
        do {
            guard let clientID = Bundle.main.object(
                forInfoDictionaryKey: "GitHubOAuthClientID"
            ) as? String else {
                throw GitHubSubmissionClient.ClientError.missingClientID
            }
            let client = try GitHubSubmissionClient(clientID: clientID)
            await releasePreparedModelForSubmission()
            let authorization = try await client.startAuthorization()
            githubSubmissionPhase = .authorizing(
                code: authorization.userCode,
                verificationURL: authorization.verificationURL
            )
            let token = try await client.waitForAccessToken(authorization)
            githubSubmissionPhase = .publishing
            let contributor = try await client.authenticatedUser(token: token)
            let package = try PowerSubmissionPackage.make(
                result: result,
                resultURL: resultFileURL,
                githubHandle: contributor,
                conflictCategory: submissionConflictCategory,
                conflictStatement: submissionConflictStatement,
                thermalAssistance: submissionThermalAssistance,
                environmentNotes: submissionEnvironmentNotes
            )
            powerSubmissionPackageURL = try await resultStore.save(package)
            let pullRequestURL = try await client.publish(
                package: package,
                contributor: contributor,
                token: token
            )
            githubSubmissionPhase = .completed(
                pullRequestURL: pullRequestURL
            )
        } catch {
            githubSubmissionPhase = .failed(
                message: error.localizedDescription
            )
        }
    }

    func selectBenchmarkPlan(_ selection: ProductionBenchmarkPlan) {
        guard canSelectBenchmarkPlan,
              loadedPlan?.plan.workload.workloadId != selection.workloadID else {
            return
        }
        resetResultsForPlanSelection()
        do {
            loadedPlan = try PilotPlanLoader.load(
                resource: selection.rawValue,
                modelProfile: selectedModelProfile
            )
            configurationError = nil
        } catch {
            loadedPlan = nil
            configurationError = String(describing: error)
        }
    }

    func selectModelProfile(_ selection: ProductionModelProfile) {
        guard canSelectModelProfile,
              loadedPlan?.plan.modelProfile.artifactId
                != selection.planModelProfile.artifactId else {
            return
        }
        let workload = ProductionBenchmarkPlan.allCases.first {
            $0.workloadID == loadedPlan?.plan.workload.workloadId
        } ?? .sustainedGeneration
        resetResultsForPlanSelection()
        selectedModelProfile = selection
        do {
            loadedPlan = try PilotPlanLoader.load(
                resource: workload.rawValue,
                modelProfile: selection
            )
            configurationError = nil
        } catch {
            loadedPlan = nil
            configurationError = String(describing: error)
        }
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
        if let powerContractError {
            return powerContractError
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
        guard canPrepare else { return }
        await refreshCompatibilityPolicy()
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
        } else if evidence.reasonCodes.contains(
            "restart_required_after_model_switch"
        ) {
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
        let liveEnvironment = DeviceEnvironment.current
        debuggerAttached = DebuggerStatus.isAttached
        lowPowerModeEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled
        buildConfiguration = BuildMetadata.configuration
        currentThermalState = liveEnvironment.thermalState
        batteryState = liveEnvironment.batteryState
        batteryLevelPercent = liveEnvironment.batteryLevelPercent
        guard canRun else { return }
        await refreshCompatibilityPolicy()
        guard canRun,
              let loadedPlan,
              let modelPreparation else { return }
        powerSubmissionPackageURL = nil
        githubSubmissionPhase = .idle
        acceptsPowerSubmissionDeclarations = false
        phase = .running
        currentThermalState = SystemMeasurements.thermalState

        do {
            _ = try PowerBenchmarkRelease.workload(for: loadedPlan.plan)
            let context = PowerExecutionContext(
                plan: loadedPlan.plan,
                environment: try PowerExecutionEnvironmentSnapshot(
                    liveEnvironment
                ),
                modelPreparation: modelPreparation
            )
            let sessionID = UUID()
            let startedAt = Date()
            try await powerCheckpointStore.begin(
                context: context,
                sessionID: sessionID,
                startedAt: startedAt,
                thermalStateAtStart: currentThermalState
            )
            let session = await BenchmarkRunner(
                runtime: runtime,
                procedure: BenchmarkProcedure(
                    warmupRuns: loadedPlan.plan.procedure.warmupRuns,
                    measuredRuns: loadedPlan.plan.procedure.measuredRuns,
                    outputTokenLimit: loadedPlan.plan.workload.outputTokenLimit
                ),
                sessionID: sessionID,
                checkpointStore: powerCheckpointStore
            ).run(prompt: loadedPlan.prompt)
            let failures = session.measuredAttempts.filter { attempt in
                if case .completed = attempt.outcome { return false }
                return true
            }.count
            let bundle = try PowerResultBundle.make(
                session: session,
                context: context
            )
            let savedURL = try await resultStore.save(bundle)
            resultFileURL = savedURL
            try await powerCheckpointStore.clear()
            latestPowerResult = bundle
            recordStoredPowerResult(
                .init(result: bundle, fileURL: savedURL)
            )
            latestUnifiedResult = nil
            submissionFileURL = nil
            result = nil
            uxValidationSummary = nil
            currentThermalState = session.thermalStateAtEnd
            recoveryNotice = nil
            phase = .completed(
                measuredAttempts: session.measuredAttempts.count,
                failedAttempts: failures
            )
        } catch {
            currentThermalState = SystemMeasurements.thermalState
            phase = .failed(message: String(describing: error))
        }
    }

    func recoverInterruptedSessionIfNeeded() async {
        guard phase != .running else { return }
        do {
            guard let recovered = try await powerCheckpointStore
                .recoverInterrupted(thermalState: SystemMeasurements.thermalState)
            else { return }
            let bundle = try PowerResultBundle.make(
                session: recovered.session,
                context: recovered.context
            )
            let savedURL = try await resultStore.save(bundle)
            resultFileURL = savedURL
            try await powerCheckpointStore.clear()
            latestPowerResult = bundle
            recordStoredPowerResult(
                .init(result: bundle, fileURL: savedURL)
            )
            result = nil
            latestUnifiedResult = nil
            recoveryNotice = "Recovered an interrupted Power session without discarding planned attempts."
            let failures = recovered.session.measuredAttempts.filter {
                if case .completed = $0.outcome { return false }
                return true
            }.count
            phase = .completed(
                measuredAttempts: recovered.session.measuredAttempts.count,
                failedAttempts: failures
            )
        } catch {
            recoveryNotice = "Interrupted Power session could not be exported: \(error.localizedDescription)"
        }
    }

    func restoreLatestPowerResultIfNeeded() async {
        guard phase != .running else { return }
        do {
            storedPowerResults = try await resultStore.loadPowerResults()
            guard !storedPowerResults.isEmpty else { return }
            let selected = selectedPowerResultID.flatMap { selectedID in
                storedPowerResults.first(where: { $0.id == selectedID })
            } ?? storedPowerResults[0]
            applyStoredPowerResult(
                selected,
                notice: "Restored \(storedPowerResults.count) validated Power result(s) from local storage. The newest result is selected; choosing another result never rewrites its JSON bytes."
            )
        } catch {
            recoveryNotice = "A saved Power result exists but could not be restored safely: \(error.localizedDescription)"
        }
    }

    func refreshThermalState() {
        let environment = DeviceEnvironment.current
        currentThermalState = SystemMeasurements.thermalState
        debuggerAttached = DebuggerStatus.isAttached
        lowPowerModeEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled
        buildConfiguration = BuildMetadata.configuration
        batteryState = environment.batteryState
        batteryLevelPercent = environment.batteryLevelPercent
    }

    func refreshCompatibilityPolicy() async {
        currentRunnerEligibility = .checking
        do {
            let policy = try await compatibilityPolicyFetcher
                .fetchCurrentPolicy()
            compatibilityPolicy = policy
            guard let plan = loadedPlan?.plan,
                  let identity = PowerRunnerIdentity(plan: plan) else {
                currentRunnerEligibility = .unavailable(
                    message: "This build does not contain a valid runner source identity."
                )
                return
            }
            if let approval = policy.approval(for: identity) {
                currentRunnerEligibility = .approved(
                    policyVersion: policy.policyVersion,
                    approvalID: approval.approvalID
                )
            } else {
                currentRunnerEligibility = .notApproved(
                    policyVersion: policy.policyVersion
                )
            }
        } catch {
            compatibilityPolicy = nil
            currentRunnerEligibility = .unavailable(
                message: error.localizedDescription
            )
        }
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
        refreshThermalState()
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
        refreshThermalState()
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

    var unifiedMeasuredAttemptRecords: [SuiteBResultBundle.Attempt] {
        latestUnifiedResult?.sessions.flatMap(\.attempts).filter {
            $0.role == "measured"
        } ?? []
    }

    var unifiedWarmupAttemptRecords: [SuiteBResultBundle.Attempt] {
        latestUnifiedResult?.sessions.flatMap(\.attempts).filter {
            $0.role == "warmup"
        } ?? []
    }

    private func resetResultsForPlanSelection() {
        phase = .ready
        preparationPhase = .notPrepared
        modelPreparation = nil
        result = nil
        resultFileURL = nil
        uxValidationSummary = nil
        inputLengthCalibrations = []
        inputLengthCalibrationError = nil
        inputSweepResults = []
        inputSweepError = nil
        contextCalibrations = []
        contextCalibrationError = nil
        contextResults = []
        contextRunError = nil
        latestUnifiedResult = nil
        latestPowerResult = nil
        recoveryNotice = nil
        submissionFileURL = nil
        submissionError = nil
        powerSubmissionPackageURL = nil
        githubSubmissionPhase = .idle
        acceptsPowerSubmissionDeclarations = false
        reviewedResult = false
        confirmsNoPersonalData = false
        agreesToRepositoryLicense = false
    }

    private func releasePreparedModelForSubmission() async {
        await runtime.releaseModel()
        modelPreparation = nil
        preparationPhase = .notPrepared
    }

    private func recordStoredPowerResult(
        _ stored: ResultStore.StoredPowerResult
    ) {
        storedPowerResults.removeAll { $0.id == stored.id }
        storedPowerResults.append(stored)
        storedPowerResults.sort {
            if $0.result.createdAt != $1.result.createdAt {
                return $0.result.createdAt > $1.result.createdAt
            }
            return $0.result.resultID.uuidString < $1.result.resultID.uuidString
        }
    }

    private func applyStoredPowerResult(
        _ stored: ResultStore.StoredPowerResult,
        notice: String
    ) {
        latestPowerResult = stored.result
        resultFileURL = stored.fileURL
        latestUnifiedResult = nil
        result = nil
        submissionFileURL = nil
        powerSubmissionPackageURL = nil
        githubSubmissionPhase = .idle
        acceptsPowerSubmissionDeclarations = false
        let measured = stored.result.attempts.filter { $0.role == "measured" }
        phase = .completed(
            measuredAttempts: measured.count,
            failedAttempts: measured.filter { $0.outcome != "completed" }.count
        )
        recoveryNotice = notice
    }

    private static func failureMessage(_ attempt: BenchmarkAttempt) -> String {
        switch attempt.outcome {
        case .completed:
            "The runner stopped before measured attempts."
        case .failed(let message, _):
            message
        case .cancelled(let reason, _), .outOfMemory(let reason, _):
            reason
        case .notRun(let reason):
            reason
        }
    }
}
