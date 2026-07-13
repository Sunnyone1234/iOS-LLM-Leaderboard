import Foundation

struct ContextAnswerContract: Codable, Sendable, Equatable {
    let hasReferenceCode: Bool
    let hasLocalSafetyFact: Bool
    let hasStableNetworkFact: Bool
    let hasBatteryPowerFact: Bool
    let hasAvoidanceFact: Bool

    var passed: Bool {
        hasReferenceCode && hasLocalSafetyFact && hasStableNetworkFact
            && hasBatteryPowerFact && hasAvoidanceFact
    }

    static func evaluate(_ text: String?) -> ContextAnswerContract {
        let value = (text ?? "").lowercased()
        return .init(
            hasReferenceCode: value.contains("orchid-47"),
            hasLocalSafetyFact: value.contains("safe")
                && ["local", "vault", "iphone"].contains(where: value.contains),
            hasStableNetworkFact: value.contains("30")
                && ["stable", "seconds"].contains(where: value.contains),
            hasBatteryPowerFact: ["20", "15"].contains(where: value.contains)
                && ["power", "charg"].contains(where: value.contains),
            hasAvoidanceFact: ["do not", "don't", "avoid", "shouldn't"].contains(where: value.contains)
                && ["delete", "reinstall", "sign out"].contains(where: value.contains)
        )
    }
}
