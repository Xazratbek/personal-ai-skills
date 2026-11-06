import CoreLocation
import SwiftUI
import UserNotifications
import os

private let log = Logger(subsystem: "com.phonemcp.fixture", category: "fixture")

final class Locator: NSObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var report: ((String) -> Void)?

    func start(_ report: @escaping (String) -> Void) {
        self.report = report
        manager.delegate = self
        manager.requestWhenInUseAuthorization()
        manager.startUpdatingLocation()
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let c = locations.last?.coordinate else { return }
        report?(String(format: "loc:%.2f,%.2f", c.latitude, c.longitude))
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {}
}

@main
struct FixtureApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }
    }
}

struct ContentView: View {
    @Environment(\.colorScheme) private var scheme
    @State private var status = "ready"
    @State private var field = ""
    @State private var on = false
    @State private var locator = Locator()
    @AppStorage("taps") private var taps = 0

    private func set(_ s: String) {
        status = s
        log.info("\(s, privacy: .public)")
    }

    var body: some View {
        VStack(spacing: 10) {
            Text(status).accessibilityIdentifier("status")
            Text("scheme=\(scheme == .dark ? "dark" : "light") taps=\(taps)").accessibilityIdentifier("info")
            TextField("Type here", text: $field)
                .textFieldStyle(.roundedBorder)
                .autocorrectionDisabled()
                .textInputAutocapitalization(.never)
                .accessibilityIdentifier("field")
                .onSubmit { set("submit:\(field)") }
            Button("Tap me") { taps += 1; set("tap:\(taps)") }.accessibilityIdentifier("tap_btn")
            Button("Ask notify") {
                UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { ok, _ in
                    DispatchQueue.main.async { set("notify:\(ok)") }
                }
            }.accessibilityIdentifier("notify_btn")
            Button("Where") { locator.start { set($0) } }.accessibilityIdentifier("where_btn")
            Button { set("icon") } label: { Image(systemName: "plus") }
                .accessibilityIdentifier("icon_btn")
                .accessibilityLabel("")
            Text("Hold me")
                .padding(8)
                .accessibilityAddTraits(.isButton)
                .accessibilityIdentifier("hold_btn")
                .onLongPressGesture(minimumDuration: 0.5) { set("long") }
            Text("Double me")
                .padding(8)
                .accessibilityAddTraits(.isButton)
                .accessibilityIdentifier("double_btn")
                .onTapGesture(count: 2) { set("double") }
            Toggle("Toggle", isOn: $on)
                .accessibilityIdentifier("toggle")
                .onChange(of: on) { _, new in set("switch:\(new ? "on" : "off")") }
            Text("Drag area")
                .frame(maxWidth: .infinity, minHeight: 60)
                .background(Color.blue.opacity(0.2))
                .accessibilityIdentifier("drag_area")
                .gesture(DragGesture(minimumDistance: 5).onEnded { v in
                    set("drag:\(Int(v.translation.width)),\(Int(v.translation.height))")
                })
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    ForEach(1...60, id: \.self) { i in Text("Item \(i)") }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding()
        .onOpenURL { set("url:\($0.absoluteString)") }
    }
}
