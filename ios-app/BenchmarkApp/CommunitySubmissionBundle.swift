import CryptoKit
import Foundation

struct CommunitySubmissionBundle: Codable, Sendable {
    let schemaVersion: String
    let submissionID: String
    let createdAt: Date
    let currentTrustLevel: String
    let requestedTrustLevel: String
    let validationStatus: String
    let contributor: Contributor
    let declarations: Declarations
    let privacy: Privacy
    let result: ResultReference

    struct Contributor: Codable, Sendable { let displayName: String }
    struct Declarations: Codable, Sendable {
        let reviewedResult: Bool
        let confirmsNoPersonalData: Bool
        let agreesToRepositoryLicense: Bool
    }
    struct Privacy: Codable, Sendable {
        let excludedIdentifiers: [String]
        let includedPublicDeviceFields: [String]
    }
    struct ResultReference: Codable, Sendable {
        let schemaVersion: String
        let resultID: String
        let workloadID: String
        let artifactID: String
        let machineIdentifier: String
        let encoding: String
        let digestAlgorithm: String
        let sha256: String
        let bundleBase64: String
    }

    static func make(
        result: SuiteBResultBundle,
        contributorName: String,
        declarations: Declarations
    ) throws -> CommunitySubmissionBundle {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        let bytes = try encoder.encode(result)
        let digest = SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined()
        return CommunitySubmissionBundle(
            schemaVersion: "suite-b-community-submission-0.1",
            submissionID: UUID().uuidString.lowercased(),
            createdAt: Date(),
            currentTrustLevel: "draft",
            requestedTrustLevel: "community-submitted",
            validationStatus: "unvalidated",
            contributor: .init(displayName: contributorName.trimmingCharacters(in: .whitespacesAndNewlines)),
            declarations: declarations,
            privacy: .init(
                excludedIdentifiers: ["apple-id", "serial-number", "udid", "user-documents", "personal-prompts"],
                includedPublicDeviceFields: ["device-model", "machine-identifier", "os-version", "os-build"]
            ),
            result: .init(
                schemaVersion: result.schemaVersion,
                resultID: result.resultID,
                workloadID: result.workload.id,
                artifactID: result.model.artifactID,
                machineIdentifier: result.device.machineIdentifier,
                encoding: "base64-json",
                digestAlgorithm: "sha256",
                sha256: digest,
                bundleBase64: bytes.base64EncodedString()
            )
        )
    }
}
