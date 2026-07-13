import XCTest
@testable import BenchmarkApp

final class BenchmarkRunnerTests: XCTestCase {
    func testContextAnswerContractRequiresAllGroundedFacts() {
        let valid = "ORCHID-47: The note is safe in the local vault. Sync waits until the network is stable for 30 seconds and, below 20%, until connected to power; do not delete or reinstall the app."
        XCTAssertTrue(ContextAnswerContract.evaluate(valid).passed)
        XCTAssertFalse(ContextAnswerContract.evaluate("The note will sync later.").passed)
    }
    func testBuildConfigurationIsExplicit() {
        XCTAssertTrue(["Debug", "Release"].contains(BuildMetadata.configuration))
        XCTAssertFalse(BuildMetadata.appVersion.isEmpty)
        XCTAssertFalse(BuildMetadata.appBuild.isEmpty)
    }

    func testKnownDeviceIdentifierIncludesFriendlyNameAndEvidenceID() {
        XCTAssertEqual(
            DeviceModelCatalog.displayName(for: "iPhone15,3"),
            "iPhone 14 Pro Max (iPhone15,3)"
        )
    }

    func testUnknownDeviceIdentifierIsNotGuessed() {
        XCTAssertEqual(
            DeviceModelCatalog.displayName(for: "iPhone99,9"),
            "iPhone99,9"
        )
    }

    func testPilotRunsOneWarmupAndFiveMeasuredAttempts() async {
        let runtime = FixtureRuntime()
        let session = await BenchmarkRunner(
            runtime: runtime,
            procedure: pilotProcedure
        ).run(prompt: "fixed")

        XCTAssertEqual(session.attempts.count, 6)
        XCTAssertEqual(session.attempts.first?.role, .warmup)
        XCTAssertEqual(session.measuredAttempts.count, 5)
        let generateCount = await runtime.generateCount
        XCTAssertEqual(generateCount, 6)
    }

    func testFailedMeasuredAttemptIsRetained() async {
        let runtime = FixtureRuntime(failingGeneration: 3)
        let session = await BenchmarkRunner(
            runtime: runtime,
            procedure: pilotProcedure
        ).run(prompt: "fixed")

        XCTAssertEqual(session.attempts.count, 6)
        guard case .failed = session.attempts[3].outcome else {
            return XCTFail("Expected failed attempt to remain in the session")
        }
    }

    func testUnifiedExportRetainsFailedAttemptEvidence() async {
        let session = await BenchmarkRunner(
            runtime: FixtureRuntime(failingGeneration: 3),
            procedure: pilotProcedure
        ).run(prompt: "fixed")

        let exported = SuiteBResultBundle.session(
            id: "default",
            target: nil,
            fixtureSHA256: String(repeating: "a", count: 64),
            padding: nil,
            benchmarkSession: session,
            memoryInterval: 50,
            minimumSuccessfulRuns: 3,
            includeQuality: false
        )

        XCTAssertEqual(exported.attempts.count, 6)
        XCTAssertEqual(exported.summary.successfulMeasuredRuns, 4)
        XCTAssertEqual(exported.summary.failedMeasuredRuns, 1)
        XCTAssertEqual(exported.attempts[3].outcome, "failed")
        XCTAssertNotNil(exported.attempts[3].errorMessage)
    }

    func testCriticalThermalStatePreventsRemainingGenerations() async {
        let thermalState = ThermalStateBox("nominal")
        let runtime = FixtureRuntime { generation in
            if generation == 1 {
                thermalState.set("critical")
            }
        }
        let session = await BenchmarkRunner(
            runtime: runtime,
            procedure: pilotProcedure,
            thermalState: { thermalState.value }
        ).run(prompt: "fixed")

        XCTAssertEqual(session.attempts.count, 6)
        XCTAssertEqual(session.measuredAttempts.count, 5)
        let generateCount = await runtime.generateCount
        XCTAssertEqual(generateCount, 2)
        XCTAssertEqual(
            session.measuredAttempts.filter {
                if case .notRun = $0.outcome { return true }
                return false
            }.count,
            4
        )
    }

