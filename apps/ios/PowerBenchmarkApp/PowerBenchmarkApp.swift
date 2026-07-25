import SwiftUI

@main
struct PowerBenchmarkApp: App {
    @State private var model = PowerAppModel()

    var body: some Scene {
        WindowGroup {
            PowerRootView(model: model)
                .task {
                    await model.reloadResults()
                }
                .task {
                    await model.refreshReleaseEligibility()
                }
        }
    }
}
