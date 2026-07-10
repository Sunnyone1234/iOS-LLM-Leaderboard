import CryptoKit
import Foundation

struct PilotPlan: Decodable, Sendable, Equatable {
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

    struct ModelProfile: Decodable, Sendable, Equatable {
        let displayName: String
        let baseModelId: String
        let artifactId: String
        let artifactRevision: String
        let quantization: String
        let modelFormat: String
        let artifactContentHash: String?
    }

    struct RuntimeProfile: Decodable, Sendable, Equatable {
        let runtimeName: String
        let packageVersion: String
        let packageRevision: String
        let mlxSwiftVersion: String
        let mlxSwiftRevision: String
        let backend: String
        let downloaderPackage: String
        let tokenizerPackage: String
    }

    struct Workload: Decodable, Sendable, Equatable {
        let workloadId: String
        let workloadVersion: String
        let v2ProfileMapping: String
        let category: String
        let promptPath: String
        let promptSha256: String
        let outputTokenLimit: Int
    }

    struct Generation: Decodable, Sendable, Equatable {
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

    struct MeasurementMode: Decodable, Sendable, Equatable {
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

    struct Procedure: Decodable, Sendable, Equatable {
        let warmupRuns: Int
        let measuredRuns: Int
        let minimumSuccessfulRunsForSummary: Int
        let restIntervalSeconds: Int
    }

    struct EnvironmentRequirements: Decodable, Sendable, Equatable {
        let releaseBuildRequired: Bool
        let debuggerDetachedRequired: Bool
        let initialThermalState: String
        let lowPowerMode: String
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

    static func load(bundle: Bundle = .main) throws -> LoadedPilotPlan {
        guard let planURL = bundle.url(
            forResource: "suite-b-pilot-001",
            withExtension: "json"
        ) else {
            throw PlanError.planMissing
        }
        let data = try Data(contentsOf: planURL)
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let plan = try decoder.decode(PilotPlan.self, from: data)
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
        guard plan.planId == "suite-b-pilot-001" else {
            throw PlanError.unsupportedPlan("unexpected plan ID \(plan.planId)")
        }
        guard plan.planVersion == "0.3.0" else {
            throw PlanError.unsupportedPlan("unexpected plan version \(plan.planVersion)")
        }
        guard plan.workload.workloadId == "suite-b-pilot-001-fixed-generation" else {
            throw PlanError.unsupportedPlan(
                "unexpected workload ID \(plan.workload.workloadId)"
            )
        }
    }
}
