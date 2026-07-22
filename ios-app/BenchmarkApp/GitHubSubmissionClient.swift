import Foundation

struct GitHubDeviceAuthorization: Sendable, Equatable {
    let deviceCode: String
    let userCode: String
    let verificationURL: URL
    let expiresIn: Int
    let interval: Int
}

actor GitHubSubmissionClient {
    enum ClientError: LocalizedError, Sendable {
        case missingClientID
        case invalidResponse
        case requestFailed(
            status: Int,
            operation: String,
            message: String,
            requestID: String?
        )
        case authorizationExpired
        case authorizationDenied
        case insufficientOAuthScope(String)
        case unexpectedForkRepository(String)

        var errorDescription: String? {
            switch self {
            case .missingClientID:
                return "Direct GitHub submission is not configured in this build."
            case .invalidResponse:
                return "GitHub returned an unreadable response."
            case .requestFailed(
                let status,
                let operation,
                let message,
                let requestID
            ):
                let requestSuffix = requestID.map { " [request \($0)]" } ?? ""
                return "GitHub \(operation) failed (\(status)): \(message)\(requestSuffix)"
            case .authorizationExpired:
                return "GitHub authorization expired. Start the submission again."
            case .authorizationDenied:
                return "GitHub authorization was cancelled."
            case .insufficientOAuthScope(let scope):
                return "GitHub authorized without public repository write access (scope: \(scope)). Revoke this OAuth App authorization in GitHub, then authorize it again with public_repo access."
            case .unexpectedForkRepository(let repository):
                return "GitHub account already has \(repository), but it is not a fork of YizeSun/iOS-LLM-Leaderboard. Rename or remove that repository before submitting."
            }
        }

        var statusCode: Int? {
            guard case .requestFailed(let status, _, _, _) = self else {
                return nil
            }
            return status
        }
    }

    private struct DeviceResponse: Decodable {
        let deviceCode: String
        let userCode: String
        let verificationURI: URL
        let expiresIn: Int
        let interval: Int

        enum CodingKeys: String, CodingKey {
            case deviceCode = "device_code"
            case userCode = "user_code"
            case verificationURI = "verification_uri"
            case expiresIn = "expires_in"
            case interval
        }
    }

    private struct TokenResponse: Decodable {
        let accessToken: String?
        let scope: String?
        let error: String?

        enum CodingKeys: String, CodingKey {
            case accessToken = "access_token"
            case scope
            case error
        }
    }

    private struct User: Decodable { let login: String }
    private struct Repository: Decodable {
        let defaultBranch: String
        let fork: Bool?
        let parent: RepositoryIdentity?
        let source: RepositoryIdentity?

        enum CodingKeys: String, CodingKey {
            case defaultBranch = "default_branch"
            case fork
            case parent
            case source
        }
    }
    private struct RepositoryIdentity: Decodable {
        let fullName: String
        enum CodingKeys: String, CodingKey { case fullName = "full_name" }
    }
    private struct ForkSyncResult: Decodable {
        let message: String
        let mergeType: String
        let baseBranch: String

        enum CodingKeys: String, CodingKey {
            case message
            case mergeType = "merge_type"
            case baseBranch = "base_branch"
        }
    }
    private struct GitReference: Decodable {
        let object: GitObject
        struct GitObject: Decodable { let sha: String }
    }
    private struct GitCommit: Decodable {
        let tree: GitTree
        struct GitTree: Decodable { let sha: String }
    }
    private struct GitBlob: Decodable { let sha: String }
    private struct CreatedTree: Decodable { let sha: String }
    private struct CreatedCommit: Decodable { let sha: String }
    private struct PullRequest: Decodable {
        let htmlURL: URL
        enum CodingKeys: String, CodingKey { case htmlURL = "html_url" }
    }

    private let clientID: String
    private let session: URLSession
    private let apiVersion = "2026-03-10"
    private let upstreamOwner = "YizeSun"
    private let repositoryName = "iOS-LLM-Leaderboard"

    init(clientID: String, session: URLSession = .shared) throws {
        let normalized = clientID.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !normalized.isEmpty,
              !normalized.contains("$(") else {
            throw ClientError.missingClientID
        }
        self.clientID = normalized
        self.session = session
    }

    func startAuthorization() async throws -> GitHubDeviceAuthorization {
        let response: DeviceResponse = try await formRequest(
            url: URL(string: "https://github.com/login/device/code")!,
            fields: ["client_id": clientID, "scope": "public_repo"]
        )
        return .init(
            deviceCode: response.deviceCode,
            userCode: response.userCode,
            verificationURL: response.verificationURI,
            expiresIn: response.expiresIn,
            interval: response.interval
        )
    }

    func waitForAccessToken(_ authorization: GitHubDeviceAuthorization) async throws -> String {
        let deadline = Date().addingTimeInterval(TimeInterval(authorization.expiresIn))
        var interval = authorization.interval
        while Date() < deadline {
            try await Task.sleep(for: .seconds(interval))
            let response: TokenResponse = try await formRequest(
                url: URL(string: "https://github.com/login/oauth/access_token")!,
                fields: [
                    "client_id": clientID,
                    "device_code": authorization.deviceCode,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                ]
            )
            if let token = response.accessToken {
                let grantedScope = response.scope ?? ""
                let scopes = Set(
                    grantedScope
                        .lowercased()
                        .split { $0 == "," || $0.isWhitespace }
                        .map(String.init)
                )
                guard scopes.contains("public_repo") || scopes.contains("repo") else {
                    throw ClientError.insufficientOAuthScope(
                        grantedScope.isEmpty ? "none" : grantedScope
                    )
                }
                return token
            }
            switch response.error {
            case "authorization_pending": continue
            case "slow_down": interval += 5
            case "access_denied": throw ClientError.authorizationDenied
            case "expired_token": throw ClientError.authorizationExpired
            default: throw ClientError.invalidResponse
            }
        }
        throw ClientError.authorizationExpired
    }

    func authenticatedUser(token: String) async throws -> String {
        let user: User = try await apiRequest(path: "/user", token: token)
        return user.login
    }

    func publish(
        package: PowerSubmissionPackage,
        contributor: String,
        token: String
    ) async throws -> URL {
        let upstream: Repository = try await apiRequest(
            path: "/repos/\(upstreamOwner)/\(repositoryName)", token: token
        )
        let repositoryOwner = try await prepareWritableRepository(
            contributor: contributor,
            upstreamDefaultBranch: upstream.defaultBranch,
            token: token
        )
        let base: GitReference = try await apiRequest(
            path: "/repos/\(repositoryOwner)/\(repositoryName)/git/ref/heads/\(upstream.defaultBranch)",
            token: token
        )
        let baseCommit: GitCommit = try await apiRequest(
            path: "/repos/\(repositoryOwner)/\(repositoryName)/git/commits/\(base.object.sha)",
            token: token
        )
        let branch = "power-submission-\(package.submissionID.uuidString.lowercased())"
        let _: GitReference = try await apiRequest(
            path: "/repos/\(repositoryOwner)/\(repositoryName)/git/refs",
            method: "POST",
            token: token,
            body: ["ref": "refs/heads/\(branch)", "sha": base.object.sha]
        )
        let resultBlob = try await createBlob(
            package.resultData, owner: repositoryOwner, token: token
        )
        let manifestBlob = try await createBlob(
            package.manifestData, owner: repositoryOwner, token: token
        )
        let tree: CreatedTree = try await apiRequest(
            path: "/repos/\(repositoryOwner)/\(repositoryName)/git/trees",
            method: "POST",
            token: token,
            body: [
                "base_tree": baseCommit.tree.sha,
                "tree": [
                    ["path": "\(package.repositoryDirectory)/result.json", "mode": "100644", "type": "blob", "sha": resultBlob.sha],
                    ["path": "\(package.repositoryDirectory)/submission.json", "mode": "100644", "type": "blob", "sha": manifestBlob.sha],
                ],
            ]
        )
        let commit: CreatedCommit = try await apiRequest(
            path: "/repos/\(repositoryOwner)/\(repositoryName)/git/commits",
            method: "POST",
            token: token,
            body: [
                "message": "Add Power 1.1 result",
                "tree": tree.sha,
                "parents": [base.object.sha],
            ]
        )
        let _: GitReference = try await apiRequest(
            path: "/repos/\(repositoryOwner)/\(repositoryName)/git/refs/heads/\(branch)",
            method: "PATCH",
            token: token,
            body: ["sha": commit.sha]
        )
        let pullRequest: PullRequest = try await apiRequest(
            path: "/repos/\(upstreamOwner)/\(repositoryName)/pulls",
            method: "POST",
            token: token,
            body: [
                "title": "Add Power 1.1 result",
                "head": "\(contributor):\(branch)",
                "base": upstream.defaultBranch,
                "body": "Submitted from the iOS Benchmark App. CI is authoritative for validation, triage, and ranking eligibility.",
                "maintainer_can_modify": true,
            ]
        )
        return pullRequest.htmlURL
    }

    private func prepareWritableRepository(
        contributor: String,
        upstreamDefaultBranch: String,
        token: String
    ) async throws -> String {
        guard contributor.caseInsensitiveCompare(upstreamOwner) != .orderedSame else {
            return upstreamOwner
        }

        var fork = try await repositoryIfPresent(owner: contributor, token: token)
        if fork == nil {
            let _: Repository = try await apiRequest(
                path: "/repos/\(upstreamOwner)/\(repositoryName)/forks",
                method: "POST",
                token: token,
                body: ["default_branch_only": true]
            )
            fork = try await waitForFork(owner: contributor, token: token)
        }
        guard let fork, isExpectedFork(fork) else {
            throw ClientError.unexpectedForkRepository(
                "\(contributor)/\(repositoryName)"
            )
        }
        let _: ForkSyncResult = try await apiRequest(
            path: "/repos/\(contributor)/\(repositoryName)/merge-upstream",
            method: "POST",
            token: token,
            body: ["branch": upstreamDefaultBranch]
        )
        return contributor
    }

    private func repositoryIfPresent(
        owner: String,
        token: String
    ) async throws -> Repository? {
        do {
            return try await apiRequest(
                path: "/repos/\(owner)/\(repositoryName)", token: token
            )
        } catch let error as ClientError where error.statusCode == 404 {
            return nil
        }
    }

    private func isExpectedFork(_ repository: Repository) -> Bool {
        let expected = "\(upstreamOwner)/\(repositoryName)"
        let upstream = repository.parent?.fullName ?? repository.source?.fullName
        return repository.fork == true
            && upstream?.caseInsensitiveCompare(expected) == .orderedSame
    }

    private func waitForFork(owner: String, token: String) async throws -> Repository {
        for _ in 0..<30 {
            if let repository = try await repositoryIfPresent(
                owner: owner,
                token: token
            ) {
                return repository
            }
            try await Task.sleep(for: .seconds(2))
        }
        throw ClientError.requestFailed(
            status: 408,
            operation: "GET /repos/\(owner)/\(repositoryName)",
            message: "GitHub fork was not ready in time",
            requestID: nil
        )
    }

    private func createBlob(_ data: Data, owner: String, token: String) async throws -> GitBlob {
        try await apiRequest(
            path: "/repos/\(owner)/\(repositoryName)/git/blobs",
            method: "POST",
            token: token,
            body: ["content": data.base64EncodedString(), "encoding": "base64"]
        )
    }

    private func formRequest<Response: Decodable>(
        url: URL,
        fields: [String: String]
    ) async throws -> Response {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.httpBody = fields
            .map { key, value in
                "\(key.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)!)=\(value.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed)!)"
            }
            .sorted()
            .joined(separator: "&")
            .data(using: .utf8)
        return try await decoded(request)
    }

    private func apiRequest<Response: Decodable>(
        path: String,
        method: String = "GET",
        token: String,
        body: Any? = nil
    ) async throws -> Response {
        var request = URLRequest(url: URL(string: "https://api.github.com\(path)")!)
        request.httpMethod = method
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        request.setValue(apiVersion, forHTTPHeaderField: "X-GitHub-Api-Version")
        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        return try await decoded(request)
    }

    private func decoded<Response: Decodable>(_ request: URLRequest) async throws -> Response {
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw ClientError.invalidResponse
        }
        guard 200..<300 ~= http.statusCode else {
            let message = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["message"] as? String
            throw ClientError.requestFailed(
                status: http.statusCode,
                operation: "\(request.httpMethod ?? "REQUEST") \(request.url?.path ?? "GitHub API")",
                message: message ?? String(data: data, encoding: .utf8) ?? "Unknown error",
                requestID: http.value(forHTTPHeaderField: "X-GitHub-Request-Id")
            )
        }
        do {
            return try JSONDecoder().decode(Response.self, from: data)
        } catch {
            throw ClientError.invalidResponse
        }
    }
}
