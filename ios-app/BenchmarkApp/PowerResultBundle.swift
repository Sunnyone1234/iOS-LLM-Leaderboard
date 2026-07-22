import Foundation

struct PowerResultBundle: Codable, Sendable, Equatable {
    let schemaVersion: String
    let resultID: UUID
    let createdAt: Date
    let benchmarkRelease: BenchmarkRelease
    let officialResultEligible: Bool
    let execution: Execution
    let configuration: Configuration
    let model: Model
    let runtime: Runtime
    let device: Device
    let environment: Environment
    let modelPreparation: ModelPreparation
    let attempts: [Attempt]
    let summary: Summary

    struct BenchmarkRelease: Codable, Sendable, Equatable {
        let id: String
        let version: String
        let protocolID: String
        let protocolVersion: String
    }

    struct Execution: Codable, Sendable, Equatable {
        let sessionID: UUID
        let workloadID: String
        let workloadVersion: String
        let workloadCategory: String
        let fixtureSHA256: String
        let measurementModeID: String
        let runnerID: String
        let runnerVersion: String
        let appVersion: String
        let appBuild: String
        let appSourceCommit: String
    }

    struct Configuration: Codable, Sendable, Equatable {
        let warmupAttempts: Int
        let measuredAttempts: Int
        let minimumMetricEligibleMeasuredAttempts: Int
        let restIntervalSeconds: Int
        let samplingEnabled: Bool
        let temperature: Double
        let topP: Double?
        let topK: Int?
        let seed: UInt64?
        let repetitionPenalty: Double?
        let thinkingMode: String
        let chatTemplateIdentity: String
        let includeStopTokenInRawEvents: Bool
        let outputTokenLimit: Int
        let modelLoadPolicy: String
        let contextPolicy: String
        let kvCachePolicy: String
        let automaticRetries: Int
        let clock: String
        let memorySamplingIntervalMilliseconds: Int
        let memoryMetric: String
        let thermalSource: String

        private enum CodingKeys: String, CodingKey {
            case warmupAttempts, measuredAttempts
            case minimumMetricEligibleMeasuredAttempts, restIntervalSeconds
            case samplingEnabled, temperature, topP, topK, seed
            case repetitionPenalty, thinkingMode, chatTemplateIdentity
            case includeStopTokenInRawEvents, outputTokenLimit
            case modelLoadPolicy, contextPolicy, kvCachePolicy
            case automaticRetries, clock, memorySamplingIntervalMilliseconds
            case memoryMetric, thermalSource
        }

        func encode(to encoder: Encoder) throws {
            var value = encoder.container(keyedBy: CodingKeys.self)
            try value.encode(warmupAttempts, forKey: .warmupAttempts)
            try value.encode(measuredAttempts, forKey: .measuredAttempts)
            try value.encode(
                minimumMetricEligibleMeasuredAttempts,
                forKey: .minimumMetricEligibleMeasuredAttempts
            )
            try value.encode(restIntervalSeconds, forKey: .restIntervalSeconds)
            try value.encode(samplingEnabled, forKey: .samplingEnabled)
            try value.encode(temperature, forKey: .temperature)
            try value.encodeNullable(topP, forKey: .topP)
            try value.encodeNullable(topK, forKey: .topK)
            try value.encodeNullable(seed, forKey: .seed)
            try value.encodeNullable(repetitionPenalty, forKey: .repetitionPenalty)
            try value.encode(thinkingMode, forKey: .thinkingMode)
            try value.encode(chatTemplateIdentity, forKey: .chatTemplateIdentity)
            try value.encode(
                includeStopTokenInRawEvents,
                forKey: .includeStopTokenInRawEvents
            )
            try value.encode(outputTokenLimit, forKey: .outputTokenLimit)
            try value.encode(modelLoadPolicy, forKey: .modelLoadPolicy)
            try value.encode(contextPolicy, forKey: .contextPolicy)
            try value.encode(kvCachePolicy, forKey: .kvCachePolicy)
            try value.encode(automaticRetries, forKey: .automaticRetries)
            try value.encode(clock, forKey: .clock)
            try value.encode(
                memorySamplingIntervalMilliseconds,
                forKey: .memorySamplingIntervalMilliseconds
            )
            try value.encode(memoryMetric, forKey: .memoryMetric)
            try value.encode(thermalSource, forKey: .thermalSource)
        }
    }

