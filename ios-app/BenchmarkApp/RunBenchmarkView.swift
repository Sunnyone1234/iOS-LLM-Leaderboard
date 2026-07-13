import SwiftUI

struct RunBenchmarkView: View {
    private let environment = DeviceEnvironment.current
    @State private var selectedPlan = ProductionBenchmarkPlan.sustainedGeneration
    @State private var selectedModelProfile = ProductionModelProfile.small
    @State private var viewModel = BenchmarkViewModel()

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Picker("Model profile", selection: $selectedModelProfile) {
                        ForEach(ProductionModelProfile.allCases) { profile in
                            Text(profile.title).tag(profile)
                        }
                    }
                    .disabled(!viewModel.canSelectModelProfile)
                    .onChange(of: selectedModelProfile) { _, selection in
                        viewModel.selectModelProfile(selection)
                    }
                    Picker("Workload", selection: $selectedPlan) {
                        ForEach(ProductionBenchmarkPlan.allCases) { selection in
                            Text(selection.title).tag(selection)
                        }
                    }
                    .disabled(!viewModel.canSelectBenchmarkPlan)
                    .onChange(of: selectedPlan) { _, selection in
                        viewModel.selectBenchmarkPlan(selection)
                    }
                    LabeledContent(
                        "Plan",
                        value: viewModel.loadedPlan?.plan.planId
                            ?? "Unavailable"
                    )
                    LabeledContent(
                        "Profile",
                        value: viewModel.loadedPlan?.plan.workload.v2ProfileMapping
                            ?? "Unavailable"
                    )
                    LabeledContent("Model", value: modelDescription)
                    LabeledContent(
                        "Evidence status",
                        value: viewModel.selectedModelProfile.evidenceStatus.rawValue
                    )
                    if viewModel.selectedModelProfile.evidenceStatus
                        == .untestedCandidate {
                        Text("This artifact is recommended for testing but has no accepted physical-iPhone evidence yet. It is not a leaderboard result.")
                            .font(.footnote)
                            .foregroundStyle(.orange)
                    }
                    LabeledContent("Procedure", value: procedureDescription)
                    Text(timingBoundaryDescription)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                } header: {
                    Text("Power Benchmark 1.0 · Reference App")
                } footer: {
                    Text("Adopted RC1 result contract · Reference App 0.9.0")
                }

                Section {
                    if let evidence = viewModel.modelPreparation {
                        LabeledContent(
                            "Cache before preparation",
                            value: evidence.cacheStateBeforePreparation.rawValue
                        )
                        LabeledContent(
                            "Model load",
                            value: evidence.modelLoadCompleted ? "Completed" : "Not completed"
                        )
                    } else {
                        Text("The pinned model has not been prepared in this App session.")
                    }
                    Button("Prepare Model") {
                        Task {
                            await viewModel.prepareModel()
                        }
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
                    LabeledContent(
                        "Low Power Mode",
                        value: viewModel.lowPowerModeEnabled ? "On" : "Off"
                    )
                    LabeledContent("Battery", value: batteryDescription)
                }

                if viewModel.debuggerAttached {
                    Section("Preflight") {
                        Label(
                            "LLDB is attached. Benchmark measurements are disabled.",
                            systemImage: "exclamationmark.triangle.fill"
                        )
                        .foregroundStyle(.orange)
                        Text("Open Product → Scheme → Edit Scheme → Run → Info and turn off Debug executable, then run the app again.")
                    }
                }

                if !viewModel.debuggerAttached
                    && viewModel.buildConfiguration != "Release" {
                    Section("Preflight") {
                        Label(
                            "Use a Release build before measuring.",
                            systemImage: "hammer.fill"
                        )
                        .foregroundStyle(.orange)
                    }
                }

                if !viewModel.debuggerAttached
                    && viewModel.buildConfiguration == "Release"
                    && viewModel.lowPowerModeEnabled {
                    Section("Preflight") {
                        Label(
                            "Turn off Low Power Mode before measuring.",
                            systemImage: "battery.25percent"
                        )
                        .foregroundStyle(.orange)
                    }
                }

                if !viewModel.debuggerAttached
                    && viewModel.buildConfiguration == "Release"
                    && !viewModel.lowPowerModeEnabled
                    && viewModel.currentThermalState != "nominal" {
                    Section("Preflight") {
                        Label(
                            "Wait for the iPhone to cool to nominal before starting.",
                            systemImage: "thermometer.high"
                        )
                        .foregroundStyle(.orange)
                        Text("Pull down to refresh the system-reported thermal state.")
                    }
                }

                Section {
                    Button("Run Benchmark") {
                        Task {
                            await viewModel.run()
                        }
                    }
                    .disabled(!viewModel.canRun)
                } footer: {
                    Text(viewModel.statusText)
                }

                if let notice = viewModel.recoveryNotice {
                    Section("Recovery") {
                        Text(notice)
                    }
                }

                if let result = viewModel.latestPowerResult {
                    let metrics = result.summary.metrics
                    Section("Latest Power Result · Median") {
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
                        ShareLink(item: resultFileURL) {
                            Label("Export Raw JSON", systemImage: "square.and.arrow.up")
                        }
                    } footer: {
                        Text("Frozen Power result contract. Candidate profiles remain unranked until physical evidence is accepted.")
                    }
                }

                if viewModel.latestUnifiedResult != nil {
                    Section {
                        TextField("GitHub handle or public name", text: $viewModel.contributorName)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                        Toggle("I reviewed the result and raw evidence", isOn: $viewModel.reviewedResult)
                        Toggle("This submission contains no personal data", isOn: $viewModel.confirmsNoPersonalData)
                        Toggle("I agree to the repository license", isOn: $viewModel.agreesToRepositoryLicense)
                        Button("Generate Repository Submission") {
                            Task { await viewModel.generateCommunitySubmission() }
                        }
                        .disabled(!viewModel.canGenerateSubmission)
                        if let error = viewModel.submissionError {
                            Text(error).foregroundStyle(.red)
                        }
                        if let url = viewModel.submissionFileURL {
                            ShareLink(item: url) {
                                Label("Export Submission JSON", systemImage: "shippingbox.and.arrow.backward")
                            }
                        }
                    } header: {
                        Text("Legacy Draft Submission")
                    } footer: {
                        Text("Legacy Draft submission export; it is not required by the Pilot v0.1 ingestion path. Pilot data uses the unmodified raw result JSON.")
                    }
                }
            }
            .navigationTitle("Run Benchmark")
            .refreshable {
                viewModel.refreshThermalState()
            }
            .task {
                viewModel.refreshThermalState()
                await viewModel.recoverInterruptedSessionIfNeeded()
            }
        }
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

#Preview {
    RunBenchmarkView()
}
