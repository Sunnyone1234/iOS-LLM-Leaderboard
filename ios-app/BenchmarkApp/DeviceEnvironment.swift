import Foundation
import UIKit

struct DeviceEnvironment: Sendable {
    let modelIdentifier: String
    let systemName: String
    let systemVersion: String
    let systemBuild: String
    let operatingSystemVersion: OperatingSystemVersion
    let physicalMemoryBytes: UInt64
    let thermalState: String
    let debuggerAttached: Bool
    let buildConfiguration: String
    let appVersion: String
    let appBuild: String
    let appSourceCommit: String?
    let lowPowerModeEnabled: Bool
    let batteryLevelPercent: Double?
    let batteryState: String

    var systemDescription: String {
        "\(systemName) \(systemVersion)"
    }

    var deviceDescription: String {
        DeviceModelCatalog.displayName(for: modelIdentifier)
    }

    @MainActor static var current: DeviceEnvironment {
        var systemInfo = utsname()
        uname(&systemInfo)
        let identifier = withUnsafePointer(to: &systemInfo.machine) { pointer in
            pointer.withMemoryRebound(to: CChar.self, capacity: 1) {
                String(cString: $0)
            }
        }

        let processInfo = ProcessInfo.processInfo
        UIDevice.current.isBatteryMonitoringEnabled = true
        let batteryLevel = UIDevice.current.batteryLevel
        return DeviceEnvironment(
            modelIdentifier: identifier,
            systemName: UIDevice.current.systemName,
            systemVersion: UIDevice.current.systemVersion,
            systemBuild: Self.systemBuild,
            operatingSystemVersion: processInfo.operatingSystemVersion,
            physicalMemoryBytes: processInfo.physicalMemory,
            thermalState: processInfo.thermalState.benchmarkName,
            debuggerAttached: DebuggerStatus.isAttached,
            buildConfiguration: BuildMetadata.configuration,
            appVersion: BuildMetadata.appVersion,
            appBuild: BuildMetadata.appBuild,
            appSourceCommit: BuildMetadata.sourceCommit,
            lowPowerModeEnabled: processInfo.isLowPowerModeEnabled,
            batteryLevelPercent: batteryLevel >= 0
                ? Double(batteryLevel) * 100
                : nil,
            batteryState: UIDevice.current.batteryState.benchmarkName
        )
    }

    private static var systemBuild: String {
        var size = 0
        guard sysctlbyname("kern.osversion", nil, &size, nil, 0) == 0 else {
            return "unknown"
        }
        var value = [CChar](repeating: 0, count: size)
        guard sysctlbyname("kern.osversion", &value, &size, nil, 0) == 0 else {
            return "unknown"
        }
        let bytes = value.prefix { $0 != 0 }.map { UInt8(bitPattern: $0) }
        return String(decoding: bytes, as: UTF8.self)
    }
}

private extension UIDevice.BatteryState {
    var benchmarkName: String {
        switch self {
        case .unknown: "unknown"
        case .unplugged: "unplugged"
        case .charging: "charging"
        case .full: "full"
        @unknown default: "unknown"
        }
    }
}

private extension ProcessInfo.ThermalState {
    var benchmarkName: String {
        switch self {
        case .nominal: "nominal"
        case .fair: "fair"
        case .serious: "serious"
        case .critical: "critical"
        @unknown default: "unknown"
        }
    }
}
