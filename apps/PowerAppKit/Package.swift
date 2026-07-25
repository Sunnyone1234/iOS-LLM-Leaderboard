// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "PowerAppKit",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
    ],
    products: [
        .library(name: "PowerResultsStore", targets: ["PowerResultsStore"]),
        .library(
            name: "PowerRunCheckpointStore",
            targets: ["PowerRunCheckpointStore"]
        ),
        .library(
            name: "PowerReleasePreflight",
            targets: ["PowerReleasePreflight"]
        ),
        .library(
            name: "PowerSubmissionKit",
            targets: ["PowerSubmissionKit"]
        ),
        .library(
            name: "PowerGitHubSubmission",
            targets: ["PowerGitHubSubmission"]
        ),
    ],
    dependencies: [
        .package(path: "../PowerRunnerKit"),
    ],
    targets: [
        .target(
            name: "PowerResultsStore",
            dependencies: [
                .product(
                    name: "PowerEvidence",
                    package: "PowerRunnerKit"
                ),
            ]
        ),
        .target(
            name: "PowerRunCheckpointStore",
            dependencies: [
                .product(
                    name: "PowerEvidence",
                    package: "PowerRunnerKit"
                ),
                .product(
                    name: "PowerRunnerCore",
                    package: "PowerRunnerKit"
                ),
                .product(
                    name: "PowerTextProgram",
                    package: "PowerRunnerKit"
                ),
            ]
        ),
        .target(name: "PowerReleasePreflight"),
        .target(
            name: "PowerSubmissionKit",
            dependencies: [
                .product(
                    name: "PowerEvidence",
                    package: "PowerRunnerKit"
                ),
            ]
        ),
        .target(
            name: "PowerGitHubSubmission",
            dependencies: ["PowerSubmissionKit"]
        ),
        .target(
            name: "PowerAppKitTestSupport",
            dependencies: [
                .product(
                    name: "PowerEvidence",
                    package: "PowerRunnerKit"
                ),
            ],
            path: "Tests/PowerAppKitTestSupport"
        ),
        .testTarget(
            name: "PowerResultsStoreTests",
            dependencies: [
                "PowerResultsStore",
                "PowerAppKitTestSupport",
                .product(
                    name: "PowerEvidence",
                    package: "PowerRunnerKit"
                ),
            ]
        ),
        .testTarget(
            name: "PowerRunCheckpointStoreTests",
            dependencies: [
                "PowerRunCheckpointStore",
                .product(
                    name: "PowerEvidence",
                    package: "PowerRunnerKit"
                ),
                .product(
                    name: "PowerRunnerCore",
                    package: "PowerRunnerKit"
                ),
                .product(
                    name: "PowerTextProgram",
                    package: "PowerRunnerKit"
                ),
            ]
        ),
        .testTarget(
            name: "PowerReleasePreflightTests",
            dependencies: ["PowerReleasePreflight"]
        ),
        .testTarget(
            name: "PowerSubmissionKitTests",
            dependencies: [
                "PowerSubmissionKit",
                "PowerAppKitTestSupport",
                .product(
                    name: "PowerEvidence",
                    package: "PowerRunnerKit"
                ),
            ]
        ),
        .testTarget(
            name: "PowerGitHubSubmissionTests",
            dependencies: [
                "PowerGitHubSubmission",
                "PowerSubmissionKit",
                "PowerAppKitTestSupport",
                .product(
                    name: "PowerEvidence",
                    package: "PowerRunnerKit"
                ),
            ]
        ),
    ]
)
