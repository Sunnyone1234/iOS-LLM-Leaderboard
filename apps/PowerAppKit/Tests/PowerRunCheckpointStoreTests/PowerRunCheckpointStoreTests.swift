import Foundation
import PowerEvidence
import PowerRunCheckpointStore
import PowerRunnerCore
import PowerTextProgram
import XCTest

final class PowerRunCheckpointStoreTests: XCTestCase {
    func testInterruptedAttemptBecomesFailedAndLaterAttemptsNotRun()
        async throws
    {
        let directory = temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = try PowerRunCheckpointStore(
            directory: directory,
            context: fixtureContext()
        )
        try await store.beginSession(fixtureSessionStart())
        try await store.record(
            fixtureAttempt(index: 0, phase: .warmup)
        )
        try await store.markAttemptStarted(
            index: 1,
            phase: .measured,
            startedAt: "2026-07-25T10:00:01.000Z",
            thermalStateAtStart: .fair
        )

        let recovery = try XCTUnwrap(
            PowerRunCheckpointStore.recover(
                from: directory,
                recoveredAt: "2026-07-25T10:00:02.000Z"
            )
        )
        let envelope = try XCTUnwrap(recovery.envelope)

        XCTAssertEqual(envelope.resultID, fixtureResultID)
        XCTAssertEqual(envelope.payload.attempts.count, 6)
        XCTAssertEqual(envelope.payload.attempts[0].outcome, .succeeded)
        XCTAssertEqual(envelope.payload.attempts[1].outcome, .failed)
        XCTAssertEqual(
            envelope.payload.attempts[1].failure?.code,
            "process_terminated_during_attempt"
        )
        XCTAssertEqual(
            envelope.payload.attempts.dropFirst(2).map(\.outcome),
            Array(repeating: .notRun, count: 4)
        )
        XCTAssertTrue(recovery.notice.contains("interrupted"))
    }

    func testCompletedCheckpointRecoversWithoutChangingAttempts()
        async throws
    {
        let directory = temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = try PowerRunCheckpointStore(
            directory: directory,
            context: fixtureContext()
        )
        try await store.beginSession(fixtureSessionStart())
        for index in 0..<6 {
            let phase: PowerAttemptPhase =
                index == 0 ? .warmup : .measured
            try await store.markAttemptStarted(
                index: index,
                phase: phase,
                startedAt: "2026-07-25T10:00:0\(index).000Z",
                thermalStateAtStart: .nominal
            )
            try await store.record(
                fixtureAttempt(index: index, phase: phase)
            )
        }
        try await store.finishSession(
            .init(
                endedAt: "2026-07-25T10:00:10.000Z",
                thermalStateAtEnd: .fair
            )
        )

        let recovery = try XCTUnwrap(
            PowerRunCheckpointStore.recover(from: directory)
        )
        let envelope = try XCTUnwrap(recovery.envelope)

        XCTAssertEqual(
            envelope.payload.attempts.map(\.outcome),
            Array(repeating: .succeeded, count: 6)
        )
        XCTAssertEqual(envelope.environment.thermalStateAtEnd, .fair)
        XCTAssertTrue(recovery.notice.contains("completed"))
    }

    func testPreparationCheckpointDoesNotInventBenchmarkEvidence()
        throws
    {
        let directory = temporaryDirectory()
        defer { try? FileManager.default.removeItem(at: directory) }
        _ = try PowerRunCheckpointStore(
            directory: directory,
            context: fixtureContext()
        )

        let recovery = try XCTUnwrap(
            PowerRunCheckpointStore.recover(from: directory)
        )

        XCTAssertNil(recovery.envelope)
        XCTAssertTrue(recovery.notice.contains("No benchmark attempt"))
    }

    private let fixtureResultID = UUID(
        uuidString: "77777777-7777-4777-8777-777777777777"
    )!

    private func temporaryDirectory() -> URL {
        FileManager.default.temporaryDirectory.appendingPathComponent(
            UUID().uuidString,
            isDirectory: true
        )
    }

