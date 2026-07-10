import Foundation
import HuggingFace
import MLXLLM
import MLXLMCommon
import Tokenizers

actor MLXSwiftRuntime: ModelPreparingRuntime {
    enum RuntimeError: LocalizedError {
        case modelNotLoaded
        case missingCompletionInfo
        case identityMismatch(String)
        case cacheVerificationFailed

        var errorDescription: String? {
            switch self {
            case .modelNotLoaded:
                "The pinned MLX model has not been loaded."
            case .missingCompletionInfo:
                "MLX generation ended without completion information."
            case .identityMismatch(let message):
                "Runtime identity mismatch: \(message)"
            case .cacheVerificationFailed:
                "The downloaded model cache could not be verified as complete."
            }
        }
    }

    nonisolated let identity =
        "MLX Swift LM 3.31.4 · mlx-community/Qwen3-0.6B-4bit@73e3e38d"

    private static let cacheVerificationMethod =
        "huggingface_revision_manifest_cached_file_size_v1"
    private static let requiredFileSuffixes = [".safetensors", ".json", ".jinja"]

    private var modelContainer: ModelContainer?
    private var preparedPlan: PilotPlan?

    func prepare(plan: PilotPlan) async -> ModelPreparationEvidence {
        let startedAt = ContinuousClock.now
        let preparedAt = Date()
        let model = plan.modelProfile
        var cacheState: ModelPreparationEvidence.CacheState = .unknown
        var downloadOccurred = false
        var preparationCompleted = false
        var modelLoadCompleted = false
        var reasons: [String] = []

        do {
            try Self.validateIdentity(plan)
            let inspector = HuggingFaceCacheInspector()
            let inspection = await inspector.inspect(
                artifactID: model.artifactId,
                revision: model.artifactRevision,
                requiredFileSuffixes: Self.requiredFileSuffixes
            )
            cacheState = inspection.state

            switch inspection.state {
            case .unknown:
                reasons = ["model_cache_state_unknown"]
            case .cached:
                try await load(
                    plan: plan,
                    localFilesOnly: true
                )
                preparationCompleted = true
                modelLoadCompleted = true
                preparedPlan = plan
            case .notCached, .incomplete:
                reasons.append(
                    inspection.state == .notCached
                        ? "model_artifact_not_cached"
                        : "model_artifact_incomplete"
                )
                try await inspector.download(
                    artifactID: model.artifactId,
                    revision: model.artifactRevision,
                    requiredFileSuffixes: Self.requiredFileSuffixes
                )
                downloadOccurred = true
                let afterDownload = await inspector.inspect(
                    artifactID: model.artifactId,
                    revision: model.artifactRevision,
                    requiredFileSuffixes: Self.requiredFileSuffixes
                )
                guard afterDownload.state == .cached else {
                    reasons.append(
                        afterDownload.state == .unknown
                            ? "model_cache_state_unknown"
                            : "model_artifact_incomplete"
                    )
                    throw RuntimeError.cacheVerificationFailed
                }
                try await load(
                    plan: plan,
                    localFilesOnly: true
                )
                preparationCompleted = true
                modelLoadCompleted = true
                preparedPlan = plan
                reasons.append("model_download_during_session")
                reasons.append("restart_required_after_download")
            }
        } catch let error as RuntimeError {
            if case .identityMismatch = error {
                reasons.append("runtime_identity_mismatch")
            } else if case .cacheVerificationFailed = error {
                // The specific cache-state reason was recorded above.
            } else {
                reasons.append("model_load_failed")
            }
            reasons.append("model_preparation_failed")
        } catch {
            if !downloadOccurred {
                reasons.append("model_load_failed")
            }
            reasons.append("model_preparation_failed")
        }

        let eligible = cacheState == .cached
            && !downloadOccurred
            && preparationCompleted
            && modelLoadCompleted
            && reasons.isEmpty
        return ModelPreparationEvidence(
            artifactID: model.artifactId,
            artifactRevision: model.artifactRevision,
            cacheStateBeforePreparation: cacheState,
            downloadOccurredDuringSession: downloadOccurred,
            preparationDurationMilliseconds: Double(
                startedAt.duration(to: .now).nanoseconds
            ) / 1_000_000,
            preparationCompleted: preparationCompleted,
            modelLoadCompleted: modelLoadCompleted,
            eligibleForPerformanceMeasurement: eligible,
            reasonCodes: Array(Set(reasons)).sorted(),
            cacheVerificationMethod: Self.cacheVerificationMethod,
            preparedAt: preparedAt
        )
    }

    private func load(plan: PilotPlan, localFilesOnly: Bool) async throws {
        guard modelContainer == nil else { return }
        let configuration = ModelConfiguration(
            id: plan.modelProfile.artifactId,
            revision: plan.modelProfile.artifactRevision
        )
        modelContainer = try await loadModelContainer(
            from: HuggingFaceDownloader(localFilesOnly: localFilesOnly),
            using: HuggingFaceTokenizerLoader(),
            configuration: configuration,
            useLatest: false
        )
    }

    static func validateIdentity(_ plan: PilotPlan) throws {
        let model = plan.modelProfile
        let runtime = plan.runtimeProfile
        guard model.artifactId == "mlx-community/Qwen3-0.6B-4bit",
              model.artifactRevision == "73e3e38d981303bc594367cd910ea6eb48349da8" else {
            throw RuntimeError.identityMismatch("model artifact or revision")
        }
        guard runtime.runtimeName == "MLX Swift LM",
              runtime.packageVersion == "3.31.4",
              runtime.packageRevision == "bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57",
              runtime.mlxSwiftVersion == "0.31.6",
              runtime.mlxSwiftRevision == "0bb916c67f4b9e5c682cbe02a42c701c93ab5021" else {
            throw RuntimeError.identityMismatch("MLX dependency identity")
        }
    }

    func generate(
        prompt: String,
        outputTokenLimit: Int,
        onToken: @Sendable (RuntimeToken) async -> Void
    ) async throws -> RuntimeGenerationResult {
        guard let modelContainer, let preparedPlan else {
            throw RuntimeError.modelNotLoaded
        }

        let clock = ContinuousClock()
        let requestStart = clock.now
        let parameters = GenerateParameters(
            maxTokens: outputTokenLimit,
            temperature: Float(preparedPlan.generation.temperature),
            topP: Float(preparedPlan.generation.topP ?? 1),
            topK: preparedPlan.generation.topK ?? 0,
            repetitionPenalty: preparedPlan.generation.repetitionPenalty.map(Float.init),
            seed: preparedPlan.generation.seed
        )

        let (stream, task, generationStart) = try await modelContainer.perform { context in
            let input = try await context.processor.prepare(
                input: UserInput(
                    prompt: prompt,
                    additionalContext: preparedPlan.generation.thinkingMode
                        == "disabled-via-chat-template"
                        ? ["enable_thinking": false]
                        : nil
                )
            )
            let generationStart = clock.now
            let (stream, task) = try generateTokensTask(
                input: input,
                parameters: parameters,
                context: context,
                includeStopToken: preparedPlan.generation.includeStopTokenInRawEvents
            )
            return (stream, task, generationStart)
        }

        var tokenIndex = 0
        var tokenIDs: [Int] = []
        var userVisibleTTFTNanoseconds: UInt64?
        var completionInfo: GenerateCompletionInfo?
        let tokenizer = await modelContainer.tokenizer

        for await event in stream {
            switch event {
            case .token(let tokenID):
                let elapsed = generationStart.duration(to: clock.now)
                tokenIDs.append(tokenID)
                if userVisibleTTFTNanoseconds == nil {
                    let decoded = tokenizer.decode(
                        tokenIds: tokenIDs,
                        skipSpecialTokens: true
                    )
                    if !decoded.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                        userVisibleTTFTNanoseconds = requestStart.duration(to: clock.now)
                            .nanoseconds
                    }
                }
                await onToken(
                    RuntimeToken(
                        index: tokenIndex,
                        tokenID: tokenID,
                        elapsedNanoseconds: elapsed.nanoseconds
                    )
                )
                tokenIndex += 1
            case .info(let info):
                completionInfo = info
            }
        }

        await task.value
        guard let completionInfo else {
            throw RuntimeError.missingCompletionInfo
        }

        return RuntimeGenerationResult(
            promptTokenCount: completionInfo.promptTokenCount,
            outputTokenCount: completionInfo.generationTokenCount,
            stopReason: completionInfo.stopReason.runtimeStopReason,
            promptTimeSeconds: completionInfo.promptTime,
            generateTimeSeconds: completionInfo.generateTime,
            userVisibleTTFTNanoseconds: preparedPlan.measurementMode
                .userVisibleTtftAvailable ? userVisibleTTFTNanoseconds : nil,
            requestCompletionNanoseconds: preparedPlan.measurementMode
                .userVisibleTtftAvailable
                ? requestStart.duration(to: clock.now).nanoseconds
                : nil,
            generatedText: preparedPlan.measurementMode.userVisibleTtftAvailable
                ? tokenizer.decode(tokenIds: tokenIDs, skipSpecialTokens: true)
                : nil
        )
    }
}