    struct Model: Codable, Sendable, Equatable {
        let displayName: String
        let baseModelID: String
        let artifactID: String
        let artifactRevision: String
        let artifactContentHash: String?
        let quantization: String
        let modelFormat: String
        let tokenizerIdentity: String
        let sourceURL: String
        let licenseIdentifier: String
        let licenseSourceURL: String
        let artifactRepositorySizeBytes: Int64

        private enum CodingKeys: String, CodingKey {
            case displayName, baseModelID, artifactID, artifactRevision
            case artifactContentHash, quantization, modelFormat
            case tokenizerIdentity, sourceURL, licenseIdentifier
            case licenseSourceURL, artifactRepositorySizeBytes
        }

        func encode(to encoder: Encoder) throws {
            var value = encoder.container(keyedBy: CodingKeys.self)
            try value.encode(displayName, forKey: .displayName)
            try value.encode(baseModelID, forKey: .baseModelID)
            try value.encode(artifactID, forKey: .artifactID)
            try value.encode(artifactRevision, forKey: .artifactRevision)
            try value.encodeNullable(
                artifactContentHash,
                forKey: .artifactContentHash
            )
            try value.encode(quantization, forKey: .quantization)
            try value.encode(modelFormat, forKey: .modelFormat)
            try value.encode(tokenizerIdentity, forKey: .tokenizerIdentity)
            try value.encode(sourceURL, forKey: .sourceURL)
            try value.encode(licenseIdentifier, forKey: .licenseIdentifier)
            try value.encode(licenseSourceURL, forKey: .licenseSourceURL)
            try value.encode(
                artifactRepositorySizeBytes,
                forKey: .artifactRepositorySizeBytes
            )
        }
    }

    struct Runtime: Codable, Sendable, Equatable {
        let name: String
        let version: String
        let resolvedRevision: String
        let backend: String
        let dependencyVersions: [String: String]
    }

    struct Device: Codable, Sendable, Equatable {
        let displayName: String
        let machineIdentifier: String
        let systemName: String
        let systemVersion: String
        let systemBuild: String
        let physicalMemoryBytes: UInt64
    }

    struct Environment: Codable, Sendable, Equatable {
        let buildConfiguration: String
        let debuggerAttached: Bool
        let lowPowerModeEnabled: Bool
        let batteryState: String
        let batteryLevelPercentAtStart: Double?
        let thermalStateAtSessionStart: String
        let thermalStateAtSessionEnd: String

        private enum CodingKeys: String, CodingKey {
            case buildConfiguration, debuggerAttached, lowPowerModeEnabled
            case batteryState, batteryLevelPercentAtStart
            case thermalStateAtSessionStart, thermalStateAtSessionEnd
        }

        func encode(to encoder: Encoder) throws {
            var value = encoder.container(keyedBy: CodingKeys.self)
            try value.encode(buildConfiguration, forKey: .buildConfiguration)
            try value.encode(debuggerAttached, forKey: .debuggerAttached)
            try value.encode(lowPowerModeEnabled, forKey: .lowPowerModeEnabled)
            try value.encode(batteryState, forKey: .batteryState)
            try value.encodeNullable(
                batteryLevelPercentAtStart,
                forKey: .batteryLevelPercentAtStart
            )
            try value.encode(
                thermalStateAtSessionStart,
                forKey: .thermalStateAtSessionStart
            )
            try value.encode(
                thermalStateAtSessionEnd,
                forKey: .thermalStateAtSessionEnd
            )
        }
    }

    struct ModelPreparation: Codable, Sendable, Equatable {
        let artifactID: String
        let artifactRevision: String
        let cacheVerificationMethod: String
        let downloadOccurredDuringSession: Bool
        let preparationCompleted: Bool
        let modelLoadCompleted: Bool
        let eligibleForPerformanceMeasurement: Bool
        let reasonCodes: [String]
        let preparedAt: Date
    }

