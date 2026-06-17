import Foundation
import Network

final class SpeechBubbleServer {
    private var listener: NWListener?
    private let queue = DispatchQueue(label: "SpeechBubbleServer")
    weak var controller: LilAgentsController?

    init(controller: LilAgentsController) {
        self.controller = controller
    }

    func start() {
        do {
            let params = NWParameters.tcp
            params.allowLocalEndpointReuse = true
            let listener = try NWListener(using: params, on: 8766)
            self.listener = listener
            listener.newConnectionHandler = { [weak self] conn in
                self?.handle(conn)
            }
            listener.start(queue: queue)
        } catch {
            print("[SpeechBubbleServer] Failed to start: \(error)")
        }
    }

    func stop() {
        listener?.cancel()
        listener = nil
    }

    private func handle(_ conn: NWConnection) {
        conn.start(queue: queue)
        conn.receive(minimumIncompleteLength: 1, maximumLength: 4096) { [weak self] data, _, _, _ in
            guard let self = self, let data = data, !data.isEmpty else {
                conn.cancel()
                return
            }
            let request = String(decoding: data, as: UTF8.self)
            let response = self.handleRequest(request)
            conn.send(content: response, completion: .contentProcessed { _ in
                conn.cancel()
            })
        }
    }

    private func handleRequest(_ request: String) -> Data {
        guard let firstLine = request.components(separatedBy: "\r\n").first else {
            return httpResponse(status: 400, body: "Bad Request")
        }
        let parts = firstLine.split(separator: " ")
        guard parts.count >= 2 else {
            return httpResponse(status: 400, body: "Bad Request")
        }
        let target = String(parts[1])
        guard let comps = URLComponents(string: "http://localhost" + target) else {
            return httpResponse(status: 400, body: "Bad Request")
        }
        let path = comps.path
        let queryItems = comps.queryItems ?? []
        let query = Dictionary(uniqueKeysWithValues: queryItems.compactMap { item in
            guard let value = item.value else { return nil }
            return (item.name, value)
        })

        if path == "/speech" {
            let rawText = (query["text"] ?? "").replacingOccurrences(of: "+", with: " ")
            let text = rawText.removingPercentEncoding ?? rawText
            let duration = Double(query["duration"] ?? "")
            let defaultDuration = min(max(Double(text.count) * 0.06, 1.5), 8.0)
            let finalDuration = duration ?? defaultDuration
            DispatchQueue.main.async { [weak self] in
                self?.controller?.showSpeechBubble(text: text, duration: finalDuration)
            }
            return httpResponse(status: 200, body: "OK")
        }

        return httpResponse(status: 404, body: "Not Found")
    }

    private func httpResponse(status: Int, body: String) -> Data {
        let statusLine: String
        switch status {
        case 200: statusLine = "HTTP/1.1 200 OK"
        case 404: statusLine = "HTTP/1.1 404 Not Found"
        default: statusLine = "HTTP/1.1 400 Bad Request"
        }
        let bodyData = body.data(using: .utf8) ?? Data()
        let headers = "\r\nContent-Length: \(bodyData.count)\r\n\r\n"
        let response = statusLine + headers + body
        return response.data(using: .utf8) ?? Data()
    }
}
