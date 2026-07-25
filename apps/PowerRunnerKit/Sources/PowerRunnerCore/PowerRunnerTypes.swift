import Foundation
import PowerEvidence

public enum PowerRunnerLimits {
    public static let maximumRenderabilityProbeEvents = 32
}

public struct PowerTargetSnapshot: Codable, Sendable, Equatable {
    public let isPhysicalDevice: Bool
    public let device: PowerDeviceIdentity
    public let batteryLevel: Double
    public let batteryState: PowerBatteryState
    public let lowPowerModeEnabled: Bool
    public let thermalState: PowerThermalState

    public init(
        isPhysicalDevice: Bool,
        device: PowerDeviceIdentity,
        batteryLevel: Double,
        batteryState: PowerBatteryState,
        lowPowerModeEnabled: Bool,
        thermalState: PowerThermalState
    ) {
        self.isPhysicalDevice = isPhysicalDevice
        self.device = device
        self.batteryLevel = batteryLevel
        self.batteryState = batteryState
        self.lowPowerModeEnabled = lowPowerModeEnabled
        self.thermalState = thermalState
    }
}

public protocol PowerTargetAdapter: Sendable {
    func captureStart() async throws -> PowerTargetSnapshot
    func currentThermalState() async -> PowerThermalState
    func currentPhysicalFootprintBytes() async -> UInt64?
}

public struct PowerRuntimeRequest: Sendable, Equatable {
    public let prompt: String
    public let configuration: PowerInferenceConfiguration

    public init(
        prompt: String,
        configuration: PowerInferenceConfiguration
    ) {
        self.prompt = prompt
        self.configuration = configuration
    }
}

public struct PowerRuntimeToken: Sendable, Equatable {
    public let index: Int
    public let tokenID: Int

    public init(index: Int, tokenID: Int) {
        self.index = index
        self.tokenID = tokenID
    }
}

public struct PowerRuntimeRenderability: Sendable, Equatable {
    public let tokenIndex: Int
    public let decodedPrefix: String
    public let isSpecial: Bool

    public init(
        tokenIndex: Int,
        decodedPrefix: String,
        isSpecial: Bool
    ) {
        self.tokenIndex = tokenIndex
        self.decodedPrefix = decodedPrefix
        self.isSpecial = isSpecial
    }
}

public struct PowerRuntimeGenerationResult: Sendable, Equatable {
    public let inputTokenCount: Int
    public let outputTokenCount: Int
    public let generatedText: String
    public let promptEvaluationNanoseconds: UInt64

    public init(
        inputTokenCount: Int,
        outputTokenCount: Int,
        generatedText: String,
        promptEvaluationNanoseconds: UInt64
    ) {
        self.inputTokenCount = inputTokenCount
        self.outputTokenCount = outputTokenCount
        self.generatedText = generatedText
        self.promptEvaluationNanoseconds = promptEvaluationNanoseconds
    }
}

public protocol PowerRuntimeAdapter: Sendable {
    var identity: PowerRuntimeIdentity { get async }

    func generate(
        request: PowerRuntimeRequest,
        onToken: @escaping @Sendable (PowerRuntimeToken) async -> Void,
        onRenderability: @escaping @Sendable (
            PowerRuntimeRenderability
        ) async -> Bool
    ) async throws -> PowerRuntimeGenerationResult
}

public enum PowerRuntimeFailureKind: Sendable, Equatable {
    case failed(code: String)
    case outOfMemory(code: String)
}

public protocol PowerRuntimeFailureClassifyingError: Error {
    var powerRuntimeFailureKind: PowerRuntimeFailureKind { get }
}

public struct PowerRunnerAttemptRequest: Sendable, Equatable {
    public let index: Int
    public let phase: PowerAttemptPhase
    public let runtimeRequest: PowerRuntimeRequest

    public init(
        index: Int,
        phase: PowerAttemptPhase,
        runtimeRequest: PowerRuntimeRequest
    ) {
        self.index = index
        self.phase = phase
        self.runtimeRequest = runtimeRequest
    }
}

public struct PowerRunnerAttemptRecord: Codable, Sendable, Equatable {
    public let index: Int
    public let phase: PowerAttemptPhase
    public let outcome: PowerAttemptOutcome
    public let startedAt: String
    public let endedAt: String
    public let requestAcceptedNanoseconds: UInt64
    public let firstTokenNanoseconds: UInt64?
    public let firstRenderableNanoseconds: UInt64?
    public let completedNanoseconds: UInt64?
    public let promptEvaluationNanoseconds: UInt64?
    public let decodeNanoseconds: UInt64?
    public let inputTokenCount: Int
    public let outputTokenCount: Int
    public let tokenEvents: [PowerTokenEvent]
    public let generatedText: String
    public let peakPhysicalFootprintBytes: UInt64?
    public let memorySamples: [PowerMemorySample]
    public let thermalStateAtStart: PowerThermalState
    public let thermalStateAtEnd: PowerThermalState
    public let thermalTransitions: [PowerThermalTransition]
    public let failure: PowerAttemptFailure?

