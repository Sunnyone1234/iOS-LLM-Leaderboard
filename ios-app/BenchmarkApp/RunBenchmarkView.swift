import SwiftUI

struct RunBenchmarkView: View {
    private let environment = DeviceEnvironment.current
    @State private var viewModel = BenchmarkViewModel()

    var body: some View {
        NavigationStack {
            Form {
                Section("Benchmark") {
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
                    LabeledContent("Procedure", value: procedureDescription)
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

                if let summary = viewModel.result?.summary {
                    Section("Latest Result · Median") {
                        LabeledContent(
                            "Pipeline TTFT",
                            value: viewModel.metricText(
                                summary.medianTTFTMilliseconds,
                                unit: "ms"
                            )
                        )
                        LabeledContent(
                            "Prefill",
                            value: viewModel.metricText(
                                summary.medianPrefillTokensPerSecond,
                                unit: "tok/s"
                            )
                        )
                        LabeledContent(
                            "Decode",
                            value: viewModel.metricText(
                                summary.medianDecodeTokensPerSecond,
                                unit: "tok/s"
                            )
                        )
                        LabeledContent(
                            "Process memory peak",
                            value: viewModel.metricText(
                                summary.medianPeakMemoryMegabytes,
                                unit: "MiB"
                            )
                        )
                        LabeledContent("Final thermal", value: summary.finalThermalState)
                    }

                    Section("Performance Degradation · First → Last") {
                        LabeledContent(
                            "Decode",
                            value: viewModel.percentText(
                                summary.degradation.decodePercentChange
                            )
                        )
                        LabeledContent(
                            "Pipeline TTFT",
                            value: viewModel.percentText(
                                summary.degradation.ttftPercentChange
                            )
                        )
                        LabeledContent(
                            "Prefill",
                            value: viewModel.percentText(
                                summary.degradation.prefillPercentChange
                            )
                        )
                    }
                }

                if !viewModel.measuredAttemptRecords.isEmpty {
                    Section("Measured Runs") {
                        ForEach(
                            Array(viewModel.measuredAttemptRecords.enumerated()),
                            id: \.offset
                        ) { offset, attempt in
                            DisclosureGroup("Run \(offset + 1) · \(attempt.outcome)") {
                                attemptDetails(attempt)
                            }
                        }
                    }
                }

                if let warmup = viewModel.warmupAttemptRecord {
                    Section("Evidence") {
                        DisclosureGroup("Warm-up · excluded from summary") {
                            attemptDetails(warmup)
                        }
                    }
                }

                if let resultFileURL = viewModel.resultFileURL {
                    Section {
                        ShareLink(item: resultFileURL) {
                            Label("Export Raw JSON", systemImage: "square.and.arrow.up")
                        }
                    } footer: {
                        Text("Non-official pilot evidence. Review before sharing.")
                    }
                }
            }
            .navigationTitle("Run Benchmark")
            .refreshable {
                viewModel.refreshThermalState()
            }
            .task {
                viewModel.refreshThermalState()
            }
        }
    }

    private var batteryDescription: String {
        let state = environment.batteryState
        guard let level = environment.batteryLevelPercent else { return state }
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
}

#Preview {
    RunBenchmarkView()
}
