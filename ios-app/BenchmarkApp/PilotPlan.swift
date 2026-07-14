import CryptoKit
import Foundation

enum ProductionModelProfile: String, CaseIterable, Identifiable, Sendable {
    case small = "qwen3-0.6b-4bit"
    case medium = "qwen3-1.7b-4bit"
    case large = "qwen3-4b-3bit"
    case llama32OneB = "llama-3.2-1b-instruct-4bit"
    case gemma3OneB = "gemma-3-1b-it-qat-4bit"
    case granite33TwoB = "granite-3.3-2b-instruct-4bit"
    case smolLM3ThreeB = "smollm3-3b-4bit"

    enum EvidenceStatus: String, Sendable {
        case maintainerReference = "Maintainer reference"
        case communityEvidence = "Community evidence"
    }

    var id: String { rawValue }

    var title: String {
        switch self {
        case .small: "Qwen3 0.6B · 4-bit · Small"
        case .medium: "Qwen3 1.7B · 4-bit · Medium"
        case .large: "Qwen3 4B · 3-bit · Larger"
        case .llama32OneB: "Llama 3.2 1B · 4-bit · Community tested"
        case .gemma3OneB: "Gemma 3 1B · 4-bit · Community tested"
        case .granite33TwoB: "Granite 3.3 2B · 4-bit · Community tested"
        case .smolLM3ThreeB: "SmolLM3 3B · 4-bit · Community tested"
        }
    }

    var evidenceStatus: EvidenceStatus {
        switch self {
        case .small, .medium, .large: .maintainerReference
        case .llama32OneB, .gemma3OneB, .granite33TwoB, .smolLM3ThreeB:
            .communityEvidence
        }
    }

    var extraEOSTokens: Set<String> {
        switch self {
        case .llama32OneB: ["<|eot_id|>"]
        case .gemma3OneB: ["<end_of_turn>"]
        default: []
        }
    }

    static func matching(_ model: PilotPlan.ModelProfile) -> Self? {
        allCases.first {
            $0.planModelProfile.artifactId == model.artifactId
                && $0.planModelProfile.artifactRevision == model.artifactRevision
        }
    }

