#include "auth.hpp"
#include <chrono>
#include <openssl/hmac.h>
#include <openssl/sha.h>
#include <sstream>
#include <iomanip>
#include <cstring>

namespace depthos {

int64_t epoch_ms() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    return std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
}

int64_t epoch_s() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    return std::chrono::duration_cast<std::chrono::seconds>(duration).count();
}

std::string sha512_hex(const std::string& data) {
    unsigned char hash[SHA512_DIGEST_LENGTH];
    SHA512(reinterpret_cast<const unsigned char*>(data.c_str()), data.size(), hash);
    
    std::stringstream ss;
    for (int i = 0; i < SHA512_DIGEST_LENGTH; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(hash[i]);
    }
    return ss.str();
}

std::string hmac_sha512(const std::string& key, const std::string& data) {
    unsigned char* digest;
    digest = HMAC(
        EVP_sha512(),
        key.c_str(), key.size(),
        reinterpret_cast<const unsigned char*>(data.c_str()), data.size(),
        nullptr, nullptr
    );
    
    std::stringstream ss;
    for (int i = 0; i < SHA512_DIGEST_LENGTH; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(digest[i]);
    }
    return ss.str();
}

std::unordered_map<std::string, std::string> sign_rest(
    const std::string& method,
    const std::string& path,
    const std::string& query,
    const std::string& body,
    const std::string& api_key,
    const std::string& api_secret
) {
    std::string ts = std::to_string(epoch_s());
    std::string body_hash = sha512_hex(body);
    
    std::string payload = method + "\n" + path + "\n" + query + "\n" + body_hash + "\n" + ts;
    std::string signature = hmac_sha512(api_secret, payload);
    
    std::unordered_map<std::string, std::string> headers;
    headers["KEY"] = api_key;
    headers["SIGN"] = signature;
    headers["Timestamp"] = ts;
    headers["Content-Type"] = "application/json";
    headers["Accept"] = "application/json";
    
    return headers;
}

std::string ws_auth_message(const std::string& api_key, const std::string& api_secret) {
    std::string ts = std::to_string(epoch_s());
    std::string payload = "api_key=" + api_key + "\nchannel=futures.orders\nevent=subscribe\ntime=" + ts;
    std::string signature = hmac_sha512(api_secret, payload);
    
    // Build JSON message
    std::string msg = R"({"time":)" + ts + R"(,"channel":"futures.login","event":"api","payload":{"api_key":")" + 
                      api_key + R"(","signature":")" + signature + R"(","timestamp":")" + ts + R"("}})";
    
    return msg;
}

std::string sub_msg(const std::string& channel, const std::string& payload, int request_id) {
    std::string ts = std::to_string(epoch_s());
    std::string msg = R"({"time":)" + ts + R"(,"id":)" + std::to_string(request_id) + 
                      R"(,"channel":")" + channel + R"(","event":"subscribe","payload":)" + payload + "}";
    return msg;
}

std::string ping_msg() {
    std::string ts = std::to_string(epoch_s());
    return R"({"time":)" + ts + R"(,"channel":"futures.ping"})";
}

} // namespace depthos
