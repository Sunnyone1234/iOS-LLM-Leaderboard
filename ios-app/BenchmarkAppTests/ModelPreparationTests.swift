import XCTest
@testable import BenchmarkApp

@MainActor
final class ModelPreparationTests: XCTestCase {
    func testRevisionManifestCacheClassification() {
        let expected: [String: Int?] = [
            "config.json": 10,
            "model.safetensors": 100,
        ]
        XCTAssertEqual(
            ModelCacheVerification.classify(
                expectedFiles: expected,
                cachedFileSizes: [:]
            ),
            .notCached
        )
        XCTAssertEqual(
            ModelCacheVerification.classify(
                expectedFiles: expected,
                cachedFileSizes: ["config.json": 10]
            ),
            .incomplete
        )
        XCTAssertEqual(
            ModelCacheVerification.classify(
                expectedFiles: expected,
                cachedFileSizes: [
                    "config.json": 10,
                    "model.safetensors": 100,
                ]
            ),
            .cached
        )
    }

    func testCachedModelAllowsRun() {
        XCTAssertEqual(admissionReasons(preparation: preparedEvidence()), [])
    }

    func testFirstDownloadBlocksRunUntilRestart() {
        let evidence = preparationEvidence(
            cacheState: .notCached,
            downloaded: true,
            completed: true,
            loaded: true,
            eligible: false,
            reasons: [
                "model_download_during_session",
                "restart_required_after_download",
            ]
        )
        let reasons = admissionReasons(preparation: evidence)
        XCTAssertTrue(reasons.contains("model_download_during_session"))
        XCTAssertTrue(reasons.contains("restart_required_after_download"))
        XCTAssertEqual(
            BenchmarkViewModel.preparationPhase(for: evidence),
            .restartRequired
        )
    }

    func testRestartAndConfirmedCacheAllowsRun() {
        let downloaded = preparationEvidence(
            cacheState: .notCached,
            downloaded: true,
            completed: true,
            loaded: true,
            eligible: false,
            reasons: ["restart_required_after_download"]
        )
        XCTAssertFalse(admissionReasons(preparation: downloaded).isEmpty)
        XCTAssertTrue(admissionReasons(preparation: preparedEvidence()).isEmpty)
        XCTAssertEqual(
            BenchmarkViewModel.preparationPhase(for: preparedEvidence()),
            .ready
        )
    }

    func testUnknownCacheBlocksRun() {
        let evidence = preparationEvidence(
            cacheState: .unknown,
            eligible: false,
            reasons: ["model_cache_state_unknown"]
        )
        XCTAssertTrue(
            admissionReasons(preparation: evidence).contains(
                "model_cache_state_unknown"
            )
        )
    }

    func testPreparationFailureBlocksRun() {
        let evidence = preparationEvidence(
            cacheState: .cached,
            eligible: false,
            reasons: ["model_preparation_failed"]
        )
        XCTAssertTrue(
            admissionReasons(preparation: evidence).contains(
                "model_preparation_failed"
            )
        )
    }

    func testPromptHashMismatchStopsLoading() {
        XCTAssertThrowsError(
            try PilotPlanLoader.validatePromptHash(
                Data("different".utf8),
                expected: String(repeating: "0", count: 64)
            )
        )
    }

    func testBundledPlanAndPromptLoadTogether() throws {
        let loaded = try PilotPlanLoader.load()
        XCTAssertEqual(loaded.plan.planId, "b-pipe-001-validation")
        XCTAssertEqual(loaded.plan.planVersion, "0.2.0-pilot")
        XCTAssertEqual(loaded.plan.workload.workloadId, "b-pipe-001-sustained-generation")
        XCTAssertFalse(loaded.prompt.isEmpty)

        let ux = try PilotPlanLoader.load(resource: "b-ux-001-short-interaction")
        XCTAssertEqual(ux.plan.planId, "b-ux-001-validation")
        XCTAssertEqual(ux.plan.workload.workloadId, "b-ux-001-short-interaction")
    }

    func testUnifiedRegistryLoadsAllWorkloads() throws {
        let registry = try SuiteBPlanRegistryLoader.load()
        XCTAssertEqual(registry.plans.count, 4)
        XCTAssertEqual(
            registry.plan(workloadID: "b-pipe-002-input-length-sweep")?.targetInputTokens,
            [32, 128, 512, 2048]
        )
        XCTAssertEqual(
            registry.plan(workloadID: "b-ux-002-context-assistance")?.outputTokenLimit,
            128
        )
    }

    func testRuntimeIdentityMismatchStopsPreparation() {
        let valid = pilotPlan()
        let invalid = PilotPlan(
            planSchemaVersion: valid.planSchemaVersion,
            planId: valid.planId,
            planVersion: valid.planVersion,
            status: valid.status,
            modelProfile: valid.modelProfile,
            runtimeProfile: .init(
                runtimeName: valid.runtimeProfile.runtimeName,
                packageVersion: "9.9.9",
                packageRevision: valid.runtimeProfile.packageRevision,
                mlxSwiftVersion: valid.runtimeProfile.mlxSwiftVersion,
                mlxSwiftRevision: valid.runtimeProfile.mlxSwiftRevision,
                backend: valid.runtimeProfile.backend,
                downloaderPackage: valid.runtimeProfile.downloaderPackage,
                tokenizerPackage: valid.runtimeProfile.tokenizerPackage
            ),
            workload: valid.workload,
            generation: valid.generation,
            measurementMode: valid.measurementMode,
            procedure: valid.procedure,
            environmentRequirements: valid.environmentRequirements
        )
        XCTAssertThrowsError(try MLXSwiftRuntime.validateIdentity(invalid))
    }

