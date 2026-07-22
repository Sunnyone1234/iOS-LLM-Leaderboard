import CryptoKit
import Foundation

struct PowerRunnerIdentity: Sendable, Equatable {
    let runnerID: String
    let runnerVersion: String
    let appVersion: String
    let appBuild: String
    let appSourceCommit: String
    let runtime: PowerRuntimeIdentity

    init(
        runnerID: String,
        runnerVersion: String,
        appVersion: String,
        appBuild: String,
        appSourceCommit: String,
        runtime: PowerRuntimeIdentity
    ) {
        self.runnerID = runnerID
        self.runnerVersion = runnerVersion
        self.appVersion = appVersion
        self.appBuild = appBuild
        self.appSourceCommit = appSourceCommit
        self.runtime = runtime
    }

    init?(plan: PilotPlan) {
        guard let sourceCommit = BuildMetadata.sourceCommit else { return nil }
        runnerID = PowerBenchmarkRelease.runnerID
        runnerVersion = BuildMetadata.appVersion
        appVersion = BuildMetadata.appVersion
        appBuild = BuildMetadata.appBuild
        appSourceCommit = sourceCommit
        runtime = PowerRuntimeIdentity(
            name: plan.runtimeProfile.runtimeName,
            version: plan.runtimeProfile.packageVersion,
            resolvedRevision: plan.runtimeProfile.packageRevision,
            backend: plan.runtimeProfile.backend,
            dependencyVersions: [
                "mlx-swift": "\(plan.runtimeProfile.mlxSwiftVersion)@\(plan.runtimeProfile.mlxSwiftRevision)",
                "swift-huggingface": plan.runtimeProfile.downloaderPackage,
                "swift-transformers": plan.runtimeProfile.tokenizerPackage,
            ]
        )
    }

    init(result: PowerResultBundle) {
        runnerID = result.execution.runnerID
        runnerVersion = result.execution.runnerVersion
        appVersion = result.execution.appVersion
        appBuild = result.execution.appBuild
        appSourceCommit = result.execution.appSourceCommit
        runtime = PowerRuntimeIdentity(
            name: result.runtime.name,
            version: result.runtime.version,
            resolvedRevision: result.runtime.resolvedRevision,
            backend: result.runtime.backend,
            dependencyVersions: result.runtime.dependencyVersions
        )
    }
}

struct PowerRuntimeIdentity: Codable, Sendable, Equatable {
    let name: String
    let version: String
    let resolvedRevision: String
    let backend: String
    let dependencyVersions: [String: String]
}

struct PowerCompatibilityPolicy: Codable, Sendable, Equatable {
    struct BenchmarkRelease: Codable, Sendable, Equatable {
        struct SourceRelease: Codable, Sendable, Equatable {
            let id: String
            let version: String
        }

        let id: String
        let policyVersion: String
        let sourceRelease: SourceRelease
    }

    struct ApprovedRunner: Codable, Sendable, Equatable {
        let approvalID: String
        let kind: String
        let runnerID: String
        let runnerVersion: String
        let appVersion: String
        let appBuild: String
        let appSourceCommit: String
        let runtime: PowerRuntimeIdentity

        func matches(_ identity: PowerRunnerIdentity) -> Bool {
            runnerID == identity.runnerID
                && runnerVersion == identity.runnerVersion
                && appVersion == identity.appVersion
                && appBuild == identity.appBuild
                && appSourceCommit == identity.appSourceCommit
                && runtime == identity.runtime
        }
    }

    let schemaVersion: String
    let policyID: String
    let policyVersion: String
    let status: String
    let benchmarkRelease: BenchmarkRelease
    let protocolSemanticsChanged: Bool
    let resultSchemaChanged: Bool
    let rawEvidenceMutationAllowed: Bool
    let approvedRunners: [ApprovedRunner]

    func approval(for identity: PowerRunnerIdentity) -> ApprovedRunner? {
        approvedRunners.first { $0.matches(identity) }
    }