    struct Attempt: Codable, Sendable, Equatable {
        let runIndex: Int
        let role: String
        let outcome: String
        let reasonCodes: [String]
        let stopReason: String?
        let generatedText: String?
        let promptTokenCount: Int?
        let outputTokenCount: Int?
        let responseConformance: ResponseConformance
        let timingEvidence: TimingEvidence
        let tokenEvents: [RuntimeToken]
        let renderabilityTrace: FirstRenderableTrace?
        let memorySamples: [ProcessMemorySample]
        let thermal: ThermalEvidence
        let derivedMetrics: Metrics

        private enum CodingKeys: String, CodingKey {
            case runIndex, role, outcome, reasonCodes, stopReason
            case generatedText, promptTokenCount, outputTokenCount
            case responseConformance, timingEvidence, tokenEvents
            case renderabilityTrace, memorySamples, thermal, derivedMetrics
        }

        func encode(to encoder: Encoder) throws {
            var value = encoder.container(keyedBy: CodingKeys.self)
            try value.encode(runIndex, forKey: .runIndex)
            try value.encode(role, forKey: .role)
            try value.encode(outcome, forKey: .outcome)
            try value.encode(reasonCodes, forKey: .reasonCodes)
            try value.encodeNullable(stopReason, forKey: .stopReason)
            try value.encodeNullable(generatedText, forKey: .generatedText)
            try value.encodeNullable(promptTokenCount, forKey: .promptTokenCount)
            try value.encodeNullable(outputTokenCount, forKey: .outputTokenCount)
            try value.encode(responseConformance, forKey: .responseConformance)
            try value.encode(timingEvidence, forKey: .timingEvidence)
            try value.encode(tokenEvents, forKey: .tokenEvents)
            try value.encodeNullable(
                renderabilityTrace,
                forKey: .renderabilityTrace
            )
            try value.encode(memorySamples, forKey: .memorySamples)
            try value.encode(thermal, forKey: .thermal)
            try value.encode(derivedMetrics, forKey: .derivedMetrics)
        }
    }

    struct ResponseConformance: Codable, Sendable, Equatable {
        let status: String
        let reasonCodes: [String]
    }

    struct TimingEvidence: Codable, Sendable, Equatable {
        let generationStartNanoseconds: UInt64?
        let promptEvaluationNanoseconds: UInt64?
        let requestCompletionNanoseconds: UInt64?

        private enum CodingKeys: String, CodingKey {
            case generationStartNanoseconds, promptEvaluationNanoseconds
            case requestCompletionNanoseconds
        }

        func encode(to encoder: Encoder) throws {
            var value = encoder.container(keyedBy: CodingKeys.self)
            try value.encodeNullable(
                generationStartNanoseconds,
                forKey: .generationStartNanoseconds
            )
            try value.encodeNullable(
                promptEvaluationNanoseconds,
                forKey: .promptEvaluationNanoseconds
            )
            try value.encodeNullable(
                requestCompletionNanoseconds,
                forKey: .requestCompletionNanoseconds
            )
        }
    }

    struct ThermalEvidence: Codable, Sendable, Equatable {
        let before: String
        let after: String
        let transitions: [ThermalTransition]
    }

    struct Metrics: Codable, Sendable, Equatable {
        let pipelineTTFTMilliseconds: Double?
        let firstRenderableProxyTTFTMilliseconds: Double?
        let requestCompletionMilliseconds: Double?
        let prefillTokensPerSecond: Double?
        let decodeTokensPerSecond: Double?
        let processPhysicalFootprintMiB: Double?

        private enum CodingKeys: String, CodingKey {
            case pipelineTTFTMilliseconds
            case firstRenderableProxyTTFTMilliseconds
            case requestCompletionMilliseconds
            case prefillTokensPerSecond, decodeTokensPerSecond
            case processPhysicalFootprintMiB
        }

        static let unavailable = Metrics(
            pipelineTTFTMilliseconds: nil,
            firstRenderableProxyTTFTMilliseconds: nil,
            requestCompletionMilliseconds: nil,
            prefillTokensPerSecond: nil,
            decodeTokensPerSecond: nil,
            processPhysicalFootprintMiB: nil
        )

