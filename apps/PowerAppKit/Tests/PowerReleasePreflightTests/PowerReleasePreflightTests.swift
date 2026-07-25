import CryptoKit
import Foundation
import PowerReleasePreflight
import Testing

struct PowerReleasePreflightTests {
    private let root = URL(string: "https://example.invalid/repository/")!

    @Test
    func closedReleaseCandidatePermitsMeasurementWithoutSubmissionAuthority() {
        #expect(PowerReleaseEligibility.releaseCandidate.permitsOfficialUse)
        #expect(PowerReleaseEligibility.releaseCandidate.message == nil)
    }

    @Test
    func matchingSupportedReleaseIsCurrent() async {
        let fixture = Fixture()
        let checker = makeChecker(fixture.files)

        #expect(
            await checker.check(declaration: fixture.declaration)
                == .current
        )
    }

    @Test
    func mismatchedLocalBuildRequiresUpdate() async {
        let fixture = Fixture()
        let checker = makeChecker(fixture.files)
        let declaration = PowerReleaseDeclaration(
            stackID: fixture.declaration.stackID,
            appVersion: fixture.declaration.appVersion,
            appBuild: "older-build",
            appSourceRevision:
                fixture.declaration.appSourceRevision,
            embeddedMeasurementStackSHA256:
                fixture.declaration.embeddedMeasurementStackSHA256,
            runnerCertificateID:
                fixture.declaration.runnerCertificateID,
            bundleIdentifier:
                fixture.declaration.bundleIdentifier
        )

        let result = await checker.check(declaration: declaration)
        guard case .updateRequired = result else {
            Issue.record("Expected an update requirement, got \(result)")
            return
        }
    }

    @Test
    func closedIntakeLocksTesting() async {
        let fixture = Fixture(publicIntakeOpen: false)
        let result = await makeChecker(fixture.files).check(
            declaration: fixture.declaration
        )

        guard case .updateRequired(let message) = result else {
            Issue.record("Expected an intake lock, got \(result)")
            return
        }
        #expect(message.contains("not currently active"))
    }

    @Test
    func tamperedReleaseDocumentFailsClosed() async {
        var fixture = Fixture()
        fixture.files["products/power/app-releases/current.json"] =
            Data("{}".utf8)

        let result = await makeChecker(fixture.files).check(
            declaration: fixture.declaration
        )
        guard case .unavailable = result else {
            Issue.record("Expected unavailable, got \(result)")
            return
        }
    }

    @Test
    func networkFailureFailsClosed() async {
        let checker = PowerReleasePreflight(
            repositoryRootURL: root
        ) { _ in
            throw TestError.offline
        }

        let result = await checker.check(
            declaration: Fixture().declaration
        )
        guard case .unavailable(let message) = result else {
            Issue.record("Expected unavailable, got \(result)")
            return
        }
        #expect(message.contains("remain locked"))
    }

    private func makeChecker(
        _ files: [String: Data]
    ) -> PowerReleasePreflight {
        PowerReleasePreflight(repositoryRootURL: root) { url in
            let prefix = root.absoluteString
            let absolute = url.absoluteString
            guard
                absolute.hasPrefix(prefix),
                let data = files[
                    String(absolute.dropFirst(prefix.count))
                ]
            else {
                throw TestError.missingFixture
            }
            return data
        }
    }
}

private struct Fixture {
    let declaration = PowerReleaseDeclaration(
        stackID: "power-text-iphone-2.0.0-rc.1",
        appVersion: "2.0.0",
        appBuild: "4",
        appSourceRevision: String(repeating: "a", count: 64),
        embeddedMeasurementStackSHA256:
            String(repeating: "b", count: 64),
        runnerCertificateID: "power2-runner-example",
        bundleIdentifier: "org.example.power"
    )
    var files: [String: Data]

    init(publicIntakeOpen: Bool = true) {
        let release = Data(
            """
            {
              "schemaVersion": "power-app-release-1.0.0",
              "productID": "power",
              "state": "supported",
              "version": "2.0.0",
              "build": "4",
              "bundleIdentifier": "org.example.power",
              "sourceRevision": "\(String(repeating: "a", count: 64))",
              "embeddedMeasurementStack": {
                "path": "products/power/stacks/current.json",
                "sha256": "\(String(repeating: "b", count: 64))"
              },
              "supportedRunnerCertificateIDs": [
                "power2-runner-example"
              ]
            }
            """.utf8
        )
        let releaseDigest = SHA256.hash(data: release).map {
            String(format: "%02x", $0)
        }.joined()
        let pointer = Data(
            """
            {
              "schemaVersion": "power-stack-pointer-1.0.0",
              "productID": "power",
              "status": "active",
              "publicIntakeOpen": \(publicIntakeOpen),
              "stackID": "power-text-iphone-2.0.0-rc.1",
              "appRelease": {
                "path": "products/power/app-releases/current.json",
                "sha256": "\(releaseDigest)"
              },
              "runnerCertificate": {
                "path": "products/power/runner-certificates/power2-runner-example.json",
                "sha256": "\(String(repeating: "c", count: 64))"
              }
            }
            """.utf8
        )
        files = [
            "products/power/current.json": pointer,
            "products/power/app-releases/current.json": release,
        ]
    }
}

private enum TestError: Error {
    case missingFixture
    case offline
}
