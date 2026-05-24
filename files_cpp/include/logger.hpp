#pragma once

#include <iostream>
#include <string>
#include <chrono>
#include <iomanip>
#include <sstream>

namespace depthos {

inline std::string log_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    std::tm* tm = std::localtime(&t);
    std::ostringstream oss;
    oss << std::put_time(tm, "%Y-%m-%d %H:%M:%S") << "." << std::setfill('0') << std::setw(3) << ms.count();
    return oss.str();
}

template<typename T>
void log_print_impl(std::ostream& os, T&& val) {
    os << std::forward<T>(val);
}

template<typename T, typename... Rest>
void log_print_impl(std::ostream& os, T&& first, Rest&&... rest) {
    os << std::forward<T>(first) << " ";
    log_print_impl(os, std::forward<Rest>(rest)...);
}

template<typename... Args>
void log_info(Args&&... args) {
    std::cout << "[INFO]  " << log_timestamp() << " ";
    log_print_impl(std::cout, std::forward<Args>(args)...);
    std::cout << std::endl;
}

template<typename... Args>
void log_warn(Args&&... args) {
    std::cout << "[WARN]  " << log_timestamp() << " ";
    log_print_impl(std::cout, std::forward<Args>(args)...);
    std::cout << std::endl;
}

template<typename... Args>
void log_error(Args&&... args) {
    std::cerr << "[ERROR] " << log_timestamp() << " ";
    log_print_impl(std::cerr, std::forward<Args>(args)...);
    std::cerr << std::endl;
}

template<typename... Args>
void log_critical(Args&&... args) {
    std::cerr << "[CRIT]  " << log_timestamp() << " ";
    log_print_impl(std::cerr, std::forward<Args>(args)...);
    std::cerr << std::endl;
}

template<typename... Args>
void log_debug(Args&&... args) {
    std::cout << "[DEBUG] " << log_timestamp() << " ";
    log_print_impl(std::cout, std::forward<Args>(args)...);
    std::cout << std::endl;
}

template<typename... Args>
void log_trace(Args&&... args) {
    std::cout << "[TRACE] " << log_timestamp() << " ";
    log_print_impl(std::cout, std::forward<Args>(args)...);
    std::cout << std::endl;
}

class Logger {
public:
    static void init(const std::string& level = "info") {
        (void)level;
    }
};

#define LOG_TRACE(...) depthos::log_trace(__VA_ARGS__)
#define LOG_DEBUG(...) depthos::log_debug(__VA_ARGS__)
#define LOG_INFO(...)  depthos::log_info(__VA_ARGS__)
#define LOG_WARN(...)  depthos::log_warn(__VA_ARGS__)
#define LOG_ERROR(...) depthos::log_error(__VA_ARGS__)
#define LOG_CRITICAL(...) depthos::log_critical(__VA_ARGS__)

} // namespace depthos