        func encode(to encoder: Encoder) throws {
            var value = encoder.container(keyedBy: CodingKeys.self)
            try value.encodeNullable(
                pipelineTTFTMilliseconds,
                forKey: .pipelineTTFTMilliseconds
            )
            try value.encodeNullable(
                firstRenderableProxyTTFTMilliseconds,
                forKey: .firstRenderableProxyTTFTMilliseconds
            )
            try value.encodeNullable(
                requestCompletionMilliseconds,
                forKey: .requestCompletionMilliseconds
            )
            try value.encodeNullable(
                prefillTokensPerSecond,
                forKey: .prefillTokensPerSecond
            )
            try value.encodeNullable(
                decodeTokensPerSecond,
                forKey: .decodeTokensPerSecond
            )
            try value.encodeNullable(
                processPhysicalFootprintMiB,
                forKey: .processPhysicalFootprintMiB
            )
        }
    }

    struct Summary: Codable, Sendable, Equatable {
        let terminalCounts: TerminalCounts
        let metrics: SummaryMetrics
    }

    struct TerminalCounts: Codable, Sendable, Equatable {
        let completed: Int
        let failed: Int
        let cancelled: Int
        let outOfMemory: Int
        let notRun: Int
        let earlyEOS: Int
    }

    struct SummaryMetrics: Codable, Sendable, Equatable {
        let medianPipelineTTFTMilliseconds: Double?
        let medianFirstRenderableProxyTTFTMilliseconds: Double?
        let medianRequestCompletionMilliseconds: Double?
        let medianPrefillTokensPerSecond: Double?
        let medianDecodeTokensPerSecond: Double?
        let medianProcessPhysicalFootprintMiB: Double?
        let decodeFirstToLastPercentChange: Double?

        private enum CodingKeys: String, CodingKey {
            case medianPipelineTTFTMilliseconds
            case medianFirstRenderableProxyTTFTMilliseconds
            case medianRequestCompletionMilliseconds
            case medianPrefillTokensPerSecond, medianDecodeTokensPerSecond
            case medianProcessPhysicalFootprintMiB
            case decodeFirstToLastPercentChange
        }

        func encode(to encoder: Encoder) throws {
            var value = encoder.container(keyedBy: CodingKeys.self)
            try value.encodeNullable(
                medianPipelineTTFTMilliseconds,
                forKey: .medianPipelineTTFTMilliseconds
            )
            try value.encodeNullable(
                medianFirstRenderableProxyTTFTMilliseconds,
                forKey: .medianFirstRenderableProxyTTFTMilliseconds
            )
            try value.encodeNullable(
                medianRequestCompletionMilliseconds,
                forKey: .medianRequestCompletionMilliseconds
            )
            try value.encodeNullable(
                medianPrefillTokensPerSecond,
                forKey: .medianPrefillTokensPerSecond
            )
            try value.encodeNullable(
                medianDecodeTokensPerSecond,
                forKey: .medianDecodeTokensPerSecond
            )
            try value.encodeNullable(
                medianProcessPhysicalFootprintMiB,
                forKey: .medianProcessPhysicalFootprintMiB
            )
            try value.encodeNullable(
                decodeFirstToLastPercentChange,
                forKey: .decodeFirstToLastPercentChange
            )
        }
    }

    enum ExportError: LocalizedError, Equatable {
        case invalidAttemptSequence
        case incompatibleExecution(String)
        case incompleteEvidence(Int)

        var errorDescription: String? {
            switch self {
            case .invalidAttemptSequence:
                "Power evidence must contain one warm-up and five measured attempts."
            case .incompatibleExecution(let reason):
                "Power result is incompatible with the frozen contract: \(reason)."
            case .incompleteEvidence(let index):
                "Completed attempt \(index) is missing required raw evidence."
            }
        }
    }

