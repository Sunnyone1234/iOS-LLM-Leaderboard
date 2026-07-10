import Foundation

actor ResultStore {
    func save(_ submission: CommunitySubmissionBundle) throws -> URL {
        let directory = try FileManager.default.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
            .appending(path: "BenchmarkSubmissions", directoryHint: .isDirectory)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let formatter = ISO8601DateFormatter(); formatter.formatOptions = [.withInternetDateTime]
        let timestamp = formatter.string(from: submission.createdAt).replacingOccurrences(of: ":", with: "-")
        let url = directory.appending(path: "\(timestamp)_\(submission.result.workloadID)_submission_\(submission.submissionID.prefix(8)).json")
        let encoder = JSONEncoder(); encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(submission).write(to: url, options: .atomic)
        return url
    }

    func save(_ result: SuiteBResultBundle) throws -> URL {
        let fileManager = FileManager.default
        let directory = try fileManager.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
            .appending(path: "BenchmarkResults", directoryHint: .isDirectory)
        try fileManager.createDirectory(at: directory, withIntermediateDirectories: true)
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        let timestamp = formatter.string(from: result.createdAt).replacingOccurrences(of: ":", with: "-")
        let device = result.device.machineIdentifier.lowercased().replacingOccurrences(of: ",", with: "-")
        let url = directory.appending(path: "\(timestamp)_\(result.workload.id)_qwen3-0.6b-4bit_\(device)_\(result.resultID.prefix(8)).json")
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(result).write(to: url, options: .atomic)
        return url
    }

    func save(_ result: PilotResultBundle) throws -> URL {
        let fileManager = FileManager.default
        let directory = try fileManager.url(
            for: .documentDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        ).appending(path: "BenchmarkResults", directoryHint: .isDirectory)
        try fileManager.createDirectory(
            at: directory,
            withIntermediateDirectories: true
        )

        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        let timestamp = formatter.string(from: result.createdAt)
            .replacingOccurrences(of: ":", with: "-")
        let shortID = String(result.resultID.prefix(8))
        let deviceID = result.device.machineIdentifier
            .lowercased()
            .replacingOccurrences(of: ",", with: "-")
        let url = directory.appending(
            path: "\(timestamp)_b-pipe-001_qwen3-0.6b-4bit_\(deviceID)_\(shortID).json",
            directoryHint: .notDirectory
        )

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(result).write(to: url, options: .atomic)
        return url
    }

    func save(_ result: UXResultBundle) throws -> URL {
        let fileManager = FileManager.default
        let directory = try fileManager.url(
            for: .documentDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        ).appending(path: "BenchmarkResults", directoryHint: .isDirectory)
        try fileManager.createDirectory(at: directory, withIntermediateDirectories: true)
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        let timestamp = formatter.string(from: result.createdAt)
            .replacingOccurrences(of: ":", with: "-")
        let deviceID = result.device.machineIdentifier.lowercased()
            .replacingOccurrences(of: ",", with: "-")
        let name = "\(timestamp)_b-ux-001_qwen3-0.6b-4bit_\(deviceID)_\(result.resultID.prefix(8)).json"
        let url = directory.appending(path: name, directoryHint: .notDirectory)
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(result).write(to: url, options: .atomic)
        return url
    }

    func save(_ result: InputSweepResultBundle) throws -> URL {
        let fileManager = FileManager.default
        let directory = try fileManager.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
            .appending(path: "BenchmarkResults", directoryHint: .isDirectory)
        try fileManager.createDirectory(at: directory, withIntermediateDirectories: true)
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        let timestamp = formatter.string(from: result.createdAt).replacingOccurrences(of: ":", with: "-")
        let device = result.device.machineIdentifier.lowercased().replacingOccurrences(of: ",", with: "-")
        let url = directory.appending(path: "\(timestamp)_b-pipe-002_qwen3-0.6b-4bit_\(device)_\(result.resultID.prefix(8)).json")
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(result).write(to: url, options: .atomic)
        return url
    }

    func save(_ result: ContextAssistanceResultBundle) throws -> URL {
        let fileManager = FileManager.default
        let directory = try fileManager.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
            .appending(path: "BenchmarkResults", directoryHint: .isDirectory)
        try fileManager.createDirectory(at: directory, withIntermediateDirectories: true)
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        let timestamp = formatter.string(from: result.createdAt).replacingOccurrences(of: ":", with: "-")
        let device = result.device.machineIdentifier.lowercased().replacingOccurrences(of: ",", with: "-")
        let url = directory.appending(path: "\(timestamp)_b-ux-002_qwen3-0.6b-4bit_\(device)_\(result.resultID.prefix(8)).json")
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        try encoder.encode(result).write(to: url, options: .atomic)
        return url
    }
}
