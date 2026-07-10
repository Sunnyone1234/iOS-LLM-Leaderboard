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
}
