import Foundation
import XCTest
@testable import BenchmarkApp

private struct StaticPowerPolicyFetcher: PowerCompatibilityPolicyFetching {
    let policy: PowerCompatibilityPolicy?

    func fetchCurrentPolicy() async throws -> PowerCompatibilityPolicy {
        guard let policy else { throw PowerCompatibilityPolicyError.unavailable }
        return policy
    }
}

final class PowerReferenceAppTests: XCTestCase {
    func testBuiltAppEmbedsExactSourceCommit() throws {
        let sourceCommit = try XCTUnwrap(BuildMetadata.sourceCommit)
        XCTAssertTrue(PowerBenchmarkRelease.isSourceCommit(sourceCommit))
    }

    func testBundledPlansMatchFrozenPowerRelease() throws {
        for selection in ProductionBenchmarkPlan.allCases {
            let loaded = try PilotPlanLoader.load(resource: selection.rawValue)
            let workload = try PowerBenchmarkRelease.workload(for: loaded.plan)
            XCTAssertEqual(workload.id, selection.workloadID)
            XCTAssertEqual(loaded.plan.workload.workloadVersion, "1.1.0-rc.1")
        }
    }

    func testPowerEncodingRetainsRequiredNullFields() throws {
        let result = try fixtureResult()
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let encodedResult = try encoder.encode(result)
        let attachment = XCTAttachment(
            data: encodedResult,
            uniformTypeIdentifier: "public.json"
        )
        attachment.name = "power-result-fixture.json"
        attachment.lifetime = .keepAlways
        add(attachment)
        let object = try XCTUnwrap(
            JSONSerialization.jsonObject(with: encodedResult)
                as? [String: Any]
        )
        XCTAssertEqual(
            object["schemaVersion"] as? String,
            "suite-b-power-result-1.1.0-rc.1"
        )
        let configuration = try XCTUnwrap(
            object["configuration"] as? [String: Any]
        )
        XCTAssertTrue(configuration["topP"] is NSNull)
        XCTAssertTrue(configuration["topK"] is NSNull)
        XCTAssertTrue(configuration["seed"] is NSNull)
        XCTAssertTrue(configuration["repetitionPenalty"] is NSNull)
        let attempts = try XCTUnwrap(object["attempts"] as? [[String: Any]])
        XCTAssertEqual(attempts.count, 6)
        XCTAssertTrue(attempts[0]["generatedText"] is NSNull)
        XCTAssertTrue(attempts[0]["renderabilityTrace"] is NSNull)
        let metrics = try XCTUnwrap(
            object["summary"] as? [String: Any]
        )["metrics"] as? [String: Any]
        XCTAssertTrue(metrics?["medianFirstRenderableProxyTTFTMilliseconds"] is NSNull)
        XCTAssertTrue(metrics?["medianRequestCompletionMilliseconds"] is NSNull)
    }