    func testAllEnvironmentRequirementsBlockRun() {
        let reasons = BenchmarkAdmission.reasonCodes(
            preparation: preparedEvidence(),
            environment: .init(
                debuggerAttached: true,
                buildConfiguration: "Debug",
                lowPowerModeEnabled: true,
                thermalState: "fair",
                batteryState: "charging",
                batteryLevelPercent: 25
            ),
            requirements: pilotPlan().environmentRequirements
        )
        XCTAssertEqual(
            Set(reasons),
            Set([
                "debugger_attached",
                "non_release_build",
                "low_power_mode_enabled",
                "initial_thermal_state_not_nominal",
                "external_power_connected",
                "battery_level_below_minimum",
            ])
        )
    }

    private func admissionReasons(
        preparation: ModelPreparationEvidence?
    ) -> [String] {
        BenchmarkAdmission.reasonCodes(
            preparation: preparation,
            environment: .init(
                debuggerAttached: false,
                buildConfiguration: "Release",
                lowPowerModeEnabled: false,
                thermalState: "nominal",
                batteryState: "unplugged",
                batteryLevelPercent: 75
            ),
            requirements: pilotPlan().environmentRequirements
        )
    }

    private func preparedEvidence() -> ModelPreparationEvidence {
        preparationEvidence(
            cacheState: .cached,
            completed: true,
            loaded: true,
            eligible: true
        )
    }

    private func preparationEvidence(
        cacheState: ModelPreparationEvidence.CacheState,
        downloaded: Bool = false,
        completed: Bool = false,
        loaded: Bool = false,
        eligible: Bool,
        reasons: [String] = []
    ) -> ModelPreparationEvidence {
        ModelPreparationEvidence(
            artifactID: "mlx-community/Qwen3-0.6B-4bit",
            artifactRevision: "73e3e38d981303bc594367cd910ea6eb48349da8",
            cacheStateBeforePreparation: cacheState,
            downloadOccurredDuringSession: downloaded,
            preparationDurationMilliseconds: 100,
            preparationCompleted: completed,
            modelLoadCompleted: loaded,
            eligibleForPerformanceMeasurement: eligible,
            reasonCodes: reasons,
            cacheVerificationMethod:
                "huggingface_revision_manifest_cached_file_size_v1",
            preparedAt: Date(timeIntervalSince1970: 0)
        )
    }

    private func pilotPlan() -> PilotPlan {
        PilotPlan(
            planSchemaVersion: "0.3",
            planId: "b-pipe-001-validation",
            planVersion: "0.2.0-pilot",
            status: "pilot-validated",
            modelProfile: .init(
                displayName: "Qwen3 0.6B",
                baseModelId: "Qwen/Qwen3-0.6B",
                artifactId: "mlx-community/Qwen3-0.6B-4bit",
                artifactRevision: "73e3e38d981303bc594367cd910ea6eb48349da8",
                quantization: "4-bit",
                modelFormat: "MLX Safetensors",
                artifactContentHash: nil
            ),
            runtimeProfile: .init(
                runtimeName: "MLX Swift LM",
                packageVersion: "3.31.4",
                packageRevision: "bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57",
                mlxSwiftVersion: "0.31.6",
                mlxSwiftRevision: "0bb916c67f4b9e5c682cbe02a42c701c93ab5021",
                backend: "MLX/Metal",
                downloaderPackage: "swift-huggingface 0.9.0",
                tokenizerPackage: "swift-transformers 1.3.0"
            ),
            workload: .init(
                workloadId: "b-pipe-001-sustained-generation",
                workloadVersion: "0.2.0-pilot",
                v2ProfileMapping: "b-pipe-001-sustained-generation@0.2.0-pilot",
                category: "pipeline",
                promptPath: "ios-app/workloads/suite-b-pilot-001-prompt.txt",
                promptSha256: String(repeating: "a", count: 64),
                outputTokenLimit: 512
            ),
            generation: .init(
                samplingEnabled: false,
                temperature: 0,
                topP: nil,
                topK: nil,
                seed: nil,
                repetitionPenalty: nil,
                thinkingMode: "disabled-via-prompt-directive",
                chatTemplateIdentity: "artifact-tokenizer-config",
                includeStopTokenInRawEvents: false,
                contextPolicy: "new-context-for-each-generation",
                modelLoadPolicy: "load-once-before-warmup",
                kvCachePolicy: "new-cache-for-each-generation"
            ),
            measurementMode: .init(
                measurementModeId: "b-mode-sustained-no-rest-v1",
                timingBoundaryVersion: "mlx-pilot-pipeline-boundaries-1",
                pipelineTtftStart: "prepared",
                pipelineTtftEnd: "first-token",
                userVisibleTtftAvailable: false,
                prefillSource: "mlx",
                decodeFormula: "documented",
                memoryMetric: "TASK_VM_INFO.phys_footprint",
                memorySamplingIntervalMilliseconds: 50
            ),
            procedure: .init(
                warmupRuns: 1,
                measuredRuns: 5,
                minimumSuccessfulRunsForSummary: 3,
                restIntervalSeconds: 0
            ),
            environmentRequirements: .init(
                releaseBuildRequired: true,
                debuggerDetachedRequired: true,
                initialThermalState: "nominal",
                lowPowerMode: "off",
                requiredPowerSource: "unplugged",
                minimumBatteryLevelPercent: 50
            )
        )
    }
}