    var planModelProfile: PilotPlan.ModelProfile {
        switch self {
        case .small:
            .init(
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
                compatibilityConstraints: Self.compatibilityConstraints,
                artifactContentHash: nil
            )
        case .medium:
            .init(
                displayName: "Qwen3 1.7B",
                baseModelId: "Qwen/Qwen3-1.7B",
                artifactId: "mlx-community/Qwen3-1.7B-4bit",
                artifactRevision: "3b1b1768f8f8cf8351c712464f906e86c2b8269e",
                modelFamily: "Qwen3 dense",
                parameterSizeClass: "medium-1.7b",
                quantization: "4-bit",
                modelFormat: "MLX Safetensors",
                tokenizerIdentity: "mlx-community/Qwen3-1.7B-4bit@3b1b1768f8f8cf8351c712464f906e86c2b8269e/tokenizer_config.json",
                sourceUrl: "https://huggingface.co/mlx-community/Qwen3-1.7B-4bit/tree/3b1b1768f8f8cf8351c712464f906e86c2b8269e",
                licenseIdentifier: "apache-2.0",
                licenseSourceUrl: "https://huggingface.co/Qwen/Qwen3-1.7B/blob/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e/LICENSE",
                artifactRepositorySizeBytes: 979_502_864,
                compatibilityConstraints: Self.compatibilityConstraints,
                artifactContentHash: nil
            )
        case .large:
            .init(
                displayName: "Qwen3 4B",
                baseModelId: "Qwen/Qwen3-4B",
                artifactId: "mlx-community/Qwen3-4B-3bit",
                artifactRevision: "c4e8054c71facfa84f781cdb7c1ffab3f09f89bf",
                modelFamily: "Qwen3 dense",
                parameterSizeClass: "large-4b",
                quantization: "3-bit",
                modelFormat: "MLX Safetensors",
                tokenizerIdentity: "mlx-community/Qwen3-4B-3bit@c4e8054c71facfa84f781cdb7c1ffab3f09f89bf/tokenizer_config.json",
                sourceUrl: "https://huggingface.co/mlx-community/Qwen3-4B-3bit/tree/c4e8054c71facfa84f781cdb7c1ffab3f09f89bf",
                licenseIdentifier: "apache-2.0",
                licenseSourceUrl: "https://huggingface.co/Qwen/Qwen3-4B/blob/1cfa9a7208912126459214e8b04321603b3df60c/LICENSE",
                artifactRepositorySizeBytes: 1_771_660_929,
                compatibilityConstraints: Self.compatibilityConstraints + [
                    "large-profile-memory-headroom-must-be-validated-on-iPhone15,3"
                ],
                artifactContentHash: nil
            )
        case .llama32OneB:
            .init(
                displayName: "Llama 3.2 1B Instruct",
                baseModelId: "meta-llama/Llama-3.2-1B-Instruct",
                artifactId: "mlx-community/Llama-3.2-1B-Instruct-4bit",
                artifactRevision: "08231374eeacb049a0eade7922910865b8fce912",
                modelFamily: "Llama 3.2",
                parameterSizeClass: "small-1b",
                quantization: "4-bit",
                modelFormat: "MLX Safetensors",
                tokenizerIdentity: "mlx-community/Llama-3.2-1B-Instruct-4bit@08231374eeacb049a0eade7922910865b8fce912/tokenizer_config.json",
                sourceUrl: "https://huggingface.co/mlx-community/Llama-3.2-1B-Instruct-4bit/tree/08231374eeacb049a0eade7922910865b8fce912",
                licenseIdentifier: "llama3.2",
                licenseSourceUrl: "https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct/blob/9213176726f574b556790deb65791e0c5aa438b6/LICENSE.txt",
                artifactRepositorySizeBytes: 712_593_855,
                compatibilityConstraints: Self.communityTestedConstraints(
                    modelType: "llama"
                ),
                artifactContentHash: nil
            )
        case .gemma3OneB:
            .init(
                displayName: "Gemma 3 1B IT",
                baseModelId: "google/gemma-3-1b-it",
                artifactId: "mlx-community/gemma-3-1b-it-qat-4bit",
                artifactRevision: "15fed4eafb456c6fcb2a1165f19ac609670ed14b",
                modelFamily: "Gemma 3 text",
                parameterSizeClass: "small-1b",
                quantization: "4-bit",
                modelFormat: "MLX Safetensors",
                tokenizerIdentity: "mlx-community/gemma-3-1b-it-qat-4bit@15fed4eafb456c6fcb2a1165f19ac609670ed14b/tokenizer_config.json",
                sourceUrl: "https://huggingface.co/mlx-community/gemma-3-1b-it-qat-4bit/tree/15fed4eafb456c6fcb2a1165f19ac609670ed14b",
                licenseIdentifier: "gemma",
                licenseSourceUrl: "https://huggingface.co/google/gemma-3-1b-it/blob/dcc83ea841ab6100d6b47a070329e1ba4cf78752/README.md",
                artifactRepositorySizeBytes: 771_863_021,
                compatibilityConstraints: Self.communityTestedConstraints(
                    modelType: "gemma3_text"
                ),
                artifactContentHash: nil
            )
        case .granite33TwoB:
            .init(
                displayName: "Granite 3.3 2B Instruct",
                baseModelId: "ibm-granite/granite-3.3-2b-instruct",
                artifactId: "mlx-community/granite-3.3-2b-instruct-4bit",
                artifactRevision: "58246c5498495c14599525c852cfadb66c9f3084",
                modelFamily: "Granite 3.3",
                parameterSizeClass: "medium-2b",
                quantization: "4-bit",
                modelFormat: "MLX Safetensors",
                tokenizerIdentity: "mlx-community/granite-3.3-2b-instruct-4bit@58246c5498495c14599525c852cfadb66c9f3084/tokenizer_config.json",
                sourceUrl: "https://huggingface.co/mlx-community/granite-3.3-2b-instruct-4bit/tree/58246c5498495c14599525c852cfadb66c9f3084",
                licenseIdentifier: "apache-2.0",
                licenseSourceUrl: "https://huggingface.co/ibm-granite/granite-3.3-2b-instruct/blob/707f574c62054322f6b5b04b6d075f0a8f05e0f0/README.md",
                artifactRepositorySizeBytes: 1_430_233_125,
                compatibilityConstraints: Self.communityTestedConstraints(
                    modelType: "granite"
                ),
                artifactContentHash: nil
            )
        case .smolLM3ThreeB:
            .init(
                displayName: "SmolLM3 3B",
                baseModelId: "HuggingFaceTB/SmolLM3-3B",
                artifactId: "mlx-community/SmolLM3-3B-4bit",
                artifactRevision: "d3a7e0594d6642dbcfb7d149bed8b0bdf49f95ce",
                modelFamily: "SmolLM3",
                parameterSizeClass: "medium-3b",
                quantization: "4-bit",
                modelFormat: "MLX Safetensors",
                tokenizerIdentity: "mlx-community/SmolLM3-3B-4bit@d3a7e0594d6642dbcfb7d149bed8b0bdf49f95ce/tokenizer_config.json",
                sourceUrl: "https://huggingface.co/mlx-community/SmolLM3-3B-4bit/tree/d3a7e0594d6642dbcfb7d149bed8b0bdf49f95ce",
                licenseIdentifier: "apache-2.0",
                licenseSourceUrl: "https://huggingface.co/HuggingFaceTB/SmolLM3-3B/blob/a07cc9a04f16550a088caea529712d1d335b0ac1/README.md",
                artifactRepositorySizeBytes: 1_747_380_812,
                compatibilityConstraints: Self.communityTestedConstraints(
                    modelType: "smollm3"
                ),
                artifactContentHash: nil
            )
        }
    }

