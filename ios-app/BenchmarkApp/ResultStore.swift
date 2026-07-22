import Foundation

actor ResultStore {
    struct StoredPowerResult: Sendable, Equatable {
        let result: PowerResultBundle
        let fileURL: URL

        var id: UUID { result.resultID }
    }

    private let documentsDirectory: URL?

    init(documentsDirectory: URL? = nil) {
        self.documentsDirectory = documentsDirectory
    }

    func save(_ package: PowerSubmissionPackage) throws -> URL {
        let root = try documentsRoot().appending(
            path: "PowerSubmissionPackages",
            directoryHint: .isDirectory
        )
        try FileManager.default.createDirectory(
            at: root,
            withIntermediateDirectories: true
        )
        let directory = root.appending(
            path: package.submissionID.uuidString.lowercased(),
            directoryHint: .isDirectory
        )
        let stagingDirectory = root.appending(
            path: ".\(package.submissionID.uuidString.lowercased()).\(UUID().uuidString.lowercased()).tmp",
            directoryHint: .isDirectory
        )
        try FileManager.default.createDirectory(
            at: stagingDirectory,
            withIntermediateDirectories: true
        )
        defer { try? FileManager.default.removeItem(at: stagingDirectory) }
        try package.resultData.write(
            to: stagingDirectory.appending(path: "result.json"),
            options: .atomic
        )
        try package.manifestData.write(
            to: stagingDirectory.appending(path: "submission.json"),
            options: .atomic
        )
        try FileManager.default.moveItem(
            at: stagingDirectory,
            to: directory
        )
        return directory
    }

    func save(_ result: PowerResultBundle) throws -> URL {
        try result.validateForExport()
        let directory = try powerResultsDirectory()
        try FileManager.default.createDirectory(
            at: directory,
            withIntermediateDirectories: true
        )
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        let timestamp = formatter.string(from: result.createdAt)
            .replacingOccurrences(of: ":", with: "-")
        let artifact = result.model.artifactID.lowercased()
            .replacingOccurrences(of: "/", with: "-")
            .replacingOccurrences(of: " ", with: "-")
        let device = result.device.machineIdentifier.lowercased()
            .replacingOccurrences(of: ",", with: "-")
        let url = directory.appending(
            path: "\(timestamp)_\(result.execution.workloadID)_\(artifact)_\(device)_\(result.resultID.uuidString.lowercased().prefix(8)).json"
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [
            .prettyPrinted, .sortedKeys, .withoutEscapingSlashes,
        ]
        try encoder.encode(result).write(to: url, options: .atomic)
        return url
    }

    func loadLatestPowerResult() throws -> StoredPowerResult? {
        try loadPowerResults().first
    }

    func loadPowerResults() throws -> [StoredPowerResult] {
        let directory = try powerResultsDirectory()
        guard FileManager.default.fileExists(atPath: directory.path) else {
            return []
        }
        let urls = try FileManager.default.contentsOfDirectory(
            at: directory,
            includingPropertiesForKeys: [.isRegularFileKey],
            options: [.skipsHiddenFiles]
        ).filter {
            $0.pathExtension.lowercased() == "json"
                && ((try? $0.resourceValues(forKeys: [.isRegularFileKey]))
                    .flatMap(\.isRegularFile) ?? false)
        }
        guard !urls.isEmpty else { return [] }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        var results: [StoredPowerResult] = []
        var lastError: Error?
        for url in urls {
            do {
                let result = try decoder.decode(
                    PowerResultBundle.self,
                    from: Data(contentsOf: url)
                )
                try result.validateForExport()
                results.append(StoredPowerResult(result: result, fileURL: url))
            } catch {
                lastError = error
            }
        }
        if !results.isEmpty {
            return results.sorted {
                if $0.result.createdAt != $1.result.createdAt {
                    return $0.result.createdAt > $1.result.createdAt
                }
                return $0.result.resultID.uuidString < $1.result.resultID.uuidString
            }
        }
        throw lastError ?? CocoaError(.fileReadCorruptFile)
    }

    private func documentsRoot() throws -> URL {
        if let documentsDirectory { return documentsDirectory }
        return try FileManager.default.url(
            for: .documentDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
    }

    private func powerResultsDirectory() throws -> URL {
        try documentsRoot().appending(
            path: "PowerBenchmarkResults",
            directoryHint: .isDirectory
        )
    }

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
        let artifact = result.model.artifactID.lowercased()
            .replacingOccurrences(of: "/", with: "-")
            .replacingOccurrences(of: " ", with: "-")
        let url = directory.appending(path: "\(timestamp)_\(result.workload.id)_\(artifact)_\(device)_\(result.resultID.prefix(8)).json")
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
