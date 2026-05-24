#include "OrderPlacement.hpp"
#include "auth.hpp"
#include <cmath>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <curl/curl.h>
#include <nlohmann/json.hpp>

namespace depthos {

// CURL callback for writing response data
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

OrderPlacement::OrderPlacement(const std::string& api_key, const std::string& api_secret)
    : api_key_(api_key), api_secret_(api_secret) {
    // Initialize CURL
    curl_global_init(CURL_GLOBAL_ALL);
}

OrderPlacement::~OrderPlacement() {
    // Cleanup CURL
    curl_global_cleanup();
}

OrderResponse OrderPlacement::place_order(const Order& order) {
    OrderResponse response;
    
    // Build request body
    nlohmann::json body_json;
    body_json["contract"] = order.contract;
    body_json["size"] = order.size;
    body_json["price"] = std::to_string(order.price);
    body_json["tif"] = (order.tif == TimeInForce::GTC ? "gtc" : 
                        order.tif == TimeInForce::IOC ? "ioc" : "poc");
    body_json["text"] = order.text;
    body_json["reduce_only"] = order.reduce_only;
    
    std::string body = body_json.dump();
    
    try {
        std::string result = make_request("POST", "/futures/usdt/orders", body);
        
        // Parse JSON response
        nlohmann::json response_json = nlohmann::json::parse(result);
        
        if (response_json.contains("id")) {
            response.success = true;
            response.status = response_json.value("status", "unknown");
            response.order_id = response_json.value("id", 0);
        } else if (response_json.contains("code")) {
            response.success = false;
            response.error = response_json.value("message", "Unknown error");
        } else {
            response.success = false;
            response.error = "Invalid response format";
        }
        
    } catch (const std::exception& e) {
        response.success = false;
        response.error = e.what();
    }
    
    return response;
}

bool OrderPlacement::cancel_order(int64_t order_id, const std::string& contract) {
    std::string path = "/futures/usdt/orders/" + std::to_string(order_id);
    
    try {
        std::string result = make_request("DELETE", path);
        
        // Parse response
        nlohmann::json response_json = nlohmann::json::parse(result);
        std::string status = response_json.value("status", "");
        
        return (status == "cancelled" || status == "closed");
    } catch (const std::exception& e) {
        return false;
    }
}

int OrderPlacement::cancel_all_orders(const std::string& contract) {
    std::string path = "/futures/usdt/orders?contract=" + contract;
    
    try {
        std::string result = make_request("DELETE", path);
        
        // Parse response
        nlohmann::json response_json = nlohmann::json::parse(result);
        
        if (response_json.contains("succeeded")) {
            return response_json["succeeded"].get<int>();
        }
        
        return 0;
    } catch (const std::exception& e) {
        return -1;
    }
}

OrderResponse OrderPlacement::query_order(int64_t order_id, const std::string& contract) {
    OrderResponse response;
    
    std::string path = "/futures/usdt/orders/" + std::to_string(order_id);
    
    try {
        std::string result = make_request("GET", path);
        
        // Parse response
        nlohmann::json response_json = nlohmann::json::parse(result);
        
        response.success = true;
        response.order_id = order_id;
        response.status = response_json.value("status", "unknown");
    } catch (const std::exception& e) {
        response.success = false;
        response.error = e.what();
    }
    
    return response;
}

std::string OrderPlacement::generate_signature(
    const std::string& method,
    const std::string& path,
    const std::string& body,
    int64_t timestamp)
{
    // Use auth module to generate signature
    auto headers = sign_rest(method, path, "", body, api_key_, api_secret_);
    auto it = headers.find("X-SIGN");
    if (it != headers.end()) {
        return it->second;
    }
    return "";
}

std::string OrderPlacement::make_request(
    const std::string& method,
    const std::string& path,
    const std::string& body)
{
    CURL* curl = curl_easy_init();
    if (!curl) {
        throw std::runtime_error("Failed to initialize CURL");
    }
    
    std::string response_string;
    std::string url = "https://api.gateio.ws" + path;
    
    // Set URL
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    
    // Set method
    if (method == "POST") {
        curl_easy_setopt(curl, CURLOPT_POST, 1L);
    } else if (method == "DELETE") {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
    }
    
    // Set body if present
    if (!body.empty() && method != "GET") {
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, body.c_str());
    }
    
    // Set write callback
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);
    
    // Generate headers
    int64_t timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    
    auto headers = sign_rest(method, path, "", body, api_key_, api_secret_);
    
    // Set headers
    struct curl_slist* chunk = NULL;
    chunk = curl_slist_append(chunk, "Content-Type: application/json");
    
    for (const auto& header : headers) {
        std::string header_str = header.first + ": " + header.second;
        chunk = curl_slist_append(chunk, header_str.c_str());
    }
    
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, chunk);
    
    // Perform request
    CURLcode res = curl_easy_perform(curl);
    
    // Cleanup
    curl_slist_free_all(chunk);
    curl_easy_cleanup(curl);
    
    if (res != CURLE_OK) {
        throw std::runtime_error("CURL request failed: " + std::string(curl_easy_strerror(res)));
    }
    
    return response_string;
}

double OrderPlacement::round_to_tick(double price, double tick_size) {
    if (tick_size <= 0.0) return price;
    return std::round(price / tick_size) * tick_size;
}

} // namespace depthos
