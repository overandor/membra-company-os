import Cocoa
import WebKit

// ──────────────────────────────────────────────────────────────────────
// Doctor Address Verifier — Native macOS Wrapper
//
// This app:
//   1. Starts a bundled Ollama server (from Resources/bin/ollama)
//   2. Starts the Flask verification server (PyInstaller binary from Resources/bin/flask_server)
//   3. Opens a native macOS window with a WKWebView pointing to http://127.0.0.1:5001
//   4. Manages both subprocesses and cleans up on quit
// ──────────────────────────────────────────────────────────────────────

let FLASK_PORT: Int = 5001
let OLLAMA_PORT: Int = 11434

// MARK: - Process Manager

class ProcessManager {
    private var ollamaProcess: Process?
    private var flaskProcess: Process?
    private let resourcesPath: String

    init() {
        // Resolve the Resources directory inside the .app bundle
        if let bundlePath = Bundle.main.resourcePath {
            resourcesPath = bundlePath
        } else {
            resourcesPath = FileManager.default.currentDirectoryPath
        }
    }

    /// Start the bundled Ollama server
    func startOllama() {
        let ollamaBin = "\(resourcesPath)/bin/ollama"

        guard FileManager.default.fileExists(atPath: ollamaBin) else {
            print("[ProcessManager] Ollama binary not found at \(ollamaBin)")
            print("[ProcessManager] Continuing without Ollama — rule-based mode only")
            return
        }

        // Make sure the binary is executable
        try? FileManager.default.setAttributes(
            [.posixPermissions: 0o755],
            ofItemAtPath: ollamaBin
        )

        let process = Process()
        process.executableURL = URL(fileURLWithPath: ollamaBin)
        process.arguments = ["serve"]
        process.environment = ProcessInfo.processInfo.environment.merging(
            [
                "OLLAMA_HOST": "127.0.0.1:\(OLLAMA_PORT)",
                "OLLAMA_MODELS": "\(dataDirectory())/models",
            ],
            uniquingKeysWith: { _, new in new }
        )

        // Redirect stdout/stderr to suppress Ollama logs in console
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice

        do {
            try process.run()
            ollamaProcess = process
            print("[ProcessManager] Ollama started (PID: \(process.processIdentifier))")
        } catch {
            print("[ProcessManager] Failed to start Ollama: \(error)")
        }
    }

    /// Start the Flask verification server (PyInstaller binary)
    func startFlaskServer() {
        let flaskBin = "\(resourcesPath)/bin/flask_server"

        guard FileManager.default.fileExists(atPath: flaskBin) else {
            print("[ProcessManager] Flask server binary not found at \(flaskBin)")
            // Try Python fallback for development
            startFlaskDev()
            return
        }

        // Make sure the binary is executable
        try? FileManager.default.setAttributes(
            [.posixPermissions: 0o755],
            ofItemAtPath: flaskBin
        )

        let dataDir = dataDirectory()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: flaskBin)
        process.environment = ProcessInfo.processInfo.environment.merging(
            [
                "FLASK_PORT": "\(FLASK_PORT)",
                "OLLAMA_HOST": "http://127.0.0.1:\(OLLAMA_PORT)",
                "UPLOAD_DIR": "\(dataDir)/uploads",
                "RESULTS_DIR": "\(dataDir)/results",
                // Don't set NO_OLLAMA — let the app try Ollama by default
            ],
            uniquingKeysWith: { _, new in new }
        )

        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice

        do {
            try process.run()
            flaskProcess = process
            print("[ProcessManager] Flask server started (PID: \(process.processIdentifier))")
        } catch {
            print("[ProcessManager] Failed to start Flask server: \(error)")
        }
    }

    /// Fallback: start Flask from Python source (for development)
    private func startFlaskDev() {
        guard let python = findPython() else {
            print("[ProcessManager] Python not found — cannot start Flask server")
            return
        }

        let appPy = "\(resourcesPath)/app_bundle.py"
        guard FileManager.default.fileExists(atPath: appPy) else {
            print("[ProcessManager] app_bundle.py not found at \(appPy)")
            return
        }

        let dataDir = dataDirectory()
        let process = Process()
        process.executableURL = URL(fileURLWithPath: python)
        process.arguments = ["-c", """
            import sys, os
            sys.path.insert(0, '\(resourcesPath)')
            os.environ['FLASK_PORT'] = '\(FLASK_PORT)'
            os.environ['OLLAMA_HOST'] = 'http://127.0.0.1:\(OLLAMA_PORT)'
            os.environ['UPLOAD_DIR'] = '\(dataDir)/uploads'
            os.environ['RESULTS_DIR'] = '\(dataDir)/results'
            os.environ['FLASK_TEMPLATE_DIR'] = '\(resourcesPath)/templates'
            from app_bundle import create_app
            app = create_app()
            app.run(host='127.0.0.1', port=\(FLASK_PORT), debug=False, use_reloader=False)
        """]

        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice

        do {
            try process.run()
            flaskProcess = process
            print("[ProcessManager] Flask dev server started via Python (PID: \(process.processIdentifier))")
        } catch {
            print("[ProcessManager] Failed to start Flask dev server: \(error)")
        }
    }

    /// Find python3 on the system
    private func findPython() -> String? {
        let candidates = ["/usr/local/bin/python3", "/usr/bin/python3", "/opt/homebrew/bin/python3"]
        for path in candidates {
            if FileManager.default.fileExists(atPath: path) {
                return path
            }
        }
        return nil
    }

    /// Get the user data directory (~/Documents/DoctorAddressVerifier)
    func dataDirectory() -> String {
        let dir = NSHomeDirectory() + "/Documents/DoctorAddressVerifier"
        try? FileManager.default.createDirectory(
            atPath: dir, withIntermediateDirectories: true
        )
        try? FileManager.default.createDirectory(
            atPath: dir + "/uploads", withIntermediateDirectories: true
        )
        try? FileManager.default.createDirectory(
            atPath: dir + "/results", withIntermediateDirectories: true
        )
        try? FileManager.default.createDirectory(
            atPath: dir + "/models", withIntermediateDirectories: true
        )
        return dir
    }

    /// Stop all managed processes
    func stopAll() {
        if let p = flaskProcess, p.isRunning {
            p.terminate()
            print("[ProcessManager] Flask server stopped")
        }
        if let p = ollamaProcess, p.isRunning {
            p.terminate()
            print("[ProcessManager] Ollama stopped")
        }
    }

    /// Wait for the Flask server to be ready
    func waitForFlask(timeout: TimeInterval = 15, completion: @escaping (Bool) -> Void) {
        let deadline = Date().addingTimeInterval(timeout)
        let queue = DispatchQueue.global(qos: .background)

        func check() {
            guard Date() < deadline else {
                DispatchQueue.main.async { completion(false) }
                return
            }

            var request = URLRequest(url: URL(string: "http://127.0.0.1:\(FLASK_PORT)/")!)
            request.timeoutInterval = 2

            URLSession.shared.dataTask(with: request) { _, response, _ in
                if let http = response as? HTTPURLResponse, http.statusCode == 200 {
                    DispatchQueue.main.async { completion(true) }
                } else {
                    queue.asyncAfter(deadline: .now() + 0.5) { check() }
                }
            }.resume()
        }

        queue.async { check() }
    }
}

