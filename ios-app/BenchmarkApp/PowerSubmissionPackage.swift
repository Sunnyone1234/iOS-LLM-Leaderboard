import CryptoKit
import Foundation

enum SubmissionConflictCategory: String, CaseIterable, Identifiable, Sendable {
    case none
    case modelAffiliated = "model-affiliated"
    case runtimeAffiliated = "runtime-affiliated"
    case hardwareAffiliated = "hardware-affiliated"
    case otherDisclosed = "other-disclosed"

    var id: String { rawValue }

    var title: String {
        switch self {
        case .none: "None"
        case .modelAffiliated: "Model affiliated"
        case .runtimeAffiliated: "Runtime affiliated"
        case .hardwareAffiliated: "Hardware affiliated"
        case .otherDisclosed: "Other disclosed"
        }
    }
}

enum SubmissionThermalAssistance: String, CaseIterable, Identifiable, Sendable {
    case none
    case deliberateCooling = "deliberate-cooling"
    case deliberateHeating = "deliberate-heating"
    case otherAssisted = "other-assisted"
    case unknown

    var id: String { rawValue }

    var title: String {
        switch self {
        case .none: "None"
        case .deliberateCooling: "Deliberate cooling"
        case .deliberateHeating: "Deliberate heating"
        case .otherAssisted: "Other assistance"
        case .unknown: "Unknown"
        }
    }
}

struct PowerSubmissionPackage: Sendable {
    let submissionID: UUID
    let manifestData: Data
    let resultData: Data

    var repositoryDirectory: String {
        "submissions/suite-b/power-1.1.0/draft/\(submissionID.uuidString.lowercased())"
    }

    enum PackageError: LocalizedError {
        case invalidGitHubHandle
        case missingConflictStatement
        case resultBytesChanged

        var errorDescription: String? {
            switch self {
            case .invalidGitHubHandle:
                "The authenticated GitHub handle is not valid for the submission schema."
            case .missingConflictStatement:
                "Describe the disclosed conflict of interest before submitting."
            case .resultBytesChanged:
                "The saved result no longer matches the completed in-memory result."
            }
        }
    }

    private struct Manifest: Encodable {
        let schemaVersion = "suite-b-power-submission-1.1.0"
        let submissionID: String
        let createdAt: Date
        let benchmarkRelease = BenchmarkRelease()
        let state = "draft"
        let requestedEvidenceLevel = "community-submitted"
        let contributor: Contributor
        let conflictOfInterest: ConflictOfInterest
        let environmentalDisclosure: EnvironmentalDisclosure
        let declarations = Declarations()
        let result: ResultReference

        struct BenchmarkRelease: Encodable {
            let id = "suite-b-power"
            let version = "1.1.0"
        }

        struct Contributor: Encodable {
            let githubHandle: String
        }

        struct ConflictOfInterest: Encodable {
            let category: String
            let statement: String
        }

        struct EnvironmentalDisclosure: Encodable {
            let thermalAssistance: String
            let notes: String?
        }

        struct Declarations: Encodable {
            let ranOnPhysicalDevice = true
            let authorizedToSubmit = true
            let reviewedPublicMetadata = true
            let rawResultUnmodified = true
            let containsNoPersonalData = true
            let acceptsCCBY40 = true
            let understandsNoRankingGuarantee = true
        }

        struct ResultReference: Encodable {
            let path = "result.json"
            let sha256: String
            let schemaVersion: String
            let resultID: String
            let workloadID: String
            let artifactID: String
            let artifactRevision: String
            let runtimeName: String
            let runtimeVersion: String
            let machineIdentifier: String
        }
    }

    static func make(
        result: PowerResultBundle,
        resultURL: URL,
        githubHandle: String,
        conflictCategory: SubmissionConflictCategory,
        conflictStatement: String,
        thermalAssistance: SubmissionThermalAssistance,
        environmentNotes: String?,
        submissionID: UUID = UUID(),
        createdAt: Date = Date()
    ) throws -> PowerSubmissionPackage {
        try result.validateForExport()
        let handlePattern = #"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$"#
        guard githubHandle.range(
            of: handlePattern,
            options: .regularExpression
        ) != nil else {
            throw PackageError.invalidGitHubHandle
        }
        let statement = conflictStatement.trimmingCharacters(
            in: .whitespacesAndNewlines
        )
        guard conflictCategory == .none || !statement.isEmpty else {
            throw PackageError.missingConflictStatement
        }

        let resultData = try Data(contentsOf: resultURL)
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        guard try encoder.encode(result) == resultData else {
            throw PackageError.resultBytesChanged
        }
        guard let rawResult = try JSONSerialization.jsonObject(
            with: resultData
        ) as? [String: Any],
              let rawResultID = rawResult["resultID"] as? String,
              UUID(uuidString: rawResultID) == result.resultID else {
            throw PackageError.resultBytesChanged
        }
        let digest = SHA256.hash(data: resultData)
            .map { String(format: "%02x", $0) }
            .joined()
        let notes = environmentNotes?.trimmingCharacters(
            in: .whitespacesAndNewlines
        )
        let manifest = Manifest(
            submissionID: submissionID.uuidString.lowercased(),
            createdAt: createdAt,
            contributor: .init(githubHandle: githubHandle),
            conflictOfInterest: .init(
                category: conflictCategory.rawValue,
                statement: conflictCategory == .none
                    ? "No conflict of interest disclosed."
                    : statement
            ),
            environmentalDisclosure: .init(
                thermalAssistance: thermalAssistance.rawValue,
                notes: notes?.isEmpty == false ? notes : nil
            ),
            result: .init(
                sha256: digest,
                schemaVersion: result.schemaVersion,
                resultID: rawResultID,
                workloadID: result.execution.workloadID,
                artifactID: result.model.artifactID,
                artifactRevision: result.model.artifactRevision,
                runtimeName: result.runtime.name,
                runtimeVersion: result.runtime.version,
                machineIdentifier: result.device.machineIdentifier
            )
        )
        return PowerSubmissionPackage(
            submissionID: submissionID,
            manifestData: try encoder.encode(manifest),
            resultData: resultData
        )
    }
}