private struct HuggingFaceDownloader: Downloader {
    enum DownloadError: LocalizedError {
        case invalidRepositoryID(String)

        var errorDescription: String? {
            switch self {
            case .invalidRepositoryID(let id):
                "Invalid Hugging Face repository ID: \(id)"
            }
        }
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

private struct HuggingFaceCacheInspector: Sendable {
    struct Inspection: Sendable {
        let state: ModelPreparationEvidence.CacheState
    }

    private let client = HuggingFace.HubClient()

    func inspect(
        artifactID: String,
        revision: String,
        requiredFileSuffixes: [String]
    ) async -> Inspection {
        guard let repository = HuggingFace.Repo.ID(rawValue: artifactID),
              let cache = client.cache else {
            return Inspection(state: .unknown)
        }
        do {
            let entries = try await client.listFiles(
                in: repository,
                revision: revision,
                recursive: true
            ).filter { entry in
                requiredFileSuffixes.contains { entry.path.hasSuffix($0) }
            }
            let expectedFiles = Dictionary(
                uniqueKeysWithValues: entries.map { ($0.path, $0.size) }
            )
            var cachedFileSizes: [String: Int] = [:]
            for entry in entries {
                guard let url = cache.cachedFilePath(
                    repo: repository,
                    kind: .model,
                    revision: revision,
                    filename: entry.path
                ) else { continue }
                let resolved = url.resolvingSymlinksInPath()
                let actualSize = try resolved.resourceValues(
                    forKeys: [.fileSizeKey]
                ).fileSize
                if let actualSize {
                    cachedFileSizes[entry.path] = actualSize
                }
            }
            return Inspection(
                state: ModelCacheVerification.classify(
                    expectedFiles: expectedFiles,
                    cachedFileSizes: cachedFileSizes
                )
            )
        } catch {
            return Inspection(state: .unknown)
        }
    }

