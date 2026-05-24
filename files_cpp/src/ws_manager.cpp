#include "ws_manager.hpp"
#include "logger.hpp"
#include <atomic>

namespace depthos {

class WSManager::Impl {
public:
    Impl() : running_(false) {}
    void start() { running_ = true; LOG_WARN("WSManager stub: no live WebSocket"); }
    void stop() { running_ = false; LOG_INFO("WSManager stopped"); }
    void wait() {}
private:
    std::atomic<bool> running_;
};

WSManager::WSManager() : impl_(std::make_unique<Impl>()) {}
WSManager::~WSManager() = default;
void WSManager::start() { impl_->start(); }
void WSManager::stop() { impl_->stop(); }
void WSManager::wait() { impl_->wait(); }

} // namespace depthos