    func testPowerResultRoundTripsThroughDecoder() throws {
        let result = try fixtureResult(
            resource: "b-ux-001-short-interaction"
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        XCTAssertEqual(
            try decoder.decode(
                PowerResultBundle.self,
                from: encoder.encode(result)
            ),
            result
        )
    }

    func testCompatibilityPolicyRequiresAnExactRunnerAndRuntimeIdentity() throws {
        let result = try fixtureResult()
        let identity = PowerRunnerIdentity(result: result)
        let approval = PowerCompatibilityPolicy.ApprovedRunner(
            approvalID: "fixture-runner",
            kind: "compatible",
            runnerID: identity.runnerID,
            runnerVersion: identity.runnerVersion,
            appVersion: identity.appVersion,
            appBuild: identity.appBuild,
            appSourceCommit: identity.appSourceCommit,
            runtime: identity.runtime
        )
        let policy = fixturePolicy(approvedRunners: [approval])

        XCTAssertEqual(policy.approval(for: identity), approval)
        let mismatched = PowerRunnerIdentity(
            runnerID: identity.runnerID,
            runnerVersion: identity.runnerVersion,
            appVersion: identity.appVersion,
            appBuild: identity.appBuild,
            appSourceCommit: identity.appSourceCommit,
            runtime: PowerRuntimeIdentity(
                name: identity.runtime.name,
                version: "unexpected-runtime",
                resolvedRevision: identity.runtime.resolvedRevision,
                backend: identity.runtime.backend,
                dependencyVersions: identity.runtime.dependencyVersions
            )
        )
        XCTAssertNil(policy.approval(for: mismatched))
        XCTAssertNoThrow(try policy.validateForPowerOneOne())
    }

    @MainActor
    func testSavedResultEligibilityIsIndependentFromCurrentAppEligibility() async throws {
        let documents = FileManager.default.temporaryDirectory.appending(
            path: UUID().uuidString,
            directoryHint: .isDirectory
        )
        try FileManager.default.createDirectory(
            at: documents,
            withIntermediateDirectories: true
        )
        defer { try? FileManager.default.removeItem(at: documents) }
        let store = ResultStore(documentsDirectory: documents)
        let result = try fixtureResult()
        _ = try await store.save(result)
        let identity = PowerRunnerIdentity(result: result)
        let approval = PowerCompatibilityPolicy.ApprovedRunner(
            approvalID: "saved-fixture-runner",
            kind: "compatible",
            runnerID: identity.runnerID,
            runnerVersion: identity.runnerVersion,
            appVersion: identity.appVersion,
            appBuild: identity.appBuild,
            appSourceCommit: identity.appSourceCommit,
            runtime: identity.runtime
        )
        let viewModel = BenchmarkViewModel(
            resultStore: store,
            compatibilityPolicyFetcher: StaticPowerPolicyFetcher(
                policy: fixturePolicy(approvedRunners: [approval])
            )
        )

        await viewModel.restoreLatestPowerResultIfNeeded()
        await viewModel.refreshCompatibilityPolicy()

        XCTAssertEqual(
            viewModel.currentRunnerEligibility,
            .notApproved(policyVersion: "1.1.2")
        )
        XCTAssertEqual(
            viewModel.selectedResultEligibility,
            .approved(
                policyVersion: "1.1.2",
                approvalID: "saved-fixture-runner"
            )
        )
        XCTAssertFalse(viewModel.canPrepare)
    }

    @MainActor
    func testUnavailablePolicyFailsClosedWithoutRemovingSavedResult() async throws {
        let documents = FileManager.default.temporaryDirectory.appending(
            path: UUID().uuidString,
            directoryHint: .isDirectory
        )
        try FileManager.default.createDirectory(
            at: documents,
            withIntermediateDirectories: true
        )
        defer { try? FileManager.default.removeItem(at: documents) }
        let store = ResultStore(documentsDirectory: documents)
        let result = try fixtureResult()
        let resultURL = try await store.save(result)
        let originalBytes = try Data(contentsOf: resultURL)
        let viewModel = BenchmarkViewModel(
            resultStore: store,
            compatibilityPolicyFetcher: StaticPowerPolicyFetcher(policy: nil)
        )

        await viewModel.restoreLatestPowerResultIfNeeded()
        await viewModel.refreshCompatibilityPolicy()

        guard case .unavailable = viewModel.currentRunnerEligibility else {
            return XCTFail("A failed policy fetch must fail closed")
        }
        guard case .unavailable = viewModel.selectedResultEligibility else {
            return XCTFail("Submission must fail closed when policy is unavailable")
        }
        XCTAssertFalse(viewModel.canPrepare)
        XCTAssertFalse(viewModel.canSubmitLatestPowerResultToGitHub)
        XCTAssertEqual(try Data(contentsOf: resultURL), originalBytes)
    }

    @MainActor
    func testLatestSavedPowerResultRestoresWithoutRewritingRawBytes() async throws {
        let documents = FileManager.default.temporaryDirectory.appending(
            path: UUID().uuidString,
            directoryHint: .isDirectory
        )
        try FileManager.default.createDirectory(
            at: documents,
            withIntermediateDirectories: true
        )
        defer { try? FileManager.default.removeItem(at: documents) }
        let store = ResultStore(documentsDirectory: documents)
        let earlier = try fixtureResult(
            createdAt: Date(timeIntervalSince1970: 2),
            resultID: UUID(uuidString: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")!
        )
        let earlierURL = try await store.save(earlier)
        let latest = try fixtureResult(
            resource: "b-ux-001-short-interaction",
            createdAt: Date(timeIntervalSince1970: 3),
            resultID: UUID(uuidString: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")!
        )
        let latestURL = try await store.save(latest)
        let originalBytes = try Data(contentsOf: latestURL)
        let corruptURL = documents
            .appending(path: "PowerBenchmarkResults", directoryHint: .isDirectory)
            .appending(path: "newer-but-corrupt.json")
        try Data("not-json".utf8).write(to: corruptURL)

        let loaded = try await store.loadLatestPowerResult()
        let restored = try XCTUnwrap(loaded)
        XCTAssertEqual(restored.result, latest)
        XCTAssertEqual(restored.fileURL, latestURL)
        XCTAssertEqual(try Data(contentsOf: latestURL), originalBytes)
        let history = try await store.loadPowerResults()
        XCTAssertEqual(history.map(\.result), [latest, earlier])

        let viewModel = BenchmarkViewModel(resultStore: store)
        await viewModel.restoreLatestPowerResultIfNeeded()
        XCTAssertEqual(viewModel.latestPowerResult, latest)
        XCTAssertEqual(viewModel.resultFileURL, latestURL)
        XCTAssertEqual(viewModel.storedPowerResults.map(\.result), [latest, earlier])
        XCTAssertTrue(viewModel.recoveryNotice?.contains("Restored") == true)

        viewModel.selectStoredPowerResult(id: earlier.resultID)
        XCTAssertEqual(viewModel.latestPowerResult, earlier)
        XCTAssertEqual(viewModel.resultFileURL, earlierURL)
        XCTAssertEqual(viewModel.githubSubmissionPhase, .idle)
        XCTAssertFalse(viewModel.acceptsPowerSubmissionDeclarations)
    }

    func testUXEncodingRetainsRecalculableRenderableEvidence() throws {
        let result = try fixtureResult(
            resource: "b-ux-001-short-interaction"
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let encodedResult = try encoder.encode(result)
        let attachment = XCTAttachment(
            data: encodedResult,
            uniformTypeIdentifier: "public.json"
        )
        attachment.name = "power-result-ux-fixture.json"
        attachment.lifetime = .keepAlways
        add(attachment)

        let object = try XCTUnwrap(
            JSONSerialization.jsonObject(with: encodedResult)
                as? [String: Any]
        )
        let attempts = try XCTUnwrap(object["attempts"] as? [[String: Any]])
        let trace = try XCTUnwrap(
            attempts[0]["renderabilityTrace"] as? [String: Any]
        )
        XCTAssertEqual(trace["firstRenderableTokenIndex"] as? Int, 0)
        XCTAssertEqual(trace["outcome"] as? String, "firstRenderableFound")
        let timing = try XCTUnwrap(
            attempts[0]["timingEvidence"] as? [String: Any]
        )
        XCTAssertNotNil(timing["requestCompletionNanoseconds"])
    }

    func testInterruptedAttemptRecoveryRetainsSixTerminalRecords() async throws {
        let directory = FileManager.default.temporaryDirectory
            .appending(path: UUID().uuidString, directoryHint: .isDirectory)
        let url = directory.appending(path: "checkpoint.json")
        let store = PowerSessionCheckpointStore(fileURL: url)
        let loaded = try PilotPlanLoader.load(resource: "suite-b-pilot-001")
        let context = try fixtureContext(plan: loaded.plan)
        let sessionID = UUID()
        try await store.begin(
            context: context,
            sessionID: sessionID,
            startedAt: Date(timeIntervalSince1970: 1),
            thermalStateAtStart: "nominal"
        )
        try await store.record(fixtureAttempt(index: 0))
        try await store.record(fixtureAttempt(index: 1))
        try await store.markAttemptStarted(
            index: 2,
            role: .measured,
            thermalStateBefore: "fair"
        )

        do {
            try await store.begin(
                context: context,
                sessionID: UUID(),
                startedAt: Date(timeIntervalSince1970: 10),
                thermalStateAtStart: "fair"
            )
            XCTFail("An unresolved checkpoint must never be overwritten")
        } catch PowerSessionCheckpointStore.CheckpointError.activeSessionExists {
            // Expected: the original session remains recoverable.
        }

        let recoveredValue = try await store.recoverInterrupted(
            thermalState: "fair"
        )
        let recovered = try XCTUnwrap(recoveredValue)
        XCTAssertEqual(recovered.session.sessionID, sessionID)
        XCTAssertEqual(recovered.session.attempts.count, 6)
        guard case .failed(_, let reason) = recovered.session.attempts[2].outcome
        else { return XCTFail("Active attempt must be retained as failed") }
        XCTAssertEqual(reason, "process_terminated_unclassified")
        for attempt in recovered.session.attempts[3...] {
            guard case .notRun(let reason) = attempt.outcome else {
                return XCTFail("Unstarted attempt must be retained as notRun")
            }
            XCTAssertEqual(reason, "prior_attempt_unrecoverable")
        }

        let recoveredResult = try PowerResultBundle.make(
            session: recovered.session,
            context: recovered.context,
            resultID: UUID(uuidString: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")!,
            createdAt: Date(timeIntervalSince1970: 3)
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let attachment = XCTAttachment(
            data: try encoder.encode(recoveredResult),
            uniformTypeIdentifier: "public.json"
        )
        attachment.name = "power-result-recovered-fixture.json"
        attachment.lifetime = .keepAlways
        add(attachment)
        try await store.clear()
    }

    func testShortInteractionResponseConformanceUsesVersionedV2Policy() {
        XCTAssertEqual(
            ShortInteractionResponseConformance.policyIdentity,
            "short-interaction-response-v2@2.0.0-draft.1"
        )
        XCTAssertTrue(
            ShortInteractionResponseConformance.passes(
                "Your note is safe on this iPhone. Sync will return when the device is online again."
            )
        )
        XCTAssertFalse(
            ShortInteractionResponseConformance.passes(
                "Your note will sync later."
            )
        )
        XCTAssertTrue(
            ShortInteractionResponseConformance.passes(
                "Your note is securely stored on this device. It will sync when connectivity returns."
            )
        )
        XCTAssertTrue(
            ShortInteractionResponseConformance.passes(
                "The note was saved locally. It will upload automatically once you are back online."
            )
        )
        XCTAssertEqual(
            ShortInteractionResponseConformance.assessment(
                "Your note is not safe on this device. It will sync when connectivity returns."
            ),
            .contradicted
        )
        XCTAssertEqual(
            ShortInteractionResponseConformance.assessment(
                "Your note remains intact on this device. It will sync when connectivity returns."
            ),
            .notVerified
        )
    }

    func testAdvisoryResponseFailureDoesNotSuppressTechnicalMetrics() throws {
        let result = try fixtureResult(
            resource: "b-ux-001-short-interaction",
            userExperienceText:
                "Your note remains intact on this device. It will sync when connectivity returns."
        )

        for attempt in result.attempts {
            XCTAssertEqual(attempt.responseConformance.status, "fail")
            XCTAssertEqual(
                attempt.responseConformance.reasonCodes,
                ["response_conformance_failed"]
            )
            XCTAssertNotNil(attempt.derivedMetrics.pipelineTTFTMilliseconds)
            XCTAssertNotNil(
                attempt.derivedMetrics.firstRenderableProxyTTFTMilliseconds
            )
            XCTAssertNotNil(attempt.derivedMetrics.requestCompletionMilliseconds)
            XCTAssertNotNil(attempt.derivedMetrics.prefillTokensPerSecond)
            XCTAssertNotNil(attempt.derivedMetrics.decodeTokensPerSecond)
            XCTAssertNotNil(attempt.derivedMetrics.processPhysicalFootprintMiB)
        }
        XCTAssertNotNil(result.summary.metrics.medianPipelineTTFTMilliseconds)
        XCTAssertNotNil(
            result.summary.metrics.medianFirstRenderableProxyTTFTMilliseconds
        )
        XCTAssertNotNil(result.summary.metrics.medianRequestCompletionMilliseconds)
        XCTAssertNotNil(result.summary.metrics.medianPrefillTokensPerSecond)
        XCTAssertNotNil(result.summary.metrics.medianDecodeTokensPerSecond)
        XCTAssertNotNil(
            result.summary.metrics.medianProcessPhysicalFootprintMiB
        )
    }

    func testPowerSubmissionPackagePreservesRawBytesAndCurrentManifest() async throws {
        let result = try fixtureResult(resource: "b-ux-001-short-interaction")
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [
            .prettyPrinted, .sortedKeys, .withoutEscapingSlashes,
        ]
        let rawBytes = try encoder.encode(result)
        let resultURL = FileManager.default.temporaryDirectory.appending(
            path: "\(UUID().uuidString)-power-result.json"
        )
        try rawBytes.write(to: resultURL)
        defer { try? FileManager.default.removeItem(at: resultURL) }

        let package = try PowerSubmissionPackage.make(
            result: result,
            resultURL: resultURL,
            githubHandle: "ExampleContributor",
            conflictCategory: .none,
            conflictStatement: "",
            thermalAssistance: .none,
            environmentNotes: nil,
            submissionID: UUID(
                uuidString: "11111111-2222-4333-8444-555555555555"
            )!,
            createdAt: Date(timeIntervalSince1970: 4)
        )
        XCTAssertEqual(package.resultData, rawBytes)
        let manifest = try XCTUnwrap(
            JSONSerialization.jsonObject(with: package.manifestData)
                as? [String: Any]
        )
        XCTAssertEqual(
            manifest["schemaVersion"] as? String,
            "suite-b-power-submission-1.1.0"
        )
        XCTAssertEqual(
            (manifest["contributor"] as? [String: Any])?["githubHandle"]
                as? String,
            "ExampleContributor"
        )
        XCTAssertEqual(
            (manifest["result"] as? [String: Any])?["resultID"] as? String,
            result.resultID.uuidString.lowercased()
        )

        let documents = FileManager.default.temporaryDirectory.appending(
            path: UUID().uuidString,
            directoryHint: .isDirectory
        )
        try FileManager.default.createDirectory(
            at: documents,
            withIntermediateDirectories: true
        )
        defer { try? FileManager.default.removeItem(at: documents) }
        let store = ResultStore(documentsDirectory: documents)
        let packageURL = try await store.save(package)
        let savedResultURL = packageURL.appending(path: "result.json")
        let savedManifestURL = packageURL.appending(path: "submission.json")
        XCTAssertEqual(try Data(contentsOf: savedResultURL), rawBytes)
        XCTAssertEqual(
            try Data(contentsOf: savedManifestURL),
            package.manifestData
        )

        do {
            _ = try await store.save(package)
            XCTFail("A saved package must not be overwritten")
        } catch {
            XCTAssertEqual(try Data(contentsOf: savedResultURL), rawBytes)
            XCTAssertEqual(
                try Data(contentsOf: savedManifestURL),
                package.manifestData
            )
        }
        let packageRoot = documents.appending(
            path: "PowerSubmissionPackages",
            directoryHint: .isDirectory
        )
        let packageRootContents = try FileManager.default.contentsOfDirectory(
            at: packageRoot,
            includingPropertiesForKeys: nil
        )
        XCTAssertFalse(packageRootContents.contains { $0.lastPathComponent.hasPrefix(".") })
    }

    private func fixtureResult(
        resource: String = "suite-b-pilot-001",
        userExperienceText: String? = nil,
        createdAt: Date = Date(timeIntervalSince1970: 3),
        resultID: UUID = UUID(
            uuidString: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        )!
    ) throws -> PowerResultBundle {
        let loaded = try PilotPlanLoader.load(resource: resource)
        let context = try fixtureContext(plan: loaded.plan)
        let isUserExperience = loaded.plan.workload.category == "user-experience"
        let attempts = (0..<6).map {
            fixtureAttempt(
                index: $0,
                userExperience: isUserExperience,
                userExperienceText: userExperienceText
            )
        }
        return try PowerResultBundle.make(
            session: BenchmarkSession(
                sessionID: UUID(),
                startedAt: Date(timeIntervalSince1970: 1),
                endedAt: Date(timeIntervalSince1970: 2),
                thermalStateAtStart: "nominal",
                thermalStateAtEnd: "fair",
                runtimeIdentity: "fixture",
                attempts: attempts
            ),
            context: context,
            resultID: resultID,
            createdAt: createdAt
        )
    }

    private func fixturePolicy(
        approvedRunners: [PowerCompatibilityPolicy.ApprovedRunner]
    ) -> PowerCompatibilityPolicy {
        PowerCompatibilityPolicy(
            schemaVersion: "suite-b-power-compatible-runners-1.1.2",
            policyID: "suite-b-power-runner-compatibility",
            policyVersion: "1.1.2",
            status: "published",
            benchmarkRelease: .init(
                id: "suite-b-power",
                policyVersion: "1.1.2",
                sourceRelease: .init(id: "suite-b-power", version: "1.1.0")
            ),
            protocolSemanticsChanged: false,
            resultSchemaChanged: false,
            rawEvidenceMutationAllowed: false,
            approvedRunners: approvedRunners
        )
    }

    private func fixtureContext(plan: PilotPlan) throws -> PowerExecutionContext {
        PowerExecutionContext(
            plan: plan,
            environment: try PowerExecutionEnvironmentSnapshot(
                DeviceEnvironment(
                    modelIdentifier: "iPhone15,3",
                    systemName: "iOS",
                    systemVersion: "26.5",
                    systemBuild: "23F79",
                    operatingSystemVersion: .init(
                        majorVersion: 26,
                        minorVersion: 5,
                        patchVersion: 0
                    ),
                    physicalMemoryBytes: 6_000_000_000,
                    thermalState: "nominal",
                    debuggerAttached: false,
                    buildConfiguration: "Release",
                    appVersion: "0.8.0",
                    appBuild: "10",
                    appSourceCommit: String(repeating: "a", count: 40),
                    lowPowerModeEnabled: false,
                    batteryLevelPercent: 80,
                    batteryState: "unplugged"
                )
            ),
            modelPreparation: ModelPreparationEvidence(
                artifactID: plan.modelProfile.artifactId,
                artifactRevision: plan.modelProfile.artifactRevision,
                cacheStateBeforePreparation: .cached,
                downloadOccurredDuringSession: false,
                preparationDurationMilliseconds: 1,
                preparationCompleted: true,
                modelLoadCompleted: true,
                eligibleForPerformanceMeasurement: true,
                reasonCodes: [],
                cacheVerificationMethod:
                    "huggingface_revision_manifest_cached_file_size_v1",
                preparedAt: Date(timeIntervalSince1970: 0)
            )
        )
    }

    private func fixtureAttempt(
        index: Int,
        userExperience: Bool = false,
        userExperienceText: String? = nil
    ) -> BenchmarkAttempt {
        let generatedText = userExperienceText
            ?? "Your note is safe on this iPhone. Sync will return when the device is online again."
        let renderabilityTrace = userExperience
            ? FirstRenderableTrace(
                policyVersion: FirstRenderableTrace.currentPolicyVersion,
                clockOrigin: FirstRenderableTrace.traceClockOrigin,
                scope: FirstRenderableTrace.traceScope,
                captureLimit: FirstRenderableTrace.maximumCaptureEntries,
                generationStartNanoseconds: 5_000_000,
                outcome: .firstRenderableFound,
                firstRenderableTokenIndex: 0,
                entries: [
                    .init(
                        tokenIndex: 0,
                        tokenID: 1,
                        tokenReceivedNanoseconds: 15_000_000,
                        decodedAtNanoseconds: 16_000_000,
                        decodedPrefix: generatedText,
                        isRenderable: true
                    ),
                ]
            )
            : nil
        return BenchmarkAttempt(
            index: index,
            role: index == 0 ? .warmup : .measured,
            tokens: [
                .init(index: 0, tokenID: 1, elapsedNanoseconds: 10_000_000),
                .init(index: 1, tokenID: 2, elapsedNanoseconds: 20_000_000),
            ],
            peakMemoryBytes: 256 * 1_048_576,
            memorySamples: [
                .init(
                    elapsedNanoseconds: 1_000_000,
                    physicalFootprintBytes: 256 * 1_048_576
                ),
            ],
            thermalStateBefore: "nominal",
            thermalStateAfter: "nominal",
            outcome: .completed(
                RuntimeGenerationResult(
                    promptTokenCount: 128,
                    outputTokenCount: 2,
                    stopReason: .endOfSequence,
                    promptTimeSeconds: 0.5,
                    generateTimeSeconds: 0.02,
                    generationStartNanoseconds: 5_000_000,
                    promptEvaluationNanoseconds: 500_000_000,
                    requestCompletionNanoseconds:
                        userExperience ? 30_000_000 : nil,
                    generatedText: userExperience ? generatedText : nil,
                    renderabilityTrace: renderabilityTrace
                )
            )
        )
    }
}
