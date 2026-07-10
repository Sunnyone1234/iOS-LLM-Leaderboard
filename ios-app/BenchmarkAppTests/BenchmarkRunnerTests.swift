import XCTest
@testable import BenchmarkApp

final class BenchmarkRunnerTests: XCTestCase {
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

    func testCriticalThermalStatePreventsRemainingGenerations() async {
        let runtime = FixtureRuntime()
        let states = ThermalSequence([
            "nominal", "nominal", // warm-up
            "nominal", "critical", // first measured run reaches critical
            "critical", "nominal", "nominal", "nominal",
        ])
        let session = await BenchmarkRunner(
            runtime: runtime,
            procedure: pilotProcedure,
            thermalState: { states.next() }
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
                    generateTimeSeconds: 0.15
                )
            )
        )

        let metrics = AttemptMetrics.calculate(for: attempt)
        XCTAssertEqual(metrics.ttftMilliseconds, 100)
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

private final class ThermalSequence: @unchecked Sendable {
    private let lock = NSLock()
    private var states: [String]

    init(_ states: [String]) {
        self.states = states
    }

    func next() -> String {
        lock.lock()
        defer { lock.unlock() }
        guard !states.isEmpty else { return "critical" }
        return states.removeFirst()
    }
}

private actor FixtureRuntime: LanguageModelRuntime {
    enum FixtureError: Error {
        case plannedFailure
    }

    nonisolated let identity = "fixture-runtime"
    private(set) var generateCount = 0
    private let failingGeneration: Int?

    init(failingGeneration: Int? = nil) {
        self.failingGeneration = failingGeneration
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
        return RuntimeGenerationResult(
            promptTokenCount: 1,
            outputTokenCount: 2,
            stopReason: .endOfSequence,
            promptTimeSeconds: 0.001,
            generateTimeSeconds: 0.002
        )
    }
}