    func testSeriousFinalThermalStateDoesNotInvalidateCompleteEvidence() {
        let attempts = (1...5).map { index in
            pilotAttempt(
                index: index,
                before: index < 4 ? "nominal" : "fair",
                after: index == 5 ? "serious" : (index < 3 ? "nominal" : "fair")
            )
        }
        let eligibility = PilotResultBundle.Eligibility.evaluate(
            attempts: attempts,
            modelPreparation: preparedEvidence(),
            debuggerAttached: false,
            buildConfiguration: "Release",
            lowPowerModeEnabled: false,
            plannedMeasuredRuns: 5
        )

        XCTAssertTrue(eligibility.sessionValidity.eligible)
        XCTAssertTrue(eligibility.coldPerformance.eligible)
        XCTAssertTrue(eligibility.sustainedPerformance.eligible)
        XCTAssertTrue(eligibility.thermalStability.eligible)
        XCTAssertFalse(eligibility.officialLeaderboard.eligible)
    }

    func testInvalidBuildAndPowerConditionsProduceReasonCodes() {
        let attempts = (1...5).map { index in
            pilotAttempt(index: index, before: "nominal", after: "nominal")
        }
        let eligibility = PilotResultBundle.Eligibility.evaluate(
            attempts: attempts,
            modelPreparation: preparedEvidence(),
            debuggerAttached: false,
            buildConfiguration: "Debug",
            lowPowerModeEnabled: true,
            plannedMeasuredRuns: 5
        )

        XCTAssertFalse(eligibility.sessionValidity.eligible)
        XCTAssertTrue(
            eligibility.sessionValidity.reasonCodes.contains("non_release_build")
        )
        XCTAssertTrue(
            eligibility.sessionValidity.reasonCodes.contains("low_power_mode_enabled")
        )
    }

    func testMetricsAreDerivedFromRawTokenEvents() {
        let attempt = BenchmarkAttempt(
            index: 1,
            role: .measured,
            tokens: [
                RuntimeToken(index: 0, tokenID: 10, elapsedNanoseconds: 100_000_000),
                RuntimeToken(index: 1, tokenID: 11, elapsedNanoseconds: 150_000_000),
                RuntimeToken(index: 2, tokenID: 12, elapsedNanoseconds: 250_000_000),
            ],
            peakMemoryBytes: 256 * 1_048_576,
            thermalStateBefore: "nominal",
            thermalStateAfter: "fair",
            outcome: .completed(
                RuntimeGenerationResult(
                    promptTokenCount: 200,
                    outputTokenCount: 3,
                    stopReason: .endOfSequence,
                    promptTimeSeconds: 0.5,
                    generateTimeSeconds: 0.15,
                    userVisibleTTFTNanoseconds: 125_000_000,
                    requestCompletionNanoseconds: 275_000_000,
                    renderabilityTrace: FirstRenderableTrace(
                        policyVersion: FirstRenderableTrace.currentPolicyVersion,
                        clockOrigin: FirstRenderableTrace.traceClockOrigin,
                        scope: FirstRenderableTrace.traceScope,
                        captureLimit: FirstRenderableTrace.maximumCaptureEntries,
                        generationStartNanoseconds: 20_000_000,
                        outcome: .firstRenderableFound,
                        firstRenderableTokenIndex: 0,
                        entries: [
                            .init(
                                tokenIndex: 0,
                                tokenID: 10,
                                tokenReceivedNanoseconds: 120_000_000,
                                decodedAtNanoseconds: 130_000_000,
                                decodedPrefix: "Hello",
                                isRenderable: true
                            )
                        ]
                    )
                )
            )
        )

        let metrics = AttemptMetrics.calculate(for: attempt)
        XCTAssertEqual(metrics.ttftMilliseconds, 100)
        XCTAssertEqual(metrics.userVisibleTTFTMilliseconds, 130)
        XCTAssertEqual(metrics.requestCompletionMilliseconds, 275)
        XCTAssertEqual(metrics.prefillTokensPerSecond, 400)
        XCTAssertNotNil(metrics.decodeTokensPerSecond)
        XCTAssertEqual(
            metrics.decodeTokensPerSecond!,
            2 / 0.15,
            accuracy: 0.0001
        )
        XCTAssertEqual(metrics.peakMemoryMegabytes, 256)
        XCTAssertEqual(metrics.p50TokenIntervalMilliseconds, 75)
        XCTAssertEqual(metrics.p95TokenIntervalMilliseconds, 97.5)
    }

