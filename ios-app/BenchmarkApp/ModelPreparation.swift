import Foundation

struct ModelPreparationEvidence: Codable, Sendable, Equatable {
    enum CacheState: String, Codable, Sendable {
        case cached
        case notCached = "not_cached"
        case incomplete
        case unknown
    }

    let artifactID: String
    let artifactRevision: String
    let cacheStateBeforePreparation: CacheState
    let downloadOccurredDuringSession: Bool
    let preparationDurationMilliseconds: Double
    let preparationCompleted: Bool
    let modelLoadCompleted: Bool
    let eligibleForPerformanceMeasurement: Bool
    let reasonCodes: [String]
    let cacheVerificationMethod: String
    let preparedAt: Date
}

struct BenchmarkAdmissionEnvironment: Sendable, Equatable {
    let debuggerAttached: Bool
    let buildConfiguration: String
    let lowPowerModeEnabled: Bool
    let thermalState: String
}

enum BenchmarkAdmission {
    static func reasonCodes(
        preparation: ModelPreparationEvidence?,
        environment: BenchmarkAdmissionEnvironment,
        requirements: PilotPlan.EnvironmentRequirements
    ) -> [String] {
        var reasons: [String] = []
        guard let preparation else {
            reasons.append("model_not_prepared")
            return reasons + environmentReasons(
                environment,
                requirements: requirements
            )
        }
        if !preparation.eligibleForPerformanceMeasurement {
            if preparation.reasonCodes.isEmpty {
                reasons.append("model_preparation_failed")
            } else {
                reasons.append(contentsOf: preparation.reasonCodes)
            }
        }
        reasons.append(contentsOf: environmentReasons(
            environment,
            requirements: requirements
        ))
        return Array(Set(reasons)).sorted()
    }

    private static func environmentReasons(
        _ environment: BenchmarkAdmissionEnvironment,
        requirements: PilotPlan.EnvironmentRequirements
    ) -> [String] {
        var reasons: [String] = []
        if requirements.debuggerDetachedRequired && environment.debuggerAttached {
            reasons.append("debugger_attached")
        }
        if requirements.releaseBuildRequired
            && environment.buildConfiguration != "Release" {
            reasons.append("non_release_build")
        }
        if requirements.lowPowerMode == "off"
            && environment.lowPowerModeEnabled {
            reasons.append("low_power_mode_enabled")
        }
        if environment.thermalState != requirements.initialThermalState {
            reasons.append("initial_thermal_state_not_nominal")
        }
        return reasons
    }
}

enum ModelCacheVerification {
    static func classify(
        expectedFiles: [String: Int?],
        cachedFileSizes: [String: Int]
    ) -> ModelPreparationEvidence.CacheState {
        guard !expectedFiles.isEmpty,
              expectedFiles.values.allSatisfy({ $0 != nil }) else {
            return .unknown
        }
        let cachedRequiredCount = expectedFiles.keys.filter {
            cachedFileSizes[$0] != nil
        }.count
        if cachedRequiredCount == 0 {
            return .notCached
        }
        let complete = expectedFiles.allSatisfy { path, expectedSize in
            cachedFileSizes[path] == expectedSize
        }
        return complete ? .cached : .incomplete
    }
}