    static func make(
        session: BenchmarkSession,
        context: PowerExecutionContext,
        resultID: UUID = UUID(),
        createdAt: Date = Date()
    ) throws -> PowerResultBundle {
        let plan = context.plan
        let workload = try PowerBenchmarkRelease.workload(for: plan)
        let source = context.environment
        let attempts = session.attempts.map {
            attempt($0, workload: workload)
        }
        let result = PowerResultBundle(
            schemaVersion: PowerBenchmarkRelease.resultSchemaVersion,
            resultID: resultID,
            createdAt: createdAt,
            benchmarkRelease: .init(
                id: PowerBenchmarkRelease.releaseID,
                version: PowerBenchmarkRelease.releaseVersion,
                protocolID: PowerBenchmarkRelease.releaseID,
                protocolVersion: PowerBenchmarkRelease.releaseVersion
            ),
            officialResultEligible: false,
            execution: .init(
                sessionID: session.sessionID,
                workloadID: workload.id,
                workloadVersion: PowerBenchmarkRelease.releaseVersion,
                workloadCategory: workload.category,
                fixtureSHA256: workload.fixtureSHA256,
                measurementModeID: workload.measurementModeID,
                runnerID: PowerBenchmarkRelease.runnerID,
                runnerVersion: source.appVersion,
                appVersion: source.appVersion,
                appBuild: source.appBuild,
                appSourceCommit: source.appSourceCommit
            ),
            configuration: .init(
                warmupAttempts: 1,
                measuredAttempts: 5,
                minimumMetricEligibleMeasuredAttempts: 3,
                restIntervalSeconds: 0,
                samplingEnabled: false,
                temperature: 0,
                topP: workload.topP,
                topK: workload.topK,
                seed: workload.seed,
                repetitionPenalty: nil,
                thinkingMode: workload.thinkingMode,
                chatTemplateIdentity: workload.chatTemplateIdentity,
                includeStopTokenInRawEvents: false,
                outputTokenLimit: workload.outputTokenLimit,
                modelLoadPolicy: "load-once-before-warmup",
                contextPolicy: "fresh-conversation-per-attempt",
                kvCachePolicy: "fresh-kv-cache-per-attempt",
                automaticRetries: 0,
                clock: "monotonic-nanoseconds",
                memorySamplingIntervalMilliseconds: 50,
                memoryMetric: "TASK_VM_INFO.phys_footprint",
                thermalSource: "ProcessInfo.thermalState"
            ),
            model: .init(
                displayName: plan.modelProfile.displayName,
                baseModelID: plan.modelProfile.baseModelId,
                artifactID: plan.modelProfile.artifactId,
                artifactRevision: plan.modelProfile.artifactRevision,
                artifactContentHash: plan.modelProfile.artifactContentHash,
                quantization: plan.modelProfile.quantization,
                modelFormat: plan.modelProfile.modelFormat,
                tokenizerIdentity: plan.modelProfile.tokenizerIdentity,
                sourceURL: plan.modelProfile.sourceUrl,
                licenseIdentifier: plan.modelProfile.licenseIdentifier,
                licenseSourceURL: plan.modelProfile.licenseSourceUrl,
                artifactRepositorySizeBytes:
                    plan.modelProfile.artifactRepositorySizeBytes
            ),
            runtime: .init(
                name: plan.runtimeProfile.runtimeName,
                version: plan.runtimeProfile.packageVersion,
                resolvedRevision: plan.runtimeProfile.packageRevision,
                backend: plan.runtimeProfile.backend,
                dependencyVersions: [
                    "mlx-swift": "\(plan.runtimeProfile.mlxSwiftVersion)@\(plan.runtimeProfile.mlxSwiftRevision)",
                    "swift-huggingface": plan.runtimeProfile.downloaderPackage,
                    "swift-transformers": plan.runtimeProfile.tokenizerPackage,
                ]
            ),
            device: .init(
                displayName: source.deviceDisplayName,
                machineIdentifier: source.modelIdentifier,
                systemName: source.systemName,
                systemVersion: source.systemVersion,
                systemBuild: source.systemBuild,
                physicalMemoryBytes: source.physicalMemoryBytes
            ),
            environment: .init(
                buildConfiguration: source.buildConfiguration,
                debuggerAttached: source.debuggerAttached,
                lowPowerModeEnabled: source.lowPowerModeEnabled,
                batteryState: source.batteryState,
                batteryLevelPercentAtStart: source.batteryLevelPercent,
                thermalStateAtSessionStart: session.thermalStateAtStart,
                thermalStateAtSessionEnd: session.thermalStateAtEnd
            ),
            modelPreparation: .init(
                artifactID: context.modelPreparation.artifactID,
                artifactRevision: context.modelPreparation.artifactRevision,
                cacheVerificationMethod:
                    context.modelPreparation.cacheVerificationMethod,
                downloadOccurredDuringSession:
                    context.modelPreparation.downloadOccurredDuringSession,
                preparationCompleted:
                    context.modelPreparation.preparationCompleted,
                modelLoadCompleted:
                    context.modelPreparation.modelLoadCompleted,
                eligibleForPerformanceMeasurement:
                    context.modelPreparation.eligibleForPerformanceMeasurement,
                reasonCodes: context.modelPreparation.reasonCodes,
                preparedAt: context.modelPreparation.preparedAt
            ),
            attempts: attempts,
            summary: summary(attempts, workload: workload)
        )
        try result.validateForExport()
        return result
    }

