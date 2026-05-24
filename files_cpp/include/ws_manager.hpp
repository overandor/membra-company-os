#pragma once

#include <string>
#include <vector>
#include <memory>
#include <thread>
#include <atomic>
#include <functional>

namespace depthos {

// Forward declarations
class RestClient;

// WebSocket manager for Gate.io futures
class WSManager {
public:
    explicit WSManager();
    ~WSManager();
    
    void start();
    void stop();
    void wait();
    
    // Callbacks for events
    std::function<void(const std::string&, const std::unordered_map<std::string, std::string>&)> on_book_ticker;
    std::function<void(const std::unordered_map<std::string, std::string>&)> on_order_update;
    std::function<void(const std::unordered_map<std::string, std::string>&)> on_user_trade;
    
private:
    class Impl;
    std::unique_ptr<Impl> impl_;
};

// Public WebSocket for book_ticker
class PublicWS {
public:
    PublicWS();
    ~PublicWS();
    
    void run();
    void stop();
    
private:
    class Impl;
    std::unique_ptr<Impl> impl_;
};

// Private WebSocket for authenticated channels
class PrivateWS {
public:
    PrivateWS();
    ~PrivateWS();
    
    void run();
    void stop();
    
private:
    class Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace depthos