// MARK: - App Delegate

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    let processManager = ProcessManager()

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Start background services
        processManager.startOllama()

        // Small delay to let Ollama initialize before Flask tries to connect
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [self] in
            processManager.startFlaskServer()

            // Wait for Flask to be ready, then load the web UI
            processManager.waitForFlask { [weak self] ready in
                guard let self = self else { return }
                if ready {
                    self.loadWebUI()
                } else {
                    self.showError("Flask server failed to start within 15 seconds.")
                }
            }
        }

        // Create the main window
        createWindow()
    }

    func applicationWillTerminate(_ notification: Notification) {
        processManager.stopAll()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    private func createWindow() {
        // Configure WebView
        let config = WKWebViewConfiguration()
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")

        webView = WKWebView(frame: .zero, configuration: config)
        webView.translatesAutoresizingMaskIntoConstraints = false

        // Show a loading page
        webView.loadHTMLString(loadingHTML(), baseURL: nil)

        // Create window
        let screenSize = NSScreen.main?.frame.size ?? NSSize(width: 1280, height: 800)
        let windowWidth: CGFloat = min(1100, screenSize.width * 0.8)
        let windowHeight: CGFloat = min(800, screenSize.height * 0.8)
        let windowRect = NSRect(
            x: (screenSize.width - windowWidth) / 2,
            y: (screenSize.height - windowHeight) / 2,
            width: windowWidth,
            height: windowHeight
        )

        window = NSWindow(
            contentRect: windowRect,
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "Doctor Address Verifier"
        window.minSize = NSSize(width: 600, height: 400)
        window.contentView = webView
        window.makeKeyAndOrderFront(nil)

        // Set up constraints
        if let contentView = window.contentView {
            NSLayoutConstraint.activate([
                webView.topAnchor.constraint(equalTo: contentView.topAnchor),
                webView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),
                webView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
                webView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            ])
        }
    }

    private func loadWebUI() {
        guard let url = URL(string: "http://127.0.0.1:\(FLASK_PORT)/") else { return }
        webView.load(URLRequest(url: url))
    }

    private func showError(_ message: String) {
        let errorHTML = """
        <html>
        <body style="background:#141414;color:#f3f4f6;font-family:-apple-system,sans-serif;
                     display:flex;align-items:center;justify-content:center;height:100vh;
                     flex-direction:column;">
            <h1 style="color:#f53b3a;">Startup Error</h1>
            <p>\(message)</p>
            <p style="color:#9ca3af;margin-top:1rem;">
                Check Console.app for logs, or try restarting the application.
            </p>
        </body>
        </html>
        """
        webView.loadHTMLString(errorHTML, baseURL: nil)
    }

    private func loadingHTML() -> String {
        return """
        <html>
        <body style="background:#141414;color:#f3f4f6;font-family:-apple-system,sans-serif;
                     display:flex;align-items:center;justify-content:center;height:100vh;
                     flex-direction:column;">
            <div style="text-align:center;">
                <h1 style="background:linear-gradient(135deg,#7a84ff,#a78cff);
                           -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                           font-size:2rem;">
                    Doctor Address Verifier
                </h1>
                <p style="color:#c7d2fe;margin-top:1rem;">Starting services...</p>
                <div style="margin-top:2rem;">
                    <div style="width:200px;height:4px;background:#2e2e2e;border-radius:2px;
                                overflow:hidden;margin:0 auto;">
                        <div style="width:40%;height:100%;background:linear-gradient(90deg,#7a84ff,#a78cff);
                                    border-radius:2px;animation:loading 1.5s ease-in-out infinite;">
                        </div>
                    </div>
                </div>
                <p style="color:#9ca3af;font-size:0.8rem;margin-top:1.5rem;">
                    Starting Ollama &amp; Flask server...
                </p>
            </div>
            <style>
                @keyframes loading {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(350%); }
                }
            </style>
        </body>
        </html>
        """
    }
}

// MARK: - Application Entry Point

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate

// Set activation policy to regular (shows in Dock)
app.setActivationPolicy(.regular)
app.activate(ignoringOtherApps: true)
app.run()
