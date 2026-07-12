import Darwin
import Foundation

enum DebuggerStatus {
    static var isAttached: Bool {
        var processInfo = kinfo_proc()
        var size = MemoryLayout<kinfo_proc>.stride
        var name: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()]
        let nameCount = u_int(name.count)
        let result = name.withUnsafeMutableBufferPointer { namePointer in
            sysctl(
                namePointer.baseAddress,
                nameCount,
                &processInfo,
                &size,
                nil,
                0
            )
        }
        guard result == 0 else { return false }
        return (processInfo.kp_proc.p_flag & P_TRACED) != 0
    }
}

enum BuildMetadata {
    static var configuration: String {
        #if DEBUG
        "Debug"
        #else
        "Release"
        #endif
    }

    static var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString")
            as? String ?? "unknown"
    }

    static var appBuild: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion")
            as? String ?? "unknown"
    }

    static var sourceCommit: String? {
        guard let rawValue = Bundle.main.object(
            forInfoDictionaryKey: "GIT_COMMIT_SHA"
        ) as? String else {
            return nil
        }
        let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty,
              value != "unknown",
              value != "$(GIT_COMMIT_SHA)" else {
            return nil
        }
        return value
    }
}
