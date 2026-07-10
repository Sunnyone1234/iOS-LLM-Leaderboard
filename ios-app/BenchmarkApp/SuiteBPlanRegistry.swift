import Foundation

struct SuiteBPlanRegistry: Decodable, Sendable, Equatable {
    let schemaVersion: String
    let plans: [Plan]

    struct Plan: Decodable, Sendable, Equatable {
        let planId: String
        let planVersion: String
        let workloadId: String
        let workloadVersion: String
        let category: String
        let runnerKind: String
        let thinkingMode: String
        let userVisibleTtftAvailable: Bool
        let warmupRuns: Int
        let measuredRuns: Int
        let outputTokenLimit: Int
        let targetInputTokens: [Int]
        let fixtureSha256: [String]
    }

    func plan(workloadID: String) -> Plan? {
        plans.first { $0.workloadId == workloadID }
    }
}

enum SuiteBPlanRegistryLoader {
    enum RegistryError: LocalizedError {
        case missing
        case unsupportedSchema(String)
        case duplicateWorkload(String)
        case invalidPlan(String)

        var errorDescription: String? {
            switch self {
            case .missing: "The bundled Suite B workload registry is missing."
            case .unsupportedSchema(let value): "Unsupported Suite B registry schema: \(value)."
            case .duplicateWorkload(let value): "Duplicate Suite B workload: \(value)."
            case .invalidPlan(let value): "Invalid Suite B workload plan: \(value)."
            }
        }
    }

    static func load(bundle: Bundle = .main) throws -> SuiteBPlanRegistry {
        guard let url = bundle.url(
            forResource: "suite-b-workload-registry",
            withExtension: "json"
        ) else { throw RegistryError.missing }
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let registry = try decoder.decode(
            SuiteBPlanRegistry.self,
            from: Data(contentsOf: url)
        )
        guard registry.schemaVersion == "suite-b-plan-registry-0.1" else {
            throw RegistryError.unsupportedSchema(registry.schemaVersion)
        }
        var ids: Set<String> = []
        for plan in registry.plans {
            guard ids.insert(plan.workloadId).inserted else {
                throw RegistryError.duplicateWorkload(plan.workloadId)
            }
            guard plan.warmupRuns >= 0,
                  plan.measuredRuns > 0,
                  plan.outputTokenLimit > 0,
                  plan.targetInputTokens.count == plan.fixtureSha256.count
                    || plan.targetInputTokens.isEmpty && plan.fixtureSha256.count == 1,
                  plan.fixtureSha256.allSatisfy({ $0.count == 64 }) else {
                throw RegistryError.invalidPlan(plan.workloadId)
            }
        }
        return registry
    }
}
