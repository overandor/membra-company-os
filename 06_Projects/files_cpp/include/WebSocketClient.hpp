#pragma once

#include <string>
#include <functional>
#include <memory>
#include <thread>
#include <mutex>
#include <queue>

namespace depthos {

enum class WebSocketState {
    Disconnected,
    Connecting,
    Connected,
    Error
};

struct WebSocketMessage {
    std::string channel;
    std::string event;
    std::string data;
    int64_t timestamp_ms;
    
    WebSocketMessage() : timestamp_ms(0) {}
};

// Callback type for messages
using MessageCallback = std::function<void(const WebSocketMessage&)>;

// Callback type for state changes
using StateCallback = std::function<void(WebSocketState)>;

class WebSocketClient {
public:
    WebSocketClient();
    ~WebSocketClient();
    
    // Connect to WebSocket server
    bool connect(const std::string& url);
    
    // Disconnect from server
    void disconnect();
    
    // Subscribe to a channel
    bool subscribe(const std::string& channel, const std::string& payload);
    
    // Send a message
    bool send(const std::string& message);
    
    // Set message callback
    void set_message_callback(MessageCallback callback);
    
    // Set state callback
    void set_state_callback(StateCallback callback);
    
    // Get current state
    WebSocketState get_state() const;
    
    // Start receiving messages (blocking)
    void run();
    
    // Stop receiving
    void stop();
    
    // Check if connected
    bool is_connected() const;
    
private:
    std::string url_;
    WebSocketState state_;
    MessageCallback message_callback_;
    StateCallback state_callback_;
    
    std::thread receive_thread_;
    mutable std::mutex state_mutex_;
    std::mutex queue_mutex_;
    std::queue<WebSocketMessage> message_queue_;
    bool running_;
    
    void set_state(WebSocketState new_state);
    void receive_loop();
    void process_message(const std::string& message);
};

} // namespace depthos
