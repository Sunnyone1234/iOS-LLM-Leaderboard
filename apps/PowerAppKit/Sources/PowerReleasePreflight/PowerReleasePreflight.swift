import CryptoKit
import Foundation

public struct PowerReleaseDeclaration: Equatable, Sendable {
    public let stackID: String
    public let appVersion: String
    public let appBuild: String
    public let appSourceRevision: String
    public let embeddedMeasurementStackSHA256: String
    public let runnerCertificateID: String
    public let bundleIdentifier: String

    public init(
        stackID: String,
        appVersion: String,
        appBuild: String,
        appSourceRevision: String,
        embeddedMeasurementStackSHA256: String,
        runnerCertificateID: String,
        bundleIdentifier: String
    ) {
        self.stackID = stackID
        self.appVersion = appVersion
        self.appBuild = appBuild
        self.appSourceRevision = appSourceRevision
        self.embeddedMeasurementStackSHA256 =
            embeddedMeasurementStackSHA256
        self.runnerCertificateID = runnerCertificateID
        self.bundleIdentifier = bundleIdentifier
    }
}

public enum PowerReleaseEligibility: Equatable, Sendable {
    case notRequired
    case checking
    case releaseCandidate
    case current
    case updateRequired(String)
    case unavailable(String)

    public var permitsOfficialUse: Bool {
        self == .current || self == .releaseCandidate
    }

    public var message: String? {
        switch self {
        case .notRequired, .releaseCandidate, .current:
            nil
        case .checking:
            "Checking the current Power release…"
        case .updateRequired(let message), .unavailable(let message):
            message
        }
    }
}

public struct PowerReleasePreflight: Sendable {
    public typealias Fetch = @Sendable (URL) async throws -> Data

    public static let defaultRepositoryRoot = URL(
        string: "https://raw.githubusercontent.com/"
            + "YizeSun/iOS-LLM-Leaderboard/main/"
    )!

    private let repositoryRootURL: URL
    private let fetch: Fetch

    public init(
        repositoryRootURL: URL = PowerReleasePreflight.defaultRepositoryRoot
    ) {
        self.repositoryRootURL = repositoryRootURL
        fetch = { url in
            let (data, response) = try await URLSession.shared.data(from: url)
            guard
                let http = response as? HTTPURLResponse,
                (200..<300).contains(http.statusCode)
            else {
                throw PreflightError.remoteResponseInvalid
            }
            return data
        }
    }

    public init(
        repositoryRootURL: URL,
        fetch: @escaping Fetch
    ) {
        self.repositoryRootURL = repositoryRootURL
        self.fetch = fetch
    }

    public func check(
        declaration: PowerReleaseDeclaration
    ) async -> PowerReleaseEligibility {
        do {
            let pointerData = try await fetch(
                repositoryURL(for: "products/power/current.json")
            )
            let pointer = try JSONDecoder().decode(
                CurrentPointer.self,
                from: pointerData
            )
            guard
                pointer.schemaVersion == "power-stack-pointer-1.0.0",
                pointer.productID == "power"
            else {
                throw PreflightError.authorityDocumentInvalid
            }
            guard
                pointer.status == "active",
                pointer.publicIntakeOpen
            else {
                return .updateRequired(
                    "Public Power intake is not currently active. "
                        + "Testing and submission are paused."
                )
            }
            guard pointer.stackID == declaration.stackID else {
                return .updateRequired(
                    "A newer Power measurement stack is active. "
                        + "Update the App before testing or submitting."
                )
            }

            let releaseData = try await fetch(
                repositoryURL(for: pointer.appRelease.path)
            )
            guard sha256(releaseData) == pointer.appRelease.sha256 else {
                throw PreflightError.authorityDigestMismatch
            }
            let release = try JSONDecoder().decode(
                AppRelease.self,
                from: releaseData
            )
            guard
                release.schemaVersion == "power-app-release-1.0.0",
                release.productID == "power"
            else {
                throw PreflightError.authorityDocumentInvalid
            }
            guard release.state == "supported" else {
                return .updateRequired(
                    "This Power App release is no longer supported. "
                        + "Update before testing or submitting."
                )
            }
            guard
                release.version == declaration.appVersion,
                release.build == declaration.appBuild,
                release.sourceRevision
                    == declaration.appSourceRevision,
                release.bundleIdentifier
                    == declaration.bundleIdentifier,
                release.embeddedMeasurementStack.sha256
                    == declaration.embeddedMeasurementStackSHA256,
                release.supportedRunnerCertificateIDs.contains(
                    declaration.runnerCertificateID
                ),
                pointer.runnerCertificate.path
                    .hasSuffix(
                        "/\(declaration.runnerCertificateID).json"
                    )
            else {
                return .updateRequired(
                    "This source-built App does not declare the current "
                        + "supported release identity. Update the repository "
                        + "and rebuild before testing or submitting."
                )
            }
            return .current
        } catch {
            return .unavailable(
                "The current Power release could not be verified from the "
                    + "trusted repository. Connect to the network and retry; "
                    + "testing and submission remain locked."
            )
        }
    }

    private func repositoryURL(for path: String) throws -> URL {
        let components = path.split(
            separator: "/",
            omittingEmptySubsequences: false
        )
        guard
            !path.hasPrefix("/"),
            !components.isEmpty,
            components.allSatisfy({
                !$0.isEmpty && $0 != "." && $0 != ".."
            })
        else {
            throw PreflightError.authorityPathInvalid
        }
        return repositoryRootURL.appending(path: path)
    }

    private func sha256(_ data: Data) -> String {
        SHA256.hash(data: data).map {
            String(format: "%02x", $0)
        }.joined()
    }
}

private extension PowerReleasePreflight {
    struct Reference: Decodable {
        let path: String
        let sha256: String
    }

    struct CurrentPointer: Decodable {
        let schemaVersion: String
        let productID: String
        let status: String
        let publicIntakeOpen: Bool
        let stackID: String
        let appRelease: Reference
        let runnerCertificate: Reference
    }

    struct AppRelease: Decodable {
        let schemaVersion: String
        let productID: String
        let state: String
        let version: String
        let build: String
        let bundleIdentifier: String
        let sourceRevision: String
        let embeddedMeasurementStack: Reference
        let supportedRunnerCertificateIDs: [String]
    }

    enum PreflightError: Error {
        case remoteResponseInvalid
        case authorityDocumentInvalid
        case authorityDigestMismatch
        case authorityPathInvalid
    }
}
