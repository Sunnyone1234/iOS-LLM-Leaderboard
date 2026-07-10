import Foundation

struct RuntimeToken: Codable, Sendable, Equatable {
    let index: Int
    let tokenID: Int
    let elapsedNanoseconds: UInt64
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

    init(
        promptTokenCount: Int,
        outputTokenCount: Int,
        stopReason: StopReason,
        promptTimeSeconds: Double?,
        generateTimeSeconds: Double?,
        userVisibleTTFTNanoseconds: UInt64? = nil,
        requestCompletionNanoseconds: UInt64? = nil,
        generatedText: String? = nil
    ) {
        self.promptTokenCount = promptTokenCount
        self.outputTokenCount = outputTokenCount
        self.stopReason = stopReason
        self.promptTimeSeconds = promptTimeSeconds
        self.generateTimeSeconds = generateTimeSeconds
        self.userVisibleTTFTNanoseconds = userVisibleTTFTNanoseconds
        self.requestCompletionNanoseconds = requestCompletionNanoseconds
        self.generatedText = generatedText
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