    private static let compatibilityConstraints = [
        "runtime:MLX-Swift-LM-3.31.4",
        "backend:MLX/Metal",
        "architecture:qwen3-dense",
        "pilot-reference-device:iPhone15,3",
        "physical-run-required-before-publication",
    ]

    private static func communityTestedConstraints(modelType: String) -> [String] {
        [
            "runtime:MLX-Swift-LM-3.31.4",
            "backend:MLX/Metal",
            "model-type:\(modelType)",
            "runtime-registry-confirmed",
            "physical-iphone-compatibility:community-tested",
            "independent-reproduction:requested",
        ]
    }
}

enum ProductionBenchmarkPlan: String, CaseIterable, Identifiable, Sendable {
    case sustainedGeneration = "suite-b-pilot-001"
    case shortInteraction = "b-ux-001-short-interaction"

    var id: String { rawValue }

    var title: String {
        switch self {
        case .sustainedGeneration:
            "B-PIPE-001 · Sustained Generation"
        case .shortInteraction:
            "B-UX-001 · Short Interaction"
        }
    }

    var workloadID: String {
        switch self {
        case .sustainedGeneration:
            "b-pipe-001-sustained-generation"
        case .shortInteraction:
            "b-ux-001-short-interaction"
        }
    }
}

struct PilotPlan: Codable, Sendable, Equatable {
    let planSchemaVersion: String
    let planId: String
    let planVersion: String
    let status: String
    let modelProfile: ModelProfile
    let runtimeProfile: RuntimeProfile
    let workload: Workload
    let generation: Generation
    let measurementMode: MeasurementMode
    let procedure: Procedure
    let environmentRequirements: EnvironmentRequirements

    struct ModelProfile: Codable, Sendable, Equatable {
        let displayName: String
        let baseModelId: String
        let artifactId: String
        let artifactRevision: String
        let modelFamily: String
        let parameterSizeClass: String
        let quantization: String
        let modelFormat: String
        let tokenizerIdentity: String
        let sourceUrl: String
        let licenseIdentifier: String
        let licenseSourceUrl: String
        let artifactRepositorySizeBytes: Int64
        let compatibilityConstraints: [String]
        let artifactContentHash: String?
    }

    struct RuntimeProfile: Codable, Sendable, Equatable {
        let runtimeName: String
        let packageVersion: String
        let packageRevision: String
        let mlxSwiftVersion: String
        let mlxSwiftRevision: String
        let backend: String
        let downloaderPackage: String
        let tokenizerPackage: String
    }

    struct Workload: Codable, Sendable, Equatable {
        let workloadId: String
        let workloadVersion: String
        let v2ProfileMapping: String
        let category: String
        let promptPath: String
        let promptSha256: String
        let outputTokenLimit: Int
    }

    struct Generation: Codable, Sendable, Equatable {
        let samplingEnabled: Bool
        let temperature: Double
        let topP: Double?
        let topK: Int?
        let seed: UInt64?
        let repetitionPenalty: Double?
        let thinkingMode: String
        let chatTemplateIdentity: String
        let includeStopTokenInRawEvents: Bool
        let contextPolicy: String
        let modelLoadPolicy: String
        let kvCachePolicy: String
    }