    func testFirstRenderableTraceStopsAfterFirstRenderablePrefix() {
        var recorder = FirstRenderableTraceRecorder(
            generationStartNanoseconds: 90_000_000
        )
        recorder.record(
            tokenIndex: 0,
            tokenID: 10,
            tokenReceivedNanoseconds: 100_000_000,
            decodedAtNanoseconds: 101_000_000,
            decodedPrefix: " \n"
        )
        recorder.record(
            tokenIndex: 1,
            tokenID: 11,
            tokenReceivedNanoseconds: 110_000_000,
            decodedAtNanoseconds: 111_000_000,
            decodedPrefix: " \nHello"
        )
        recorder.record(
            tokenIndex: 2,
            tokenID: 12,
            tokenReceivedNanoseconds: 120_000_000,
            decodedAtNanoseconds: 121_000_000,
            decodedPrefix: " \nHello world"
        )

        let trace = recorder.finalize(outputTokenCount: 3)
        XCTAssertEqual(trace.outcome, .firstRenderableFound)
        XCTAssertEqual(trace.firstRenderableTokenIndex, 1)
        XCTAssertEqual(trace.firstRenderableDecodedAtNanoseconds, 111_000_000)
        XCTAssertEqual(trace.entries.count, 2)
        XCTAssertFalse(trace.entries[0].isRenderable)
        XCTAssertTrue(trace.entries[1].isRenderable)
    }

    func testFirstRenderablePolicyUsesTheFrozenUnicodeScalarSet() {
        XCTAssertFalse(FirstRenderableTrace.isRenderable(" \n\u{00A0}\u{3000}"))
        XCTAssertTrue(FirstRenderableTrace.isRenderable(" \n\u{001C}"))
    }

    func testFirstRenderableTraceCapsNonRenderableEvidenceAt32Tokens() {
        var recorder = FirstRenderableTraceRecorder(
            generationStartNanoseconds: 90_000_000
        )
        for index in 0..<FirstRenderableTrace.maximumCaptureEntries {
            recorder.record(
                tokenIndex: index,
                tokenID: index,
                tokenReceivedNanoseconds: UInt64(100_000_000 + index),
                decodedAtNanoseconds: UInt64(101_000_000 + index),
                decodedPrefix: String(repeating: " ", count: index + 1)
            )
        }

        XCTAssertFalse(recorder.shouldDecodeNextToken)
        let trace = recorder.finalize(
            outputTokenCount: FirstRenderableTrace.maximumCaptureEntries + 1
        )
        XCTAssertEqual(trace.outcome, .captureLimitReached)
        XCTAssertNil(trace.firstRenderableTokenIndex)
        XCTAssertNil(trace.firstRenderableDecodedAtNanoseconds)
        XCTAssertEqual(
            trace.entries.count,
            FirstRenderableTrace.maximumCaptureEntries
        )
    }

    func testDegradationUsesFirstAndLastSuccessfulMeasuredRuns() {
        let first = PilotResultBundle.Attempt(
            runIndex: 1,
            role: "measured",
            outcome: "completed",
            errorMessage: nil,
            promptTokenCount: 200,
            outputTokenCount: 512,
            stopReason: "outputTokenLimit",
            thermalStateBefore: "nominal",
            thermalStateAfter: "fair",
            memorySamplingIntervalMilliseconds: 50,
            metrics: AttemptMetrics(
                ttftMilliseconds: 500,
                prefillTokensPerSecond: 400,
                decodeTokensPerSecond: 50,
                peakMemoryMegabytes: 700,
                p50TokenIntervalMilliseconds: 20,
                p95TokenIntervalMilliseconds: 22,
                p99TokenIntervalMilliseconds: 24
            ),
            tokenEvents: []
        )
        let last = PilotResultBundle.Attempt(
            runIndex: 5,
            role: "measured",
            outcome: "completed",
            errorMessage: nil,
            promptTokenCount: 200,
            outputTokenCount: 512,
            stopReason: "outputTokenLimit",
            thermalStateBefore: "serious",
            thermalStateAfter: "serious",
            memorySamplingIntervalMilliseconds: 50,
            metrics: AttemptMetrics(
                ttftMilliseconds: 750,
                prefillTokensPerSecond: 300,
                decodeTokensPerSecond: 30,
                peakMemoryMegabytes: 700,
                p50TokenIntervalMilliseconds: 30,
                p95TokenIntervalMilliseconds: 32,
                p99TokenIntervalMilliseconds: 34
            ),
            tokenEvents: []
        )

        let degradation = PilotResultBundle.Degradation.calculate(
            first: first,
            last: last
        )
        XCTAssertEqual(degradation.decodePercentChange!, -40, accuracy: 0.0001)
        XCTAssertEqual(degradation.ttftPercentChange!, 50, accuracy: 0.0001)
        XCTAssertEqual(degradation.prefillPercentChange!, -25, accuracy: 0.0001)
    }


