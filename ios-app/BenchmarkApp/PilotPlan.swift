import CryptoKit
import Foundation

enum ProductionModelProfile: String, CaseIterable, Identifiable, Sendable {
    case small = "qwen3-0.6b-4bit"
    case medium = "qwen3-1.7b-4bit"
    case large = "qwen3-4b-3bit"

    var id: String { rawValue }

    var title: String {
        switch self {
        case .small: "Qwen3 0.6B · 4-bit · Small"
        case .medium: "Qwen3 1.7B · 4-bit · Medium"
        case .large: "Qwen3 4B · 3-bit · Larger"
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
        }
    }

    private static let compatibilityConstraints = [
        "runtime:MLX-Swift-LM-3.31.4",
        "backend:MLX/Metal",
        "architecture:qwen3-dense",
        "pilot-reference-device:iPhone15,3",
        "physical-run-required-before-publication",
    ]
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