    struct MeasurementMode: Codable, Sendable, Equatable {
        let measurementModeId: String
        let timingBoundaryVersion: String
        let pipelineTtftStart: String
        let pipelineTtftEnd: String
        let userVisibleTtftAvailable: Bool
        let prefillSource: String
        let decodeFormula: String
        let memoryMetric: String
        let memorySamplingIntervalMilliseconds: Int
    }

    struct Procedure: Codable, Sendable, Equatable {
        let warmupRuns: Int
        let measuredRuns: Int
        let minimumSuccessfulRunsForSummary: Int
        let restIntervalSeconds: Int
    }

    struct EnvironmentRequirements: Codable, Sendable, Equatable {
        let releaseBuildRequired: Bool
        let debuggerDetachedRequired: Bool
        let initialThermalState: String
        let lowPowerMode: String
        let requiredPowerSource: String
        let minimumBatteryLevelPercent: Double
    }
}

struct LoadedPilotPlan: Sendable {
    let plan: PilotPlan
    let prompt: String
}

enum PilotPlanLoader {
    enum PlanError: LocalizedError, Equatable {
        case planMissing
        case promptMissing(String)
        case promptHashMismatch(expected: String, actual: String)
        case unsupportedPlan(String)

        var errorDescription: String? {
            switch self {
            case .planMissing:
                "The bundled Suite B Pilot plan is missing."
            case .promptMissing(let path):
                "The Pilot prompt is missing: \(path)"
            case .promptHashMismatch(let expected, let actual):
                "Prompt hash mismatch. Expected \(expected), got \(actual)."
            case .unsupportedPlan(let reason):
                "Unsupported Pilot plan: \(reason)"
            }
        }
    }

    static func load(
        resource: String = "suite-b-pilot-001",
        modelProfile: ProductionModelProfile = .small,
        bundle: Bundle = .main
    ) throws -> LoadedPilotPlan {
        guard let planURL = bundle.url(
            forResource: resource,
            withExtension: "json"
        ) else {
            throw PlanError.planMissing
        }
        let data = try Data(contentsOf: planURL)
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let decodedPlan = try decoder.decode(PilotPlan.self, from: data)
        let plan = PilotPlan(
            planSchemaVersion: decodedPlan.planSchemaVersion,
            planId: decodedPlan.planId,
            planVersion: decodedPlan.planVersion,
            status: decodedPlan.status,
            modelProfile: modelProfile.planModelProfile,
            runtimeProfile: decodedPlan.runtimeProfile,
            workload: decodedPlan.workload,
            generation: decodedPlan.generation,
            measurementMode: decodedPlan.measurementMode,
            procedure: decodedPlan.procedure,
            environmentRequirements: decodedPlan.environmentRequirements
        )
        try validateIdentity(plan)

        let promptName = URL(fileURLWithPath: plan.workload.promptPath)
            .deletingPathExtension().lastPathComponent
        let promptExtension = URL(fileURLWithPath: plan.workload.promptPath)
            .pathExtension
        guard let promptURL = bundle.url(
            forResource: promptName,
            withExtension: promptExtension
        ) else {
            throw PlanError.promptMissing(plan.workload.promptPath)
        }
        let promptData = try Data(contentsOf: promptURL)
        try validatePromptHash(
            promptData,
            expected: plan.workload.promptSha256
        )
        guard let prompt = String(data: promptData, encoding: .utf8) else {
            throw CocoaError(.fileReadInapplicableStringEncoding)
        }
        return LoadedPilotPlan(plan: plan, prompt: prompt)
    }

    static func validatePromptHash(_ data: Data, expected: String) throws {
        let actual = SHA256.hash(data: data).map {
            String(format: "%02x", $0)
        }.joined()
        guard actual == expected else {
            throw PlanError.promptHashMismatch(expected: expected, actual: actual)
        }
    }

    static func validateIdentity(_ plan: PilotPlan) throws {
        guard plan.planSchemaVersion == "0.3" else {
            throw PlanError.unsupportedPlan(
                "unexpected plan schema \(plan.planSchemaVersion)"
            )
        }
        let supported = [
            ("b-pipe-001-validation", "1.0.0-rc.1", "b-pipe-001-sustained-generation"),
            ("b-ux-001-validation", "1.0.0-rc.1", "b-ux-001-short-interaction"),
        ]
        guard supported.contains(where: {
            $0.0 == plan.planId && $0.1 == plan.planVersion
                && $0.2 == plan.workload.workloadId
        }) else {
            throw PlanError.unsupportedPlan(
                "unexpected plan identity \(plan.planId)@\(plan.planVersion)"
            )
        }
    }
}
