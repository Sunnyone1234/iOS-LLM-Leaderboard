import Foundation

enum DeviceModelCatalog {
    private static let names: [String: String] = [
        "iPhone14,7": "iPhone 14",
        "iPhone14,8": "iPhone 14 Plus",
        "iPhone15,2": "iPhone 14 Pro",
        "iPhone15,3": "iPhone 14 Pro Max",
    ]

    static func displayName(for identifier: String) -> String {
        guard let name = names[identifier] else { return identifier }
        return "\(name) (\(identifier))"
    }
}
