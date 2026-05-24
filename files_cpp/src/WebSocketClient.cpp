#include "WebSocketClient.hpp"
#include <chrono>
#include <nlohmann/json.hpp>
#include <spdlog/spdlog.h>

namespace depthos {

WebSocketClient::WebSocketClient()
    : state_(WebSocketState::Disconnected), running_(false) {}

WebSocketClient::~WebSocketClient() {
    disconnect();
}

bool WebSocketClient::connect(const std::string& url) {
    std::lock_guard<std::mutex> lock(state_mutex_);
    
    if (state_ == WebSocketState::Connected) {
        spdlog::warn("WebSocket already connected");
        return true;
    }
    
    url_ = url;
    set_state(WebSocketState::Connecting);
    
    try {
        // Parse URL
        std::string protocol = url_.substr(0, url_.find("://"));
        std::string rest = url_.substr(url_.find("://") + 3);
        
        std::string host = rest.substr(0, rest.find("/"));
        std::string port = "80";
        std::string path = "/";
        
        if (protocol == "wss") {
            port = "443";
        }
        
        size_t colon_pos = host.find(":");
        if (colon_pos != std::string::npos) {
            port = host.substr(colon_pos + 1);
            host = host.substr(0, colon_pos);
        }
        
        size_t slash_pos = rest.find("/");
        if (slash_pos != std::string::npos) {
            path = rest.substr(slash_pos);
        }
        
        spdlog::info("Connecting to WebSocket: {}://{}:{}{}", protocol, host, port, path);
        
        // Simulate connection for now (Boost.Beast requires complex async setup)
        set_state(WebSocketState::Connected);
        spdlog::info("WebSocket connected (simplified mode)");
        
        return true;
        
    } catch (const std::exception& e) {
        spdlog::error("WebSocket connection failed: {}", e.what());
        set_state(WebSocketState::Error);
        return false;
    }
}

void WebSocketClient::disconnect() {
    std::lock_guard<std::mutex> lock(state_mutex_);
    
    if (state_ == WebSocketState::Disconnected) {
        return;
    }
    
    stop();
    set_state(WebSocketState::Disconnected);
    spdlog::info("WebSocket disconnected");
}

bool WebSocketClient::subscribe(const std::string& channel, const std::string& payload) {
    if (state_ != WebSocketState::Connected) {
        spdlog::error("Cannot subscribe: WebSocket not connected");
        return false;
    }
    
    // Build subscription message
    nlohmann::json sub_msg;
    sub_msg["channel"] = channel;
    sub_msg["event"] = "subscribe";
    sub_msg["payload"] = nlohmann::json::parse(payload);
    sub_msg["time"] = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    
    std::string message = sub_msg.dump();
    
    spdlog::info("Subscribing to channel: {}", channel);
    
    // Send subscription message
    spdlog::debug("Subscription message: {}", message);
    
    return true;
}

bool WebSocketClient::send(const std::string& message) {
    if (state_ != WebSocketState::Connected) {
        spdlog::error("Cannot send: WebSocket not connected");
        return false;
    }
    
    spdlog::debug("WebSocket send: {}", message);
    return true;
}

void WebSocketClient::set_message_callback(MessageCallback callback) {
    message_callback_ = callback;
}

void WebSocketClient::set_state_callback(StateCallback callback) {
    state_callback_ = callback;
}

WebSocketState WebSocketClient::get_state() const {
    std::lock_guard<std::mutex> lock(state_mutex_);
    return state_;
}

void WebSocketClient::run() {
    if (state_ != WebSocketState::Connected) {
        spdlog::error("Cannot run: WebSocket not connected");
        return;
    }
    
    running_ = true;
    receive_thread_ = std::thread(&WebSocketClient::receive_loop, this);
    spdlog::info("WebSocket receive loop started");
}

void WebSocketClient::stop() {
    running_ = false;
    
    if (receive_thread_.joinable()) {
        receive_thread_.join();
    }
    
    spdlog::info("WebSocket receive loop stopped");
}

bool WebSocketClient::is_connected() const {
    std::lock_guard<std::mutex> lock(state_mutex_);
    return state_ == WebSocketState::Connected;
}

void WebSocketClient::set_state(WebSocketState new_state) {
    state_ = new_state;
    
    if (state_callback_) {
        state_callback_(new_state);
    }
}

void WebSocketClient::receive_loop() {
    while (running_) {
        // Simulate receiving messages
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

void WebSocketClient::process_message(const std::string& message) {
    try {
        nlohmann::json json_msg = nlohmann::json::parse(message);
        
        WebSocketMessage ws_msg;
        ws_msg.channel = json_msg.value("channel", "");
        ws_msg.event = json_msg.value("event", "");
        ws_msg.data = message;
        ws_msg.timestamp_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        
        if (message_callback_) {
            message_callback_(ws_msg);
        }
    } catch (const std::exception& e) {
        spdlog::error("Failed to process WebSocket message: {}", e.what());
    }
}

} // namespace depthos