    func validateForPowerOneOne() throws {
        guard policyID == "suite-b-power-runner-compatibility",
              status == "published",
              benchmarkRelease.id == "suite-b-power",
              benchmarkRelease.policyVersion == policyVersion,
              benchmarkRelease.sourceRelease.id == "suite-b-power",
              benchmarkRelease.sourceRelease.version == "1.1.0",
              !protocolSemanticsChanged,
              !resultSchemaChanged,
              !rawEvidenceMutationAllowed,
              !approvedRunners.isEmpty else {
            throw PowerCompatibilityPolicyError.invalidPolicy
        }
    }
}

struct PowerCompatibilityPolicyIndex: Codable, Sendable, Equatable {
    struct CurrentPolicy: Codable, Sendable, Equatable {
        let policyVersion: String
        let path: String
        let sha256: String
    }

    let schemaVersion: String
    let currentPolicy: CurrentPolicy
}

enum PowerEligibility: Sendable, Equatable {
    case checking
    case approved(policyVersion: String, approvalID: String)
    case notApproved(policyVersion: String)
    case unavailable(message: String)
    case noResult

    var isApproved: Bool {
        if case .approved = self { return true }
        return false
    }
}

protocol PowerCompatibilityPolicyFetching: Sendable {
    func fetchCurrentPolicy() async throws -> PowerCompatibilityPolicy
}

struct GitHubPowerCompatibilityPolicyClient: PowerCompatibilityPolicyFetching {
    static let indexURL = URL(
        string: "https://raw.githubusercontent.com/YizeSun/iOS-LLM-Leaderboard/main/benchmarks/suite-b-on-device-performance/power-compatible-runners-current.json"
    )!
    private static let repositoryRoot = URL(
        string: "https://raw.githubusercontent.com/YizeSun/iOS-LLM-Leaderboard/main/"
    )!

    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func fetchCurrentPolicy() async throws -> PowerCompatibilityPolicy {
        let indexData = try await fetch(Self.indexURL)
        let index = try JSONDecoder().decode(
            PowerCompatibilityPolicyIndex.self,
            from: indexData
        )
        guard index.schemaVersion
                == "suite-b-power-compatible-runners-index-1.0",
              index.currentPolicy.path.hasPrefix(
                "benchmarks/suite-b-on-device-performance/"
              ),
              !index.currentPolicy.path.contains(".."),
              index.currentPolicy.sha256.count == 64 else {
            throw PowerCompatibilityPolicyError.invalidIndex
        }

        let policyURL = Self.repositoryRoot.appending(
            path: index.currentPolicy.path
        )
        let policyData = try await fetch(policyURL)
        let digest = SHA256.hash(data: policyData)
            .map { String(format: "%02x", $0) }
            .joined()
        guard digest == index.currentPolicy.sha256.lowercased() else {
            throw PowerCompatibilityPolicyError.hashMismatch
        }

        let policy = try JSONDecoder().decode(
            PowerCompatibilityPolicy.self,
            from: policyData
        )
        try policy.validateForPowerOneOne()
        guard policy.policyVersion == index.currentPolicy.policyVersion else {
            throw PowerCompatibilityPolicyError.versionMismatch
        }
        return policy
    }

    private func fetch(_ url: URL) async throws -> Data {
        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.timeoutInterval = 20
        request.setValue(
            "BenchmarkApp/\(BuildMetadata.appVersion)",
            forHTTPHeaderField: "User-Agent"
        )
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse,
              response.statusCode == 200 else {
            throw PowerCompatibilityPolicyError.unavailable
        }
        return data
    }
}

enum PowerCompatibilityPolicyError: LocalizedError {
    case unavailable
    case invalidIndex
    case hashMismatch
    case invalidPolicy
    case versionMismatch

    var errorDescription: String? {
        switch self {
        case .unavailable:
            "The current Power compatibility policy could not be downloaded."
        case .invalidIndex:
            "The Power compatibility-policy index is invalid."
        case .hashMismatch:
            "The downloaded Power compatibility policy failed its SHA-256 check."
        case .invalidPolicy:
            "The downloaded policy is not a valid published Power 1.1 compatibility policy."
        case .versionMismatch:
            "The compatibility-policy index and policy version do not match."
        }
    }
}