    private func pilotAttempt(
        index: Int,
        before: String,
        after: String
    ) -> PilotResultBundle.Attempt {
        PilotResultBundle.Attempt(
            runIndex: index,
            role: "measured",
            outcome: "completed",
            errorMessage: nil,
            promptTokenCount: 235,
            outputTokenCount: 512,
            stopReason: "outputTokenLimit",
            thermalStateBefore: before,
            thermalStateAfter: after,
            memorySamplingIntervalMilliseconds: 50,
            metrics: AttemptMetrics(
                ttftMilliseconds: 500,
                prefillTokensPerSecond: 400,
                decodeTokensPerSecond: 50,
                peakMemoryMegabytes: 700,
                p50TokenIntervalMilliseconds: 20,
                p95TokenIntervalMilliseconds: 22,
                p99TokenIntervalMilliseconds: 24
            ),
            tokenEvents: []
        )
    }

    private var pilotProcedure: BenchmarkProcedure {
        BenchmarkProcedure(
            warmupRuns: 1,
            measuredRuns: 5,
            outputTokenLimit: 512
        )
    }

    private func preparedEvidence() -> ModelPreparationEvidence {
        ModelPreparationEvidence(
            artifactID: "mlx-community/Qwen3-0.6B-4bit",
            artifactRevision: "73e3e38d981303bc594367cd910ea6eb48349da8",
            cacheStateBeforePreparation: .cached,
            downloadOccurredDuringSession: false,
            preparationDurationMilliseconds: 100,
            preparationCompleted: true,
            modelLoadCompleted: true,
            eligibleForPerformanceMeasurement: true,
            reasonCodes: [],
            cacheVerificationMethod:
                "huggingface_revision_manifest_cached_file_size_v1",
            preparedAt: Date(timeIntervalSince1970: 0)
        )
    }
}

private final class ThermalStateBox: @unchecked Sendable {
    private let lock = NSLock()
    private var state: String

    init(_ state: String) {
        self.state = state
    }

    var value: String {
        lock.lock()
        defer { lock.unlock() }
        return state
    }

    func set(_ value: String) {
        lock.lock()
        state = value
        lock.unlock()
    }
}

private actor FixtureRuntime: LanguageModelRuntime {
    enum FixtureError: Error {
        case plannedFailure
    }

    nonisolated let identity = "fixture-runtime"
    private(set) var generateCount = 0
    private let failingGeneration: Int?
    private let afterGeneration: @Sendable (Int) -> Void

    init(
        failingGeneration: Int? = nil,
        afterGeneration: @escaping @Sendable (Int) -> Void = { _ in }
    ) {
        self.failingGeneration = failingGeneration
        self.afterGeneration = afterGeneration
    }

    func generate(
        prompt: String,
        outputTokenLimit: Int,
        onToken: @Sendable (RuntimeToken) async -> Void
    ) async throws -> RuntimeGenerationResult {
        let generation = generateCount
        generateCount += 1

        if generation == failingGeneration {
            throw FixtureError.plannedFailure
        }

        await onToken(
            RuntimeToken(index: 0, tokenID: 1, elapsedNanoseconds: 1_000)
        )
        await onToken(
            RuntimeToken(index: 1, tokenID: 2, elapsedNanoseconds: 2_000)
        )
        afterGeneration(generation)
        return RuntimeGenerationResult(
            promptTokenCount: 1,
            outputTokenCount: 2,
            stopReason: .endOfSequence,
            promptTimeSeconds: 0.001,
            generateTimeSeconds: 0.002
        )
    }
}
