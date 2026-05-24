#pragma once

#include <string>
#include <unordered_map>
#include <cstdint>

namespace depthos {

// Get current epoch time in milliseconds
int64_t epoch_ms();

// Get current epoch time in seconds
int64_t epoch_s();

// Build Gate.io REST auth headers
// Returns a map of headers to merge into the request
std::unordered_map<std::string, std::string> sign_rest(
    const std::string& method,
    const std::string& path,
    const std::string& query,
    const std::string& body,
    const std::string& api_key,
    const std::string& api_secret
);

// Build Gate.io WS authentication message
// Returns the auth payload as a JSON string
std::string ws_auth_message(
    const std::string& api_key,
    const std::string& api_secret
);

// Build subscription message for WS
std::string sub_msg(
    const std::string& channel,
    const std::string& payload,
    int request_id = 1
);

// Build ping message for WS
std::string ping_msg();

} // namespace depthos