    public init(
        index: Int,
        phase: PowerAttemptPhase,
        outcome: PowerAttemptOutcome,
        startedAt: String,
        endedAt: String,
        requestAcceptedNanoseconds: UInt64,
        firstTokenNanoseconds: UInt64?,
        firstRenderableNanoseconds: UInt64?,
        completedNanoseconds: UInt64?,
        promptEvaluationNanoseconds: UInt64?,
        decodeNanoseconds: UInt64?,
        inputTokenCount: Int,
        outputTokenCount: Int,
        tokenEvents: [PowerTokenEvent],
        generatedText: String,
        peakPhysicalFootprintBytes: UInt64?,
        memorySamples: [PowerMemorySample],
        thermalStateAtStart: PowerThermalState,
        thermalStateAtEnd: PowerThermalState,
        thermalTransitions: [PowerThermalTransition],
        failure: PowerAttemptFailure?
    ) {
        self.index = index
        self.phase = phase
        self.outcome = outcome
        self.startedAt = startedAt
        self.endedAt = endedAt
        self.requestAcceptedNanoseconds = requestAcceptedNanoseconds
        self.firstTokenNanoseconds = firstTokenNanoseconds
        self.firstRenderableNanoseconds = firstRenderableNanoseconds
        self.completedNanoseconds = completedNanoseconds
        self.promptEvaluationNanoseconds = promptEvaluationNanoseconds
        self.decodeNanoseconds = decodeNanoseconds
        self.inputTokenCount = inputTokenCount
        self.outputTokenCount = outputTokenCount
        self.tokenEvents = tokenEvents
        self.generatedText = generatedText
        self.peakPhysicalFootprintBytes = peakPhysicalFootprintBytes
        self.memorySamples = memorySamples
        self.thermalStateAtStart = thermalStateAtStart
        self.thermalStateAtEnd = thermalStateAtEnd
        self.thermalTransitions = thermalTransitions
        self.failure = failure
    }
}

public struct PowerRunnerSession: Codable, Sendable, Equatable {
    public let startedAt: String
    public let endedAt: String
    public let targetAtStart: PowerTargetSnapshot
    public let thermalStateAtEnd: PowerThermalState
    public let runtimeIdentity: PowerRuntimeIdentity
    public let attempts: [PowerRunnerAttemptRecord]

    public init(
        startedAt: String,
        endedAt: String,
        targetAtStart: PowerTargetSnapshot,
        thermalStateAtEnd: PowerThermalState,
        runtimeIdentity: PowerRuntimeIdentity,
        attempts: [PowerRunnerAttemptRecord]
    ) {
        self.startedAt = startedAt
        self.endedAt = endedAt
        self.targetAtStart = targetAtStart
        self.thermalStateAtEnd = thermalStateAtEnd
        self.runtimeIdentity = runtimeIdentity
        self.attempts = attempts
    }
}

public struct PowerRunnerSessionStart: Codable, Sendable, Equatable {
    public let startedAt: String
    public let targetAtStart: PowerTargetSnapshot
    public let runtimeIdentity: PowerRuntimeIdentity
    public let expectedAttemptCount: Int

    public init(
        startedAt: String,
        targetAtStart: PowerTargetSnapshot,
        runtimeIdentity: PowerRuntimeIdentity,
        expectedAttemptCount: Int
    ) {
        self.startedAt = startedAt
        self.targetAtStart = targetAtStart
        self.runtimeIdentity = runtimeIdentity
        self.expectedAttemptCount = expectedAttemptCount
    }
}

public struct PowerRunnerSessionCompletion: Codable, Sendable, Equatable {
    public let endedAt: String
    public let thermalStateAtEnd: PowerThermalState

    public init(
        endedAt: String,
        thermalStateAtEnd: PowerThermalState
    ) {
        self.endedAt = endedAt
        self.thermalStateAtEnd = thermalStateAtEnd
    }
}

/// A checkpoint sink can persist an active attempt before runtime execution.
/// On relaunch it can convert an unfinished active attempt into retained
/// cancellation/failure evidence rather than dropping it.
public protocol PowerAttemptCheckpointSink: Sendable {
    func beginSession(_ start: PowerRunnerSessionStart) async throws

    func markAttemptStarted(
        index: Int,
        phase: PowerAttemptPhase,
        startedAt: String,
        thermalStateAtStart: PowerThermalState
    ) async throws

    func record(_ attempt: PowerRunnerAttemptRecord) async throws

    func finishSession(
        _ completion: PowerRunnerSessionCompletion
    ) async throws
}

public extension PowerAttemptCheckpointSink {
    func beginSession(_ start: PowerRunnerSessionStart) async throws {}

    func finishSession(
        _ completion: PowerRunnerSessionCompletion
    ) async throws {}
}
