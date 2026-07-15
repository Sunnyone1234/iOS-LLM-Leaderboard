import Foundation
import XCTest
@testable import BenchmarkApp

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

    private func fixtureResult(
        resource: String = "suite-b-pilot-001",
        userExperienceText: String? = nil
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
            resultID: UUID(uuidString: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")!,
            createdAt: Date(timeIntervalSince1970: 3)
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
