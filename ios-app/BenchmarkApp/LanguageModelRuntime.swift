import Foundation

struct RuntimeToken: Codable, Sendable, Equatable {
    let index: Int
    let tokenID: Int
    let elapsedNanoseconds: UInt64
}

struct FirstRenderableTrace: Codable, Sendable, Equatable {
    static let currentPolicyVersion = "first-renderable-decoded-prefix-v1"
    static let traceClockOrigin = "adapter-request-accepted"
    static let traceScope = "through-first-renderable-inclusive"
    static let maximumCaptureEntries = 32

    enum Outcome: String, Codable, Sendable {
        case firstRenderableFound
        case noRenderableContent
        case captureLimitReached
    }

    struct Entry: Codable, Sendable, Equatable {
        let tokenIndex: Int
        let tokenID: Int
        let tokenReceivedNanoseconds: UInt64
        let decodedAtNanoseconds: UInt64
        let decodedPrefix: String
        let isRenderable: Bool
    }

    let policyVersion: String
    let clockOrigin: String
    let scope: String
    let captureLimit: Int
    let generationStartNanoseconds: UInt64
    let outcome: Outcome
    let firstRenderableTokenIndex: Int?
    let entries: [Entry]

    var firstRenderableDecodedAtNanoseconds: UInt64? {
        guard let firstRenderableTokenIndex else { return nil }
        return entries.first {
            $0.tokenIndex == firstRenderableTokenIndex && $0.isRenderable
        }?.decodedAtNanoseconds
    }

    static func isRenderable(_ decodedPrefix: String) -> Bool {
        decodedPrefix.unicodeScalars.contains { !isPolicyWhitespace($0.value) }
    }

    private static func isPolicyWhitespace(_ value: UInt32) -> Bool {
        switch value {
        case 0x0009...0x000D,
             0x0020,
             0x0085,
             0x00A0,
             0x1680,
             0x2000...0x200A,
             0x2028...0x2029,
             0x202F,
             0x205F,
             0x3000:
            return true
        default:
            return false
        }
    }
}

struct FirstRenderableTraceRecorder: Sendable {
    private let generationStartNanoseconds: UInt64
    private var entries: [FirstRenderableTrace.Entry] = []
    private var firstRenderableTokenIndex: Int?

    init(generationStartNanoseconds: UInt64) {
        self.generationStartNanoseconds = generationStartNanoseconds
        entries.reserveCapacity(FirstRenderableTrace.maximumCaptureEntries)
    }

    var shouldDecodeNextToken: Bool {
        firstRenderableTokenIndex == nil
            && entries.count < FirstRenderableTrace.maximumCaptureEntries
    }

    mutating func record(
        tokenIndex: Int,
        tokenID: Int,
        tokenReceivedNanoseconds: UInt64,
        decodedAtNanoseconds: UInt64,
        decodedPrefix: String
    ) {
        guard shouldDecodeNextToken else { return }
        let renderable = FirstRenderableTrace.isRenderable(decodedPrefix)
        entries.append(
            .init(
                tokenIndex: tokenIndex,
                tokenID: tokenID,
                tokenReceivedNanoseconds: tokenReceivedNanoseconds,
                decodedAtNanoseconds: decodedAtNanoseconds,
                decodedPrefix: decodedPrefix,
                isRenderable: renderable
            )
        )
        if renderable {
            firstRenderableTokenIndex = tokenIndex
        }
    }

    func finalize(outputTokenCount: Int) -> FirstRenderableTrace {
        let outcome: FirstRenderableTrace.Outcome
        if firstRenderableTokenIndex != nil {
            outcome = .firstRenderableFound
        } else if outputTokenCount > entries.count {
            outcome = .captureLimitReached
        } else {
            outcome = .noRenderableContent
        }
        return FirstRenderableTrace(
            policyVersion: FirstRenderableTrace.currentPolicyVersion,
            clockOrigin: FirstRenderableTrace.traceClockOrigin,
            scope: FirstRenderableTrace.traceScope,
            captureLimit: FirstRenderableTrace.maximumCaptureEntries,
            generationStartNanoseconds: generationStartNanoseconds,
            outcome: outcome,
            firstRenderableTokenIndex: firstRenderableTokenIndex,
            entries: entries
        )
    }
}

struct RuntimeGenerationResult: Codable, Sendable, Equatable {
    enum StopReason: String, Codable, Sendable {
        case endOfSequence
        case outputTokenLimit
        case cancelled
    }

    let promptTokenCount: Int
    let outputTokenCount: Int
    let stopReason: StopReason
    let promptTimeSeconds: Double?
    let generateTimeSeconds: Double?
    let userVisibleTTFTNanoseconds: UInt64?
    let requestCompletionNanoseconds: UInt64?
    let generatedText: String?
    let renderabilityTrace: FirstRenderableTrace?

    init(
        promptTokenCount: Int,
        outputTokenCount: Int,
        stopReason: StopReason,
        promptTimeSeconds: Double?,
        generateTimeSeconds: Double?,
        userVisibleTTFTNanoseconds: UInt64? = nil,
        requestCompletionNanoseconds: UInt64? = nil,
        generatedText: String? = nil,
        renderabilityTrace: FirstRenderableTrace? = nil
    ) {
        self.promptTokenCount = promptTokenCount
        self.outputTokenCount = outputTokenCount
        self.stopReason = stopReason
        self.promptTimeSeconds = promptTimeSeconds
        self.generateTimeSeconds = generateTimeSeconds
        self.userVisibleTTFTNanoseconds = userVisibleTTFTNanoseconds
        self.requestCompletionNanoseconds = requestCompletionNanoseconds
        self.generatedText = generatedText
        self.renderabilityTrace = renderabilityTrace
    }
}

protocol LanguageModelRuntime: Sendable {
    var identity: String { get }

    func generate(
        prompt: String,
        outputTokenLimit: Int,
        onToken: @Sendable (RuntimeToken) async -> Void
    ) async throws -> RuntimeGenerationResult
}

protocol ModelPreparingRuntime: LanguageModelRuntime {
    func prepare(plan: PilotPlan) async -> ModelPreparationEvidence
    func calibrateInputLengthFixtures(
        targets: [Int]
    ) async throws -> [InputLengthFixtureCalibration]
    func calibrateContextAssistanceFixtures(
        document: String,
        question: String,
        targets: [Int]
    ) async throws -> [InputLengthFixtureCalibration]
}

struct InputLengthFixtureCalibration: Sendable, Equatable {
    let targetTokenCount: Int
    let actualTokenCount: Int
    let paddingRepetitions: Int
    let promptSHA256: String
}

enum InputLengthFixtureGenerator {
    static let baseText = "Read the following benchmark input and reply with OK. Input:"

    static func prompt(paddingRepetitions: Int) -> String {
        baseText + String(repeating: " x", count: paddingRepetitions)
    }
}

enum ContextAssistanceFixtureGenerator {
    static func prompt(
        document: String,
        question: String,
        paddingRepetitions: Int
    ) -> String {
        document
            + "\nBackground records appendix:"
            + String(repeating: " x", count: paddingRepetitions)
            + "\n\nQuestion:\n" + question
    }
}