    func download(
        artifactID: String,
        revision: String,
        requiredFileSuffixes: [String]
    ) async throws {
        guard let repository = HuggingFace.Repo.ID(rawValue: artifactID) else {
            throw HuggingFaceDownloader.DownloadError.invalidRepositoryID(artifactID)
        }
        let patterns = requiredFileSuffixes.map { "*\($0)" }
        _ = try await client.downloadSnapshot(
            of: repository,
            revision: revision,
            matching: patterns
        )
    }
}

private struct HuggingFaceTokenizerLoader: TokenizerLoader {
    func load(from directory: URL) async throws -> any MLXLMCommon.Tokenizer {
        let tokenizer = try await Tokenizers.AutoTokenizer.from(modelFolder: directory)
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

private extension GenerateStopReason {
    var runtimeStopReason: RuntimeGenerationResult.StopReason {
        switch self {
        case .stop: .endOfSequence
        case .length: .outputTokenLimit
        case .cancelled: .cancelled
        }
    }
}

private extension Duration {
    var nanoseconds: UInt64 {
        let parts = components
        let seconds = UInt64(max(0, parts.seconds))
        let attoseconds = UInt64(max(0, parts.attoseconds))
        return seconds * 1_000_000_000 + attoseconds / 1_000_000_000
    }
}