    func validateForExport() throws {
        guard attempts.count == 6,
              attempts.enumerated().allSatisfy({ index, attempt in
                  attempt.runIndex == index
                      && attempt.role == (index == 0 ? "warmup" : "measured")
              }) else {
            throw ExportError.invalidAttemptSequence
        }
        guard schemaVersion == PowerBenchmarkRelease.resultSchemaVersion,
              benchmarkRelease.id == PowerBenchmarkRelease.releaseID,
              benchmarkRelease.version == PowerBenchmarkRelease.releaseVersion,
              officialResultEligible == false,
              PowerBenchmarkRelease.isSourceCommit(execution.appSourceCommit),
              PowerBenchmarkRelease.isPhysicalIPhone(device.machineIdentifier)
        else {
            throw ExportError.incompatibleExecution("identity or provenance")
        }
        for attempt in attempts where attempt.outcome == "completed" {
            guard attempt.reasonCodes.isEmpty,
                  attempt.stopReason != nil,
                  attempt.promptTokenCount != nil,
                  attempt.outputTokenCount == attempt.tokenEvents.count,
                  !attempt.tokenEvents.isEmpty,
                  attempt.timingEvidence.generationStartNanoseconds != nil,
                  attempt.timingEvidence.promptEvaluationNanoseconds != nil,
                  !attempt.memorySamples.isEmpty else {
                throw ExportError.incompleteEvidence(attempt.runIndex)
            }
            if execution.workloadID == "b-ux-001-short-interaction",
               attempt.renderabilityTrace == nil
                || attempt.timingEvidence.requestCompletionNanoseconds == nil {
                throw ExportError.incompleteEvidence(attempt.runIndex)
            }
        }
    }

    private static func attempt(
        _ source: BenchmarkAttempt,
        workload: PowerBenchmarkRelease.Workload
    ) -> Attempt {
        let outcome: String
        let stopReason: String?
        switch source.outcome {
        case .completed(let generation):
            outcome = "completed"
            stopReason = generation.stopReason == .cancelled
                ? nil : generation.stopReason.rawValue
        case .failed:
            outcome = "failed"; stopReason = nil
        case .cancelled:
            outcome = "cancelled"; stopReason = nil
        case .outOfMemory:
            outcome = "outOfMemory"; stopReason = nil
        case .notRun:
            outcome = "notRun"; stopReason = nil
        }
        let generation = source.outcome.generation
        let response = responseConformance(
            workload: workload,
            outcome: outcome,
            text: generation?.generatedText
        )
        let metrics = metrics(source, workload: workload)
        return Attempt(
            runIndex: source.index,
            role: source.role.rawValue,
            outcome: outcome,
            reasonCodes: source.outcome.reasonCodes,
            stopReason: stopReason,
            generatedText: generation?.generatedText,
            promptTokenCount: generation?.promptTokenCount,
            outputTokenCount: generation?.outputTokenCount,
            responseConformance: response,
            timingEvidence: .init(
                generationStartNanoseconds:
                    generation?.generationStartNanoseconds,
                promptEvaluationNanoseconds:
                    generation?.promptEvaluationNanoseconds,
                requestCompletionNanoseconds:
                    generation?.requestCompletionNanoseconds
            ),
            tokenEvents: source.tokens,
            renderabilityTrace: generation?.renderabilityTrace,
            memorySamples: source.memorySamples,
            thermal: .init(
                before: source.thermalStateBefore,
                after: source.thermalStateAfter,
                transitions: source.thermalTransitions
            ),
            derivedMetrics: metrics
        )
    }