    private func fixtureContext() -> PowerRunCheckpointContext {
        .init(
            resultID: fixtureResultID,
            program: .init(
                id: "text-generation-performance",
                version: "2.0.0-draft.2",
                manifestSHA256: String(repeating: "1", count: 64)
            ),
            target: .init(
                id: "apple-iphone-physical",
                version: "1.0.0-draft.1",
                manifestSHA256: String(repeating: "2", count: 64)
            ),
            runnerCertificateID: "power-runner-test",
            appRelease: .init(
                version: "2.0.0",
                build: "4",
                sourceRevision: String(repeating: "3", count: 64),
                embeddedMeasurementStackSHA256: String(
                    repeating: "4",
                    count: 64
                )
            ),
            model: .init(
                registryEntryID: "model-test",
                registryEntrySHA256: String(repeating: "5", count: 64),
                artifactID: "mlx-community/model",
                artifactRevision: String(repeating: "6", count: 40),
                parameterCount: 1_000_000_000,
                quantization: "4-bit",
                format: "MLX Safetensors"
            ),
            workload: fixtureWorkload(),
            workloadSHA256: String(repeating: "7", count: 64),
            thermalAssistance: .none
        )
    }

    private func fixtureSessionStart() -> PowerRunnerSessionStart {
        .init(
            startedAt: "2026-07-25T10:00:00.000Z",
            targetAtStart: .init(
                isPhysicalDevice: true,
                device: .init(
                    machineIdentifier: "iPhone15,3",
                    osVersion: "iOS 26.5",
                    osBuild: "23F84"
                ),
                batteryLevel: 0.8,
                batteryState: .unplugged,
                lowPowerModeEnabled: false,
                thermalState: .nominal
            ),
            runtimeIdentity: .init(
                name: "MLX Swift LM",
                version: "3.31.4",
                resolvedRevision: String(repeating: "8", count: 40),
                backend: "mlx-metal",
                configuration: [:]
            ),
            expectedAttemptCount: 6
        )
    }

    private func fixtureWorkload() -> PowerTextWorkload {
        .init(
            schemaVersion: "power-workload-1.0.0-draft.1",
            programID: "text-generation-performance",
            programVersion: "2.0.0-draft.2",
            workloadID: "power.text.short-interaction",
            workloadVersion: "1.0.0-draft.2",
            status: "migration-draft",
            title: "Short Interaction",
            category: "interactive",
            fixture: .init(
                path: "fixture.txt",
                sha256: String(repeating: "9", count: 64)
            ),
            measurementMode: "warm-resident-interactive-v1",
            generation: .init(
                sampling: false,
                temperature: 0,
                topP: 1,
                topK: 0,
                seed: 0,
                maximumOutputTokens: 128,
                reasoningMode: "disabled",
                newContextPerAttempt: true,
                newKVCachePerAttempt: true
            ),
            procedure: .init(
                warmupAttempts: 1,
                measuredAttempts: 5,
                restIntervalSeconds: 0
            ),
            primaryMetric: "first-renderable-proxy-ttft-ms",
            metrics: ["first-renderable-proxy-ttft-ms"]
        )
    }

    private func fixtureAttempt(
        index: Int,
        phase: PowerAttemptPhase
    ) -> PowerRunnerAttemptRecord {
        .init(
            index: index,
            phase: phase,
            outcome: .succeeded,
            startedAt: "2026-07-25T10:00:00.000Z",
            endedAt: "2026-07-25T10:00:01.000Z",
            requestAcceptedNanoseconds: 0,
            firstTokenNanoseconds: 100,
            firstRenderableNanoseconds: 110,
            completedNanoseconds: 500,
            promptEvaluationNanoseconds: 90,
            decodeNanoseconds: 400,
            inputTokenCount: 10,
            outputTokenCount: 5,
            tokenEvents: [],
            generatedText: "fixture",
            peakPhysicalFootprintBytes: 1_000,
            memorySamples: [],
            thermalStateAtStart: .nominal,
            thermalStateAtEnd: .nominal,
            thermalTransitions: [],
            failure: nil
        )
    }
}
