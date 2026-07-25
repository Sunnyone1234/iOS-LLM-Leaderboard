import PowerGitHubSubmission
import PowerResultsStore
import PowerSubmissionKit
import SwiftUI
import UIKit

struct PowerResultsView: View {
    @Bindable var model: PowerAppModel
    @FocusState private var notesFocused: Bool
    @State private var copiedAuthorizationCode = false

    var body: some View {
        List {
            if model.isLoadingResults {
                ProgressView("Loading saved Power 2 results…")
            } else if let error = model.resultLoadError {
                ContentUnavailableView(
                    "Results unavailable",
                    systemImage: "exclamationmark.triangle",
                    description: Text(error)
                )
            } else if model.results.isEmpty {
                ContentUnavailableView(
                    "No Power 2 results",
                    systemImage: "tray",
                    description: Text(
                        "Completed Power 2 tests will appear here. "
                            + "Power 1.1 files are not imported or converted."
                    )
                )
            } else {
                Section("Saved results") {
                    ForEach(model.results) { result in
                        Button {
                            model.selectResult(result.id)
                        } label: {
                            ResultRow(
                                result: result,
                                isSelected:
                                    result.id == model.selectedResult?.id
                            )
                        }
                        .buttonStyle(.plain)
                        .disabled(!model.canSelectResult)
                    }
                }

                if let selected = model.selectedResult {
                    Section {
                        LabeledContent(
                            "SHA-256",
                            value: abbreviated(selected.sha256)
                        )
                        LabeledContent(
                            "Bytes",
                            value: selected.byteCount.formatted()
                        )
                        ShareLink(item: selected.fileURL) {
                            Label(
                                "Share raw evidence",
                                systemImage: "square.and.arrow.up"
                            )
                        }
                    } header: {
                        Text("Selected result")
                    } footer: {
                        Text(
                            "The Results Store and submission package preserve "
                                + "the selected file byte-for-byte. GitHub "
                                + "submission accepts only evidence declaring "
                                + "the current supported App release identity."
                        )
                    }

                    githubContributionSection
                }
            }
        }
        .navigationTitle("Results")
        .scrollDismissesKeyboard(.interactively)
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("Done") {
                    notesFocused = false
                }
            }
        }
        .refreshable {
            await model.refreshReleaseEligibility()
            await model.reloadResults()
        }
    }

    @ViewBuilder
    private var githubContributionSection: some View {
        Section("GitHub contribution") {
            Picker(
                "Conflict of interest",
                selection: $model.submissionConflict
            ) {
                ForEach(PowerSubmissionConflict.allCases, id: \.self) {
                    conflict in
                    Text(conflictLabel(conflict)).tag(conflict)
                }
            }
            if model.submissionConflict == .disclosed {
                TextField(
                    "Disclosure statement",
                    text: $model.submissionDisclosure,
                    axis: .vertical
                )
                .focused($notesFocused)
            }
            TextField(
                "Optional environment notes",
                text: $model.submissionEnvironmentNotes,
                axis: .vertical
            )
            .focused($notesFocused)
            Toggle(
                "I ran this on a physical device, reviewed the public "
                    + "metadata, confirm the raw evidence is unmodified "
                    + "and contains no personal data, accept CC BY 4.0, "
                    + "and understand that submission does not guarantee "
                    + "ranking.",
                isOn: $model.acceptsSubmissionDeclarations
            )
            Button {
                notesFocused = false
                model.submitSelectedResult()
            } label: {
                Label(
                    "Submit to GitHub",
                    systemImage: "arrow.up.circle.fill"
                )
            }
            .disabled(!model.canSubmitSelectedResult)

            submissionStatus

            if model.submissionAvailable {
                Label(
                    "This source-built App self-declares its release identity. "
                        + "Trusted repository CI checks the declaration and "
                        + "evidence contract; it does not attest the local "
                        + "binary. One eligible contributor is Accepted, and "
                        + "independent reproduction raises confidence.",
                    systemImage: "info.circle"
                )
                .foregroundStyle(.secondary)
            }
            if !model.submissionAvailable {
                Label(
                    submissionUnavailableReason,
                    systemImage: "lock.shield"
                )
                .foregroundStyle(.orange)
            } else if !model.selectedResultMatchesCurrentRelease {
                Label(
                    "This saved result came from a different App release. "
                        + "Run a new test with the current Official build "
                        + "before submitting.",
                    systemImage: "arrow.triangle.2.circlepath"
                )
                .foregroundStyle(.orange)
            } else if !model.githubSubmissionConfigured {
                Label(
                    "This build has no GitHub OAuth Client ID.",
                    systemImage: "exclamationmark.triangle"
                )
                .foregroundStyle(.orange)
            }
        }
    }

    private var submissionUnavailableReason: String {
        if model.releaseEligibility == .releaseCandidate {
            return "This is a closed Official App release rehearsal. Its "
                + "result must be reviewed by a maintainer and cannot be "
                + "submitted to public intake or ranking."
        }
        return model.measurementLockReason
            ?? "Submission requires the current Official source "
            + "configuration and a confirmed remote release. Repository "
            + "CI remains the acceptance authority."
    }

    @ViewBuilder
    private var submissionStatus: some View {
        switch model.submissionState {
        case .idle:
            EmptyView()
        case .authorizing(let authorization):
            VStack(alignment: .leading, spacing: 8) {
                Text("GitHub code")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(authorization.userCode)
                    .font(.headline.monospaced())
                    .textSelection(.enabled)
            }
            Button {
                UIPasteboard.general.string = authorization.userCode
                copiedAuthorizationCode = true
                Task {
                    try? await Task.sleep(for: .seconds(2))
                    copiedAuthorizationCode = false
                }
            } label: {
                Label(
                    copiedAuthorizationCode
                        ? "Code copied"
                        : "Copy code",
                    systemImage: copiedAuthorizationCode
                        ? "checkmark.circle.fill"
                        : "doc.on.doc"
                )
            }
            Link(destination: authorization.verificationURL) {
                Label("Authorize on GitHub", systemImage: "safari")
            }
            Text(
                "Return to the App after authorization. If iOS relaunches "
                    + "the App, the saved result remains available and you "
                    + "can start authorization again."
            )
            .font(.footnote)
            .foregroundStyle(.secondary)
        case .publishing:
            HStack {
                ProgressView()
                Text("Creating fork, evidence commit, and pull request…")
            }
        case .completed(let pullRequestURL):
            Label(
                "Pull request created",
                systemImage: "checkmark.circle.fill"
            )
            .foregroundStyle(.green)
            Link("Open pull request", destination: pullRequestURL)
        case .failed(let message):
            Label(message, systemImage: "xmark.circle.fill")
                .foregroundStyle(.red)
        }
    }

    private func conflictLabel(
        _ conflict: PowerSubmissionConflict
    ) -> String {
        switch conflict {
        case .none:
            "None"
        case .disclosed:
            "Disclosed"
        }
    }

    private func abbreviated(_ digest: String) -> String {
        "\(digest.prefix(12))…\(digest.suffix(8))"
    }
}

private struct ResultRow: View {
    let result: StoredPowerResult
    let isSelected: Bool

    var body: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text(result.workloadID)
                    .font(.headline)
                Text(result.modelArtifactID)
                    .font(.subheadline)
                Text(result.createdAt)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            if isSelected {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.tint)
                    .accessibilityLabel("Selected")
            }
        }
        .contentShape(Rectangle())
    }
}