    private static func responseConformance(
        workload: PowerBenchmarkRelease.Workload,
        outcome: String,
        text: String?
    ) -> ResponseConformance {
        guard workload.category == "user-experience" else {
            return .init(status: "notApplicable", reasonCodes: [])
        }
        guard outcome == "completed" else {
            return .init(status: "notEvaluated", reasonCodes: [])
        }
        let passed = ShortInteractionResponseConformance.passes(text)
        return .init(
            status: passed ? "pass" : "fail",
            reasonCodes: passed ? [] : ["response_conformance_failed"]
        )
    }

    private static func metrics(
        _ source: BenchmarkAttempt,
        workload: PowerBenchmarkRelease.Workload
    ) -> Metrics {
        guard case .completed(let generation) = source.outcome else {
            return .unavailable
        }
        let tokens = source.tokens
        let validTokens = generation.outputTokenCount == tokens.count
            && tokens.enumerated().allSatisfy { index, token in
                token.index == index
                    && (index == 0
                        || token.elapsedNanoseconds
                            >= tokens[index - 1].elapsedNanoseconds)
            }
        let pipeline = validTokens ? tokens.first.map {
            Double($0.elapsedNanoseconds) / 1_000_000
        } : nil
        let prefill = generation.promptEvaluationNanoseconds.flatMap { duration in
            duration > 0
                ? Double(generation.promptTokenCount) * 1_000_000_000
                    / Double(duration)
                : nil
        }
        let decode: Double?
        if validTokens,
           tokens.count >= 2,
           let first = tokens.first,
           let last = tokens.last,
           last.elapsedNanoseconds > first.elapsedNanoseconds {
            decode = Double(tokens.count - 1) * 1_000_000_000
                / Double(last.elapsedNanoseconds - first.elapsedNanoseconds)
        } else {
            decode = nil
        }
        let memory = source.memorySamples.map(\.physicalFootprintBytes).max()
            .map { Double($0) / 1_048_576 }
        return Metrics(
            pipelineTTFTMilliseconds: pipeline,
            firstRenderableProxyTTFTMilliseconds:
                workload.category == "user-experience"
                    ? generation.renderabilityTrace?
                        .firstRenderableDecodedAtNanoseconds
                        .map { Double($0) / 1_000_000 }
                    : nil,
            requestCompletionMilliseconds:
                workload.category == "user-experience"
                    ? generation.requestCompletionNanoseconds.map {
                        Double($0) / 1_000_000
                    }
                    : nil,
            prefillTokensPerSecond: prefill,
            decodeTokensPerSecond: decode,
            processPhysicalFootprintMiB: memory
        )
    }

    private static func summary(
        _ attempts: [Attempt],
        workload: PowerBenchmarkRelease.Workload
    ) -> Summary {
        let measured = Array(attempts.dropFirst())
        func values(_ transform: (Metrics) -> Double?) -> [Double] {
            measured.compactMap { attempt in
                attempt.outcome == "completed"
                    ? transform(attempt.derivedMetrics) : nil
            }
        }
        let firstDecode = attempts.indices.contains(1)
            ? attempts[1].derivedMetrics.decodeTokensPerSecond : nil
        let lastDecode = attempts.indices.contains(5)
            ? attempts[5].derivedMetrics.decodeTokensPerSecond : nil
        let degradation: Double?
        if workload.category == "pipeline",
           let firstDecode,
           let lastDecode,
           firstDecode > 0 {
            degradation = ((lastDecode / firstDecode) - 1) * 100
        } else {
            degradation = nil
        }
        return Summary(
            terminalCounts: .init(
                completed: measured.filter { $0.outcome == "completed" }.count,
                failed: measured.filter { $0.outcome == "failed" }.count,
                cancelled: measured.filter { $0.outcome == "cancelled" }.count,
                outOfMemory:
                    measured.filter { $0.outcome == "outOfMemory" }.count,
                notRun: measured.filter { $0.outcome == "notRun" }.count,
                earlyEOS: measured.filter {
                    $0.outcome == "completed" && $0.stopReason == "endOfSequence"
                }.count
            ),
            metrics: .init(
                medianPipelineTTFTMilliseconds: median(values {
                    $0.pipelineTTFTMilliseconds
                }),
                medianFirstRenderableProxyTTFTMilliseconds: median(values {
                    $0.firstRenderableProxyTTFTMilliseconds
                }),
                medianRequestCompletionMilliseconds: median(values {
                    $0.requestCompletionMilliseconds
                }),
                medianPrefillTokensPerSecond: median(values {
                    $0.prefillTokensPerSecond
                }),
                medianDecodeTokensPerSecond: median(values {
                    $0.decodeTokensPerSecond
                }),
                medianProcessPhysicalFootprintMiB: median(values {
                    $0.processPhysicalFootprintMiB
                }),
                decodeFirstToLastPercentChange: degradation
            )
        )
    }

