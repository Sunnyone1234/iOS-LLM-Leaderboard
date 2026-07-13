import Foundation
import HuggingFace
import MLXLLM
import MLXLMCommon
import Tokenizers

/// Exact model artifacts represented by the Ship 1.0 RC1 reference profiles.
enum TestedShipProfile: String, CaseIterable, Sendable {
    case qwen3_0_6B
    case qwen3_1_7B
    case qwen3_4B

    var artifactID: String {
        switch self {
        case .qwen3_0_6B: "mlx-community/Qwen3-0.6B-4bit"
        case .qwen3_1_7B: "mlx-community/Qwen3-1.7B-4bit"
        case .qwen3_4B: "mlx-community/Qwen3-4B-3bit"
        }
    }

    var revision: String {
        switch self {
        case .qwen3_0_6B: "73e3e38d981303bc594367cd910ea6eb48349da8"
        case .qwen3_1_7B: "3b1b1768f8f8cf8351c712464f906e86c2b8269e"
        case .qwen3_4B: "c4e8054c71facfa84f781cdb7c1ffab3f09f89bf"
        }
    }
}

struct PinnedMLXModel: Sendable {
    enum RecipeError: Error {
        case missingCompletionInfo
    }

    let profile: TestedShipProfile
    let container: ModelContainer

    /// Set `localFilesOnly` to true after the pinned revision is cached when
    /// the app must fail instead of attempting a network download.
    static func load(
        _ profile: TestedShipProfile,
        localFilesOnly: Bool = false
    ) async throws -> Self {
        let configuration = ModelConfiguration(
            id: profile.artifactID,
            revision: profile.revision
        )
        let container = try await loadModelContainer(
            from: RevisionPinnedDownloader(localFilesOnly: localFilesOnly),
            using: HuggingFaceTokenizerLoader(),
            configuration: configuration,
            useLatest: false
        )
        return Self(profile: profile, container: container)
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

private struct RevisionPinnedDownloader: Downloader {
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

private struct HuggingFaceTokenizerLoader: TokenizerLoader {
    func load(from directory: URL) async throws -> any MLXLMCommon.Tokenizer {
        let tokenizer = try await Tokenizers.AutoTokenizer.from(
            modelFolder: directory
        )
        return HuggingFaceTokenizer(tokenizer)
    }
}

private struct HuggingFaceTokenizer: MLXLMCommon.Tokenizer {
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
