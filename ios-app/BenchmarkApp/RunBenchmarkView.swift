import SwiftUI
import UIKit

struct RunBenchmarkView: View {
    private enum Tab: Hashable {
        case test
        case results
    }

    @Environment(\.scenePhase) private var scenePhase
    private let environment = DeviceEnvironment.current
    @Bindable var settings: PowerAppSettings
    @State private var viewModel = BenchmarkViewModel()
    @State private var copiedGitHubCode = false
    @State private var selectedTab: Tab = .test

    var body: some View {
        TabView(selection: $selectedTab) {
            NavigationStack {
                testForm
            }
            .tabItem {
                Label("Test", systemImage: "play.circle.fill")
            }
            .tag(Tab.test)

            NavigationStack {
                resultsForm
            }
            .tabItem {
                Label("Results", systemImage: "tray.full.fill")
            }
            .tag(Tab.results)
        }
        .task {
            viewModel.selectModelProfile(settings.selectedModelProfile)
            viewModel.selectBenchmarkPlan(settings.selectedManualWorkload)
            viewModel.refreshThermalState()
            await viewModel.refreshCompatibilityPolicy()
            await viewModel.recoverInterruptedSessionIfNeeded()
            await viewModel.restoreLatestPowerResultIfNeeded()
        }
        .onChange(of: scenePhase) { _, phase in
            guard phase == .active else { return }
            Task {
                await viewModel.refreshCompatibilityPolicy()
            }
        }
    }