    private static func median(_ values: [Double]) -> Double? {
        guard values.count >= 3 else { return nil }
        let sorted = values.sorted()
        let middle = sorted.count / 2
        return sorted.count.isMultiple(of: 2)
            ? (sorted[middle - 1] + sorted[middle]) / 2
            : sorted[middle]
    }
}

enum ShortInteractionResponseConformance {
    enum Assessment: String, Equatable {
        case verified
        case notVerified = "not_verified"
        case contradicted
    }

    private struct Policy: Decodable {
        struct LocalPersistence: Decodable {
            let claimTerms: [String]
            let locationTerms: [String]
            let contradictionPhrases: [String]
        }

        struct DeferredSync: Decodable {
            let actionTerms: [String]
            let connectivityTerms: [String]
            let conditionTerms: [String]
            let contradictionPhrases: [String]
        }

        let policyID: String
        let policyVersion: String
        let status: String
        let maximumSentences: Int
        let localPersistence: LocalPersistence
        let deferredSync: DeferredSync
    }

    private final class PolicyBundleMarker: NSObject {}

    private static let policy: Policy? = {
        let bundles = [Bundle(for: PolicyBundleMarker.self), Bundle.main]
        guard let url = bundles.lazy.compactMap({
            $0.url(
                forResource: "short-interaction-response-v2",
                withExtension: "json"
            )
        }).first,
        let data = try? Data(contentsOf: url),
        let value = try? JSONDecoder().decode(Policy.self, from: data),
        value.policyID == "short-interaction-response-v2",
        value.status == "draft" else {
            return nil
        }
        return value
    }()

    static var policyIdentity: String? {
        policy.map { "\($0.policyID)@\($0.policyVersion)" }
    }

    static func passes(_ text: String?) -> Bool {
        assessment(text) == .verified
    }

    static func assessment(_ text: String?) -> Assessment {
        guard let policy, let text else { return .notVerified }
        let normalized = text.precomposedStringWithCompatibilityMapping
            .lowercased()
            .split(whereSeparator: { $0.isWhitespace })
            .joined(separator: " ")
        guard !normalized.isEmpty else { return .notVerified }
        let sentenceCount = normalized.components(
            separatedBy: CharacterSet(charactersIn: ".!?")
        ).filter {
            !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        }.count
        guard sentenceCount <= policy.maximumSentences else {
            return .notVerified
        }

        let contradictions =
            policy.localPersistence.contradictionPhrases
            + policy.deferredSync.contradictionPhrases
        if contradictions.contains(where: normalized.contains) {
            return .contradicted
        }

        let tokens = Set(
            normalized.components(
                separatedBy: CharacterSet.alphanumerics.inverted
            ).filter { !$0.isEmpty }
        )
        let localPersistence = !tokens.isDisjoint(
            with: Set(policy.localPersistence.claimTerms)
        ) && !tokens.isDisjoint(
            with: Set(policy.localPersistence.locationTerms)
        )
        let deferredSync = !tokens.isDisjoint(
            with: Set(policy.deferredSync.actionTerms)
        ) && !tokens.isDisjoint(
            with: Set(policy.deferredSync.connectivityTerms)
        ) && !tokens.isDisjoint(
            with: Set(policy.deferredSync.conditionTerms)
        )
        return localPersistence && deferredSync ? .verified : .notVerified
    }
}

private extension KeyedEncodingContainer {
    mutating func encodeNullable<T: Encodable>(
        _ value: T?,
        forKey key: Key
    ) throws {
        if let value {
            try encode(value, forKey: key)
        } else {
            try encodeNil(forKey: key)
        }
    }
}
