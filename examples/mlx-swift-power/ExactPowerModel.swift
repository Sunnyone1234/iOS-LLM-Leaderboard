import Foundation
import HuggingFace
import MLXLLM
import MLXLMCommon
import Tokenizers

/// Loads the exact artifact and revision attached to a Power evidence row.
/// Loading succeeds independently of whether a Ship profile has been published.
struct ExactPowerModel: Sendable {
    enum RecipeError: Error {
        case missingCompletionInfo
    }

    let artifactID: String
    let revision: String
    let container: ModelContainer

    static func load(
        artifactID: String,
        revision: String,
        localFilesOnly: Bool = false
    ) async throws -> Self {
        let configuration = ModelConfiguration(
            id: artifactID,
            revision: revision
        )
        let container = try await loadModelContainer(
            from: PowerRevisionPinnedDownloader(localFilesOnly: localFilesOnly),
            using: PowerHuggingFaceTokenizerLoader(),
            configuration: configuration,
            useLatest: false
        )
        return Self(
            artifactID: artifactID,
            revision: revision,
            container: container
        )
    }

    /// Streams adapter token events. UI rendering time is outside this boundary.
    func stream(
        prompt: String,
        maxTokens: Int = 128,
        onToken: @Sendable (Int, Int) async -> Void
    ) async throws -> GenerateCompletionInfo {
        let parameters = GenerateParameters(
            maxTokens: maxTokens,
            temperature: 0,
            topP: 1,
            topK: 0
        )
        let (stream, task) = try await container.perform { context in
            let input = try await context.processor.prepare(
                input: UserInput(
                    prompt: prompt,
                    additionalContext: ["enable_thinking": false]
                )
            )
            return try generateTokensTask(
                input: input,
                parameters: parameters,
                context: context,
                includeStopToken: false
            )
        }

        var index = 0
        var completionInfo: GenerateCompletionInfo?
        for await event in stream {
            switch event {
            case .token(let tokenID):
                await onToken(index, tokenID)
                index += 1
            case .info(let info):
                completionInfo = info
            }
        }
        await task.value
        guard let completionInfo else {
            throw RecipeError.missingCompletionInfo
        }
        return completionInfo
    }
}

private struct PowerRevisionPinnedDownloader: Downloader {
    enum DownloadError: Error {
        case invalidRepositoryID(String)
    }

    private let client = HuggingFace.HubClient()
    let localFilesOnly: Bool

    func download(
        id: String,
        revision: String?,
        matching patterns: [String],
        useLatest: Bool,
        progressHandler: @Sendable @escaping (Progress) -> Void
    ) async throws -> URL {
        guard let repository = HuggingFace.Repo.ID(rawValue: id) else {
            throw DownloadError.invalidRepositoryID(id)
        }
        return try await client.downloadSnapshot(
            of: repository,
            revision: revision ?? "main",
            matching: patterns,
            localFilesOnly: localFilesOnly
        ) { @MainActor progress in
            progressHandler(progress)
        }
    }
}

private struct PowerHuggingFaceTokenizerLoader: TokenizerLoader {
    func load(from directory: URL) async throws -> any MLXLMCommon.Tokenizer {
        let tokenizer = try await Tokenizers.AutoTokenizer.from(
            modelFolder: directory
        )
        return PowerHuggingFaceTokenizer(tokenizer)
    }
}

private struct PowerHuggingFaceTokenizer: MLXLMCommon.Tokenizer {
    private let upstream: any Tokenizers.Tokenizer

    init(_ upstream: any Tokenizers.Tokenizer) {
        self.upstream = upstream
    }

    func encode(text: String, addSpecialTokens: Bool) -> [Int] {
        upstream.encode(text: text, addSpecialTokens: addSpecialTokens)
    }

    func decode(tokenIds: [Int], skipSpecialTokens: Bool) -> String {
        upstream.decode(tokens: tokenIds, skipSpecialTokens: skipSpecialTokens)
    }

    func convertTokenToId(_ token: String) -> Int? {
        upstream.convertTokenToId(token)
    }

    func convertIdToToken(_ id: Int) -> String? {
        upstream.convertIdToToken(id)
    }

    var bosToken: String? { upstream.bosToken }
    var eosToken: String? { upstream.eosToken }
    var unknownToken: String? { upstream.unknownToken }

    func applyChatTemplate(
        messages: [[String: any Sendable]],
        tools: [[String: any Sendable]]?,
        additionalContext: [String: any Sendable]?
    ) throws -> [Int] {
        do {
            return try upstream.applyChatTemplate(
                messages: messages,
                tools: tools,
                additionalContext: additionalContext
            )
        } catch Tokenizers.TokenizerError.missingChatTemplate {
            throw MLXLMCommon.TokenizerError.missingChatTemplate
        }
    }
}