    private var testForm: some View {
        Form {
            currentRunnerEligibilitySection

            Section {
                Picker("Model profile", selection: $settings.selectedModelProfile) {
                    ForEach(ProductionModelProfile.allCases) { profile in
                        Text(profile.title).tag(profile)
                    }
                }
                .disabled(!viewModel.canSelectModelProfile)
                .onChange(of: settings.selectedModelProfile) { _, selection in
                    viewModel.selectModelProfile(selection)
                }
                Picker("Workload", selection: $settings.selectedManualWorkload) {
                    ForEach(ProductionBenchmarkPlan.allCases) { selection in
                        Text(selection.title).tag(selection)
                    }
                }
                .disabled(!viewModel.canSelectBenchmarkPlan)
                .onChange(of: settings.selectedManualWorkload) { _, selection in
                    viewModel.selectBenchmarkPlan(selection)
                }
                LabeledContent("Plan", value: viewModel.loadedPlan?.plan.planId ?? "Unavailable")
                LabeledContent("Profile", value: viewModel.loadedPlan?.plan.workload.v2ProfileMapping ?? "Unavailable")
                LabeledContent("Model", value: modelDescription)
                LabeledContent("Evidence status", value: viewModel.selectedModelProfile.evidenceStatus.rawValue)
                if viewModel.selectedModelProfile.evidenceStatus == .communityEvidence {
                    Text("This artifact has single-contributor community evidence. Another physical-iPhone run adds evidence; reproduction grouping still requires an exact comparison identity.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                LabeledContent("Procedure", value: procedureDescription)
                Text(timingBoundaryDescription)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            } header: {
                Text("Power Benchmark 1.1")
            } footer: {
                Text("Power 1.1 measurement contract · behavior preview v2 draft · App 0.17.0")
            }

            Section {
                if let evidence = viewModel.modelPreparation {
                    LabeledContent("Cache before preparation", value: evidence.cacheStateBeforePreparation.rawValue)
                    LabeledContent("Model load", value: evidence.modelLoadCompleted ? "Completed" : "Not completed")
                } else {
                    Text("The pinned model has not been prepared in this App session.")
                }
                Button("Prepare Model") {
                    Task { await viewModel.prepareModel() }
                }
                .disabled(!viewModel.canPrepare)
            } header: {
                Text("Model Preparation")
            } footer: {
                Text(preparationStatusText)
            }

            Section("This iPhone") {
                LabeledContent("Device", value: environment.deviceDescription)
                LabeledContent("System", value: environment.systemDescription)
                LabeledContent("Thermal state", value: viewModel.currentThermalState)
                LabeledContent("Build", value: viewModel.buildConfiguration)
                LabeledContent("Low Power Mode", value: viewModel.lowPowerModeEnabled ? "On" : "Off")
                LabeledContent("Battery", value: batteryDescription)
            }

            PowerEnvironmentObservationsSection(
                settings: settings,
                resultIDs: viewModel.latestPowerResult.map {
                    [$0.resultID.uuidString.lowercased()]
                } ?? []
            )

            preflightSections

            Section {
                Button("Run Benchmark") {
                    Task { await viewModel.run() }
                }
                .disabled(!viewModel.canRun)
                if viewModel.latestPowerResult != nil {
                    Button("View Saved Result") {
                        selectedTab = .results
                    }
                }
            } footer: {
                Text(viewModel.statusText)
            }

            if let notice = viewModel.recoveryNotice {
                Section("Recovery") {
                    Text(notice)
                }
            }
        }
        .navigationTitle("Test")
        .scrollDismissesKeyboard(.interactively)
        .keyboardDismissToolbar(action: dismissKeyboard)
        .refreshable {
            viewModel.refreshThermalState()
            await viewModel.refreshCompatibilityPolicy()
        }
    }

    private var resultsForm: some View {
        Form {
            if viewModel.storedPowerResults.isEmpty {
                Section {
                    ContentUnavailableView(
                        "No Saved Results",
                        systemImage: "tray",
                        description: Text("Complete a Power test first. Every completed result will be retained here.")
                    )
                }
            } else {
                Section {
                    Picker(
                        "Selected result",
                        selection: Binding<UUID?>(
                            get: { viewModel.selectedPowerResultID },
                            set: { selectedID in
                                if let selectedID {
                                    viewModel.selectStoredPowerResult(id: selectedID)
                                }
                            }
                        )
                    ) {
                        ForEach(viewModel.storedPowerResults, id: \.id) { stored in
                            Text(storedPowerResultLabel(stored)).tag(Optional(stored.id))
                        }
                    }
                    .disabled(!viewModel.canSelectStoredPowerResult)
                    if let selected = viewModel.latestPowerResult {
                        LabeledContent("Result ID", value: selected.resultID.uuidString.lowercased())
                        LabeledContent("Runner", value: "App \(selected.execution.appVersion) (\(selected.execution.appBuild))")
                    }
                } header: {
                    Text("Saved Power Results")
                } footer: {
                    Text("Selecting a result changes only what is displayed, shared, or submitted. Frozen JSON is never recalculated or rewritten.")
                }
            }

            selectedResultEligibilitySection

            if let result = viewModel.latestPowerResult {
                let metrics = result.summary.metrics
                Section("Selected Power Result · Median") {
                    LabeledContent("Pipeline TTFT", value: viewModel.metricText(metrics.medianPipelineTTFTMilliseconds, unit: "ms"))
                    LabeledContent("First-renderable proxy TTFT", value: viewModel.metricText(metrics.medianFirstRenderableProxyTTFTMilliseconds, unit: "ms"))
                    LabeledContent("Request completion", value: viewModel.metricText(metrics.medianRequestCompletionMilliseconds, unit: "ms"))
                    LabeledContent("Prefill", value: viewModel.metricText(metrics.medianPrefillTokensPerSecond, unit: "tok/s"))
                    LabeledContent("Decode", value: viewModel.metricText(metrics.medianDecodeTokensPerSecond, unit: "tok/s"))
                    LabeledContent("Process footprint", value: viewModel.metricText(metrics.medianProcessPhysicalFootprintMiB, unit: "MiB"))
                    LabeledContent("Decode first → last", value: viewModel.percentText(metrics.decodeFirstToLastPercentChange))
                }

                Section("Attempt Evidence") {
                    ForEach(result.attempts, id: \.runIndex) { attempt in
                        DisclosureGroup("\(attempt.role.capitalized) \(attempt.runIndex) · \(attempt.outcome)") {
                            powerAttemptDetails(attempt)
                        }
                    }
                }
            }

            if let resultFileURL = viewModel.resultFileURL {
                Section {
                    LabeledContent("Selected result file", value: resultFileURL.lastPathComponent)
                    ShareLink(item: resultFileURL) {
                        Label("Share Raw Power JSON", systemImage: "square.and.arrow.up")
                    }
                } header: {
                    Text("Result delivery")
                } footer: {
                    Text("The same frozen file is shared; neither this view nor GitHub submission recalculates or rewrites it.")
                }

                githubContributionSection
            }
        }
        .navigationTitle("Results")
        .scrollDismissesKeyboard(.interactively)
        .keyboardDismissToolbar(action: dismissKeyboard)
        .refreshable {
            await viewModel.refreshCompatibilityPolicy()
        }
    }

    @ViewBuilder
    private var currentRunnerEligibilitySection: some View {
        Section("Runner eligibility") {
            switch viewModel.currentRunnerEligibility {
            case .checking:
                HStack {
                    ProgressView()
                    Text("Checking current Power policy…")
                }
            case .approved(let policyVersion, let approvalID):
                Label("Approved for Power \(policyVersion)", systemImage: "checkmark.shield.fill")
                    .foregroundStyle(.green)
                Text(approvalID)
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)
            case .notApproved(let policyVersion):
                Label("Update required", systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                Text("This exact App build is not approved by Power policy \(policyVersion). Model preparation and measurement are disabled.")
                Link(
                    "Open iOS App update instructions",
                    destination: URL(
                        string: "https://github.com/YizeSun/iOS-LLM-Leaderboard/tree/main/ios-app"
                    )!
                )
            case .unavailable(let message):
                Label("Unable to verify eligibility", systemImage: "wifi.exclamationmark")
                    .foregroundStyle(.orange)
                Text(message)
                Button("Retry Check") {
                    Task { await viewModel.refreshCompatibilityPolicy() }
                }
            case .noResult:
                EmptyView()
            }
        }
    }

    @ViewBuilder
    private var selectedResultEligibilitySection: some View {
        if viewModel.latestPowerResult != nil {
            Section("Submission eligibility") {
                switch viewModel.selectedResultEligibility {
                case .checking:
                    HStack {
                        ProgressView()
                        Text("Checking selected result…")
                    }
                case .approved(let policyVersion, let approvalID):
                    Label("Eligible under Power \(policyVersion)", systemImage: "checkmark.shield.fill")
                        .foregroundStyle(.green)
                    Text(approvalID)
                        .font(.caption.monospaced())
                        .foregroundStyle(.secondary)
                case .notApproved(let policyVersion):
                    Label("Result not eligible", systemImage: "xmark.shield.fill")
                        .foregroundStyle(.red)
                    Text("The selected result's exact runner and runtime identity is not approved by Power policy \(policyVersion). It remains available for inspection and raw export, but cannot be submitted.")
                case .unavailable(let message):
                    Label("Unable to verify result", systemImage: "wifi.exclamationmark")
                        .foregroundStyle(.orange)
                    Text(message)
                    Button("Retry Check") {
                        Task { await viewModel.refreshCompatibilityPolicy() }
                    }
                case .noResult:
                    EmptyView()
                }
            }
        }
    }

    @ViewBuilder
    private var preflightSections: some View {
        if viewModel.debuggerAttached {
            Section("Preflight") {
                Label("LLDB is attached. Benchmark measurements are disabled.", systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                Text("Open Product → Scheme → Edit Scheme → Run → Info and turn off Debug executable, then run the app again.")
            }
        }

        if !viewModel.debuggerAttached && viewModel.buildConfiguration != "Release" {
            Section("Preflight") {
                Label("Use a Release build before measuring.", systemImage: "hammer.fill")
                    .foregroundStyle(.orange)
            }
        }

        if !viewModel.debuggerAttached
            && viewModel.buildConfiguration == "Release"
            && viewModel.lowPowerModeEnabled {
            Section("Preflight") {
                Label("Turn off Low Power Mode before measuring.", systemImage: "battery.25percent")
                    .foregroundStyle(.orange)
            }
        }

        if !viewModel.debuggerAttached
            && viewModel.buildConfiguration == "Release"
            && !viewModel.lowPowerModeEnabled
            && viewModel.currentThermalState != "nominal" {
            Section("Preflight") {
                Label("Wait for the iPhone to cool to nominal before starting.", systemImage: "thermometer.high")
                    .foregroundStyle(.orange)
                Text("Pull down to refresh the system-reported thermal state.")
            }
        }
    }

    private var githubContributionSection: some View {
        Section {
            Picker("Conflict of interest", selection: $viewModel.submissionConflictCategory) {
                ForEach(SubmissionConflictCategory.allCases) { category in
                    Text(category.title).tag(category)
                }
            }
            if viewModel.submissionConflictCategory != .none {
                TextField("Disclosure statement", text: $viewModel.submissionConflictStatement, axis: .vertical)
            }
            Picker("Thermal assistance", selection: $viewModel.submissionThermalAssistance) {
                ForEach(SubmissionThermalAssistance.allCases) { assistance in
                    Text(assistance.title).tag(assistance)
                }
            }
            TextField("Optional environment notes", text: $viewModel.submissionEnvironmentNotes, axis: .vertical)
            Toggle(
                "I ran this on a physical device, reviewed the public metadata, confirm the raw result is unmodified and contains no personal data, accept CC BY 4.0, and understand that submission does not guarantee ranking.",
                isOn: $viewModel.acceptsPowerSubmissionDeclarations
            )
            Button {
                dismissKeyboard()
                Task { await viewModel.submitLatestPowerResultToGitHub() }
            } label: {
                Label("Submit to GitHub", systemImage: "arrow.up.circle.fill")
            }
            .disabled(!viewModel.canSubmitLatestPowerResultToGitHub)

            githubSubmissionStatus

            if let packageURL = viewModel.powerSubmissionPackageURL {
                ShareLink(item: packageURL) {
                    Label("Share Two-file Package", systemImage: "square.and.arrow.up")
                }
            }
            if !viewModel.githubSubmissionConfigured {
                Label(
                    "Direct submission is unavailable because this build has no GitHub OAuth Client ID.",
                    systemImage: "exclamationmark.triangle"
                )
                .foregroundStyle(.orange)
                Link(
                    "Open contributor guide",
                    destination: URL(
                        string: "https://github.com/YizeSun/iOS-LLM-Leaderboard/blob/main/contributor-kit/power-1.1-quickstart.md"
                    )!
                )
            }
        } header: {
            Text("GitHub contribution")
        } footer: {
            Text("The App creates the current Power 1.1 two-file package, preserves result.json byte-for-byte, commits it to your fork, and opens a pull request. Repository CI makes the authoritative accept, manual-review, or reject decision.")
        }
    }

    private func dismissKeyboard() {
        UIApplication.shared.sendAction(
            #selector(UIResponder.resignFirstResponder),
            to: nil,
            from: nil,
            for: nil
        )
    }

    @ViewBuilder
    private var githubSubmissionStatus: some View {
        switch viewModel.githubSubmissionPhase {
        case .idle:
            EmptyView()
        case .authorizing(let code, let verificationURL):
            VStack(alignment: .leading, spacing: 8) {
                Text("GitHub code")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(code)
                    .font(.headline.monospaced())
                    .textSelection(.enabled)
                    .accessibilityLabel("GitHub authorization code \(code)")
            }
            Button {
                copyGitHubCode(code)
            } label: {
                Label(
                    copiedGitHubCode ? "Code copied" : "Copy code",
                    systemImage: copiedGitHubCode
                        ? "checkmark.circle.fill"
                        : "doc.on.doc"
                )
            }
            Link(destination: verificationURL) {
                Label("Authorize on GitHub", systemImage: "safari")
            }
            Text("The model was released before authorization to reduce memory pressure. Return to the App after authorizing; if iOS relaunches it, the saved result will be restored and you can start a fresh authorization.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        case .publishing:
            HStack {
                ProgressView()
                Text("Creating fork, evidence commit, and pull request…")
            }
        case .completed(let pullRequestURL):
            Label("Pull request created", systemImage: "checkmark.circle.fill")
                .foregroundStyle(.green)
            Link("Open pull request", destination: pullRequestURL)
            Text("Choose another saved result above to submit it. To run a new test, prepare the model again, then tap Run Benchmark; the new result will be saved and selected automatically.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        case .failed(let message):
            Label(message, systemImage: "xmark.circle.fill")
                .foregroundStyle(.red)
        }
    }

    private func copyGitHubCode(_ code: String) {
        UIPasteboard.general.string = code
        copiedGitHubCode = true
        Task {
            try? await Task.sleep(for: .seconds(2))
            copiedGitHubCode = false
        }
    }

    private func storedPowerResultLabel(
        _ stored: ResultStore.StoredPowerResult
    ) -> String {
        let result = stored.result
        return "\(result.createdAt.formatted(date: .abbreviated, time: .shortened)) · \(result.model.displayName) · \(result.execution.workloadID)"
    }

    private var batteryDescription: String {
        let state = viewModel.batteryState
        guard let level = viewModel.batteryLevelPercent else { return state }
        return "\(level.formatted(.number.precision(.fractionLength(0))))% · \(state)"
    }

    private var modelDescription: String {
        guard let model = viewModel.loadedPlan?.plan.modelProfile else {
            return "Unavailable"
        }
        return "\(model.displayName) · \(model.quantization)"
    }

    private var procedureDescription: String {
        guard let plan = viewModel.loadedPlan?.plan else {
            return "Unavailable"
        }
        return "\(plan.procedure.warmupRuns) warm-up + \(plan.procedure.measuredRuns) measured"
    }

    private var timingBoundaryDescription: String {
        guard let plan = viewModel.loadedPlan?.plan else {
            return "Timing boundary unavailable."
        }
        if plan.measurementMode.userVisibleTtftAvailable {
            return "First-renderable proxy TTFT is measured inside the adapter from bounded decode evidence, not at the screen. Pipeline TTFT remains a separate boundary."
        }
        return "This pipeline workload reports Pipeline TTFT after chat-template application and tokenization. User-visible TTFT is unavailable and is never inferred from Pipeline TTFT."
    }

    private var preparationStatusText: String {
        switch viewModel.preparationPhase {
        case .notPrepared:
            "Checks the exact artifact revision, downloads if needed, and loads the model without running inference."
        case .preparing:
            "Preparing the pinned model…"
        case .ready:
            "Verified cached model loaded."
        case .restartRequired:
            "Model downloaded — restart required before measuring."
        case .blocked(let message), .failed(let message):
            message
        }
    }

    @ViewBuilder
    private func powerAttemptDetails(_ attempt: PowerResultBundle.Attempt) -> some View {
        let metrics = attempt.derivedMetrics
        LabeledContent("Pipeline TTFT", value: viewModel.metricText(metrics.pipelineTTFTMilliseconds, unit: "ms"))
        LabeledContent("First-renderable proxy TTFT", value: viewModel.metricText(metrics.firstRenderableProxyTTFTMilliseconds, unit: "ms"))
        LabeledContent("Request completion", value: viewModel.metricText(metrics.requestCompletionMilliseconds, unit: "ms"))
        LabeledContent("Prefill", value: viewModel.metricText(metrics.prefillTokensPerSecond, unit: "tok/s"))
        LabeledContent("Decode", value: viewModel.metricText(metrics.decodeTokensPerSecond, unit: "tok/s"))
        LabeledContent("Process footprint", value: viewModel.metricText(metrics.processPhysicalFootprintMiB, unit: "MiB"))
        LabeledContent(
            "Tokens",
            value: "\(attempt.promptTokenCount.map(String.init) ?? "—") → \(attempt.outputTokenCount.map(String.init) ?? "—")"
        )
        LabeledContent(
            "Thermal",
            value: "\(attempt.thermal.before) → \(attempt.thermal.after)"
        )
        LabeledContent("Memory samples", value: String(attempt.memorySamples.count))
        LabeledContent("Token events", value: String(attempt.tokenEvents.count))
        LabeledContent("Response contract", value: attempt.responseConformance.status)
        LabeledContent("Stop reason", value: attempt.stopReason ?? "Unavailable")
        if !attempt.reasonCodes.isEmpty {
            Text(attempt.reasonCodes.joined(separator: ", "))
                .foregroundStyle(.red)
                .textSelection(.enabled)
        }
    }

    @ViewBuilder
    private func attemptDetails(_ attempt: PilotResultBundle.Attempt) -> some View {
        LabeledContent("Pipeline TTFT", value: viewModel.metricText(
            attempt.metrics.ttftMilliseconds,
            unit: "ms"
        ))
        LabeledContent("Prefill", value: viewModel.metricText(
            attempt.metrics.prefillTokensPerSecond,
            unit: "tok/s"
        ))
        LabeledContent("Decode", value: viewModel.metricText(
            attempt.metrics.decodeTokensPerSecond,
            unit: "tok/s"
        ))
        LabeledContent("Memory peak", value: viewModel.metricText(
            attempt.metrics.peakMemoryMegabytes,
            unit: "MiB"
        ))
        LabeledContent("Token interval p50", value: viewModel.metricText(
            attempt.metrics.p50TokenIntervalMilliseconds,
            unit: "ms"
        ))
        LabeledContent("Token interval p95", value: viewModel.metricText(
            attempt.metrics.p95TokenIntervalMilliseconds,
            unit: "ms"
        ))
        LabeledContent("Token interval p99", value: viewModel.metricText(
            attempt.metrics.p99TokenIntervalMilliseconds,
            unit: "ms"
        ))
        LabeledContent(
            "Tokens",
            value: "\(attempt.promptTokenCount ?? 0) → \(attempt.outputTokenCount ?? 0)"
        )
        LabeledContent(
            "Thermal",
            value: "\(attempt.thermalStateBefore) → \(attempt.thermalStateAfter)"
        )
        LabeledContent("Stop reason", value: attempt.stopReason ?? "Unavailable")
        if let error = attempt.errorMessage {
            Text(error)
                .foregroundStyle(.red)
        }
    }


    @ViewBuilder
    private func unifiedAttemptDetails(_ attempt: SuiteBResultBundle.Attempt) -> some View {
        LabeledContent("Pipeline TTFT", value: viewModel.metricText(
            attempt.metrics.ttftMilliseconds,
            unit: "ms"
        ))
        LabeledContent("First-renderable proxy TTFT", value: viewModel.metricText(
            attempt.metrics.userVisibleTTFTMilliseconds,
            unit: "ms"
        ))
        LabeledContent("Request completion", value: viewModel.metricText(
            attempt.metrics.requestCompletionMilliseconds,
            unit: "ms"
        ))
        LabeledContent("Prefill", value: viewModel.metricText(
            attempt.metrics.prefillTokensPerSecond,
            unit: "tok/s"
        ))
        LabeledContent("Decode", value: viewModel.metricText(
            attempt.metrics.decodeTokensPerSecond,
            unit: "tok/s"
        ))
        LabeledContent("Memory peak", value: viewModel.metricText(
            attempt.metrics.peakMemoryMegabytes,
            unit: "MiB"
        ))
        LabeledContent(
            "Tokens",
            value: "\(attempt.promptTokenCount ?? 0) → \(attempt.outputTokenCount ?? 0)"
        )
        LabeledContent(
            "Thermal",
            value: "\(attempt.thermalStateBefore) → \(attempt.thermalStateAfter)"
        )
        LabeledContent("Stop reason", value: attempt.stopReason ?? "Unavailable")
        if let error = attempt.errorMessage {
            Text(error)
                .foregroundStyle(.red)
        }
    }
}

private extension View {
    func keyboardDismissToolbar(action: @escaping () -> Void) -> some View {
        toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("Done", action: action)
            }
        }
    }
}

#Preview {
    RunBenchmarkView(settings: PowerAppSettings())
}
