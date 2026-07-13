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
        XCTAssertEqual(loaded.plan.planVersion, "1.0.0-rc.1")
        XCTAssertEqual(loaded.plan.workload.workloadId, "b-pipe-001-sustained-generation")
        XCTAssertFalse(loaded.prompt.isEmpty)

        let ux = try PilotPlanLoader.load(resource: "b-ux-001-short-interaction")
        XCTAssertEqual(ux.plan.planId, "b-ux-001-validation")
        XCTAssertEqual(ux.plan.workload.workloadId, "b-ux-001-short-interaction")
    }

    func testProductionPickerContainsOnlyTheTwoPilotWorkloads() {
        XCTAssertEqual(
            ProductionBenchmarkPlan.allCases.map(\.workloadID),
            [
                "b-pipe-001-sustained-generation",
                "b-ux-001-short-interaction",
            ]
        )
    }

    func testProductionModelPickerContainsExactlyThreeFixedProfiles() {
        XCTAssertEqual(
            ProductionModelProfile.allCases.map {
                $0.planModelProfile.artifactId
            },
            [
                "mlx-community/Qwen3-0.6B-4bit",
                "mlx-community/Qwen3-1.7B-4bit",
                "mlx-community/Qwen3-4B-3bit",
            ]
        )
        XCTAssertEqual(
            Set(ProductionModelProfile.allCases.map {
                $0.planModelProfile.artifactRevision
            }).count,
            3
        )
    }

    func testProductionPlanSelectionLoadsTheExactPlan() {
        let viewModel = BenchmarkViewModel()

        viewModel.selectBenchmarkPlan(.shortInteraction)
        XCTAssertEqual(
            viewModel.loadedPlan?.plan.workload.workloadId,
            "b-ux-001-short-interaction"
        )
        XCTAssertTrue(
            viewModel.loadedPlan?.plan.measurementMode.userVisibleTtftAvailable
                == true
        )

        viewModel.selectBenchmarkPlan(.sustainedGeneration)
        XCTAssertEqual(
            viewModel.loadedPlan?.plan.workload.workloadId,
            "b-pipe-001-sustained-generation"
        )
        XCTAssertTrue(
            viewModel.loadedPlan?.plan.measurementMode.userVisibleTtftAvailable
                == false
        )
    }

    func testModelSelectionLoadsExactArtifactAndPreservesWorkload() {
        let viewModel = BenchmarkViewModel()
        viewModel.selectBenchmarkPlan(.shortInteraction)
        viewModel.selectModelProfile(.medium)

        XCTAssertEqual(
            viewModel.loadedPlan?.plan.workload.workloadId,
            "b-ux-001-short-interaction"
        )
        XCTAssertEqual(
            viewModel.loadedPlan?.plan.modelProfile.artifactId,
            "mlx-community/Qwen3-1.7B-4bit"
        )
        XCTAssertEqual(viewModel.preparationPhase, .notPrepared)

        viewModel.selectModelProfile(.large)
        XCTAssertEqual(
            viewModel.loadedPlan?.plan.modelProfile.artifactRevision,
            "c4e8054c71facfa84f781cdb7c1ffab3f09f89bf"
        )
        XCTAssertEqual(viewModel.preparationPhase, .notPrepared)
    }

    func testUnifiedExportIdentifiesSelectedModelProfile() throws {
        let loaded = try PilotPlanLoader.load(
            resource: ProductionBenchmarkPlan.shortInteraction.rawValue,
            modelProfile: .medium
        )
        let registry = try SuiteBPlanRegistryLoader.load()
        let registryPlan = try XCTUnwrap(
            registry.plan(workloadID: loaded.plan.workload.workloadId)
        )
        let profile = loaded.plan.modelProfile
        let preparation = ModelPreparationEvidence(
            artifactID: profile.artifactId,
            artifactRevision: profile.artifactRevision,
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
        let bundle = SuiteBResultBundle.common(
            registryPlan: registryPlan,
            basePlan: loaded.plan,
            environment: DeviceEnvironment(
                modelIdentifier: "iPhone15,3",
                systemName: "iOS",
                systemVersion: "26.5",
                systemBuild: "23F77",
                operatingSystemVersion: .init(
                    majorVersion: 26,
                    minorVersion: 5,
                    patchVersion: 0
                ),
                physicalMemoryBytes: 6_000_000_000,
                thermalState: "nominal",
                debuggerAttached: false,
                buildConfiguration: "Release",
                appVersion: "0.7.0",
                appBuild: "9",
                appSourceCommit: nil,
                lowPowerModeEnabled: false,
                batteryLevelPercent: 75,
                batteryState: "unplugged"
            ),
            modelPreparation: preparation,
            sessions: []
        )

        XCTAssertEqual(bundle.schemaVersion, "suite-b-result-bundle-0.4")
        XCTAssertEqual(bundle.model.artifactID, profile.artifactId)
        XCTAssertEqual(bundle.model.artifactRevision, profile.artifactRevision)
        XCTAssertEqual(bundle.model.modelFamily, "Qwen3 dense")
        XCTAssertEqual(bundle.model.parameterSizeClass, "medium-1.7b")
        XCTAssertEqual(bundle.model.artifactRepositorySizeBytes, 979_502_864)
        XCTAssertEqual(
            bundle.generationConfiguration.chatTemplateIdentity,
            "artifact-tokenizer-config-enable-thinking-false"
        )
    }

    func testProductionPlansMatchTheirExportRegistryIdentity() throws {
        let registry = try SuiteBPlanRegistryLoader.load()
        for selection in ProductionBenchmarkPlan.allCases {
            for modelProfile in ProductionModelProfile.allCases {
                let loaded = try PilotPlanLoader.load(
                    resource: selection.rawValue,
                    modelProfile: modelProfile
                )
                let registryPlan = try XCTUnwrap(
                    registry.plan(workloadID: selection.workloadID)
                )
                XCTAssertTrue(
                    SuiteBResultBundle.executionIdentityMatches(
                        registryPlan: registryPlan,
                        plan: loaded.plan
                    ),
                    "\(selection.workloadID) / \(modelProfile.rawValue)"
                )
                XCTAssertNoThrow(
                    try MLXSwiftRuntime.validateIdentity(loaded.plan)
                )
            }
        }

        let pipeline = try PilotPlanLoader.load(
            resource: ProductionBenchmarkPlan.sustainedGeneration.rawValue
        )
        let uxRegistry = try XCTUnwrap(
            registry.plan(workloadID: ProductionBenchmarkPlan.shortInteraction.workloadID)
        )
        XCTAssertFalse(
            SuiteBResultBundle.executionIdentityMatches(
                registryPlan: uxRegistry,
                plan: pipeline.plan
            )
        )
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
                modelFamily: "Qwen3 dense",
                parameterSizeClass: "small-0.6b",
                quantization: "4-bit",
                modelFormat: "MLX Safetensors",
                tokenizerIdentity: "mlx-community/Qwen3-0.6B-4bit@73e3e38d981303bc594367cd910ea6eb48349da8/tokenizer_config.json",
                sourceUrl: "https://huggingface.co/mlx-community/Qwen3-0.6B-4bit/tree/73e3e38d981303bc594367cd910ea6eb48349da8",
                licenseIdentifier: "apache-2.0",
                licenseSourceUrl: "https://huggingface.co/Qwen/Qwen3-0.6B/blob/c1899de289a04d12100db370d81485cdf75e47ca/LICENSE",
                artifactRepositorySizeBytes: 682_323_786,
                compatibilityConstraints: ["physical-run-required-before-publication"],
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
