#include "rest_client.hpp"
#include "config.hpp"
#include "auth.hpp"
#include "logger.hpp"
#include <curl/curl.h>
#include <nlohmann/json.hpp>
#include <sstream>
#include <iostream>
#include <thread>
#include <cmath>
#include <unordered_set>

using json = nlohmann::json;

namespace depthos {

// Callback for curl to write response data
static size_t write_callback(void* contents, size_t size, size_t nmemb, void* userp) {
    size_t total_size = size * nmemb;
    std::string* response = static_cast<std::string*>(userp);
    response->append(static_cast<char*>(contents), total_size);
    return total_size;
}

RestClient::RestClient() {
    curl_handle_ = curl_easy_init();
    if (!curl_handle_) {
        throw std::runtime_error("Failed to initialize CURL");
    }
}

RestClient::~RestClient() {
    if (curl_handle_) {
        curl_easy_cleanup(curl_handle_);
    }
}

HttpResponse RestClient::request(
    const std::string& method,
    const std::string& path,
    const std::unordered_map<std::string, std::string>& query,
    const std::string& body,
    bool signed_request
) {
    HttpResponse response;
    std::string url = std::string(FUTURES_REST_URL) + path;
    
    // Build query string
    if (!query.empty()) {
        url += "?";
        bool first = true;
        for (const auto& [key, value] : query) {
            if (!first) url += "&";
            url += key + "=" + value;
            first = false;
        }
    }
    
    // Set up CURL
    curl_easy_setopt(curl_handle_, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl_handle_, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl_handle_, CURLOPT_WRITEDATA, &response.body);
    curl_easy_setopt(curl_handle_, CURLOPT_TIMEOUT, 15L);
    
    // Headers
    struct curl_slist* headers = nullptr;
    
    if (signed_request) {
        std::string query_str;
        for (const auto& [key, value] : query) {
            query_str += key + "=" + value + "&";
        }
        if (!query_str.empty()) {
            query_str.pop_back();  // Remove trailing &
        }
        
        auto auth_headers = sign_rest(method, path, query_str, body, API_KEY, API_SECRET);
        for (const auto& [key, value] : auth_headers) {
            std::string header = key + ": " + value;
            headers = curl_slist_append(headers, header.c_str());
        }
    }
    
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "Accept: application/json");
    curl_easy_setopt(curl_handle_, CURLOPT_HTTPHEADER, headers);
    
    // Method
    if (method == "POST") {
        curl_easy_setopt(curl_handle_, CURLOPT_POST, 1L);
        curl_easy_setopt(curl_handle_, CURLOPT_POSTFIELDS, body.c_str());
    } else if (method == "DELETE") {
        curl_easy_setopt(curl_handle_, CURLOPT_CUSTOMREQUEST, "DELETE");
    } else {
        curl_easy_setopt(curl_handle_, CURLOPT_HTTPGET, 1L);
    }
    
    // Perform request
    CURLcode res = curl_easy_perform(curl_handle_);
    
    if (res != CURLE_OK) {
        response.error = curl_easy_strerror(res);
        response.status_code = 0;
    } else {
        curl_easy_getinfo(curl_handle_, CURLINFO_RESPONSE_CODE, &response.status_code);
    }
    
    curl_slist_free_all(headers);
    
    // Retry logic for 429/5xx
    const int max_retries = 5;
    const std::vector<int> retry_codes = {429, 500, 502, 503, 504};
    
    for (int attempt = 1; attempt <= max_retries; attempt++) {
        if (response.is_success()) break;
        
        bool should_retry = false;
        for (int code : retry_codes) {
            if (response.status_code == code) {
                should_retry = true;
                break;
            }
        }
        
        if (!should_retry) break;
        
        double delay = 0.5 * std::pow(2, attempt - 1);
        LOG_WARN("HTTP {} on {} {} - retry {} in {}s", response.status_code, method, path, attempt, delay);
        std::this_thread::sleep_for(std::chrono::milliseconds(static_cast<int>(delay * 1000)));
        
        // Retry the request
        response.body.clear();
        res = curl_easy_perform(curl_handle_);
        
        if (res != CURLE_OK) {
            response.error = curl_easy_strerror(res);
            response.status_code = 0;
        } else {
            curl_easy_getinfo(curl_handle_, CURLINFO_RESPONSE_CODE, &response.status_code);
        }
    }
    
    return response;
}

std::unordered_map<std::string, ContractSpec> RestClient::fetch_contract_specs(
    const std::vector<std::string>& contract_names
) {
    std::unordered_map<std::string, ContractSpec> specs;
    
    HttpResponse response = request("GET", "/futures/" + std::string(SETTLE) + "/contracts");
    
    if (!response.is_success()) {
        LOG_ERROR("Failed to fetch contract specs: {}", response.body);
        return specs;
    }
    
    try {
        json data = json::parse(response.body);
        std::unordered_set<std::string> universe(contract_names.begin(), contract_names.end());
        
        for (const auto& c : data) {
            std::string name = c["name"].get<std::string>();
            if (universe.find(name) == universe.end()) continue;
            
            Decimal tick = Decimal(c["order_price_round"].get<std::string>());
            int lot = c["order_size_min"].get<int>();
            Decimal quanto = Decimal(c["quanto_multiplier"].get<std::string>());
            Decimal last = Decimal(c.value<std::string>("last_price", "0"));
            
            // Verify current last price is within micro-price range
            if (last > Decimal("0.10")) {
                LOG_WARN("{} last_price={} exceeds micro-price ceiling, skipping", name, last.str());
                continue;
            }
            
            ContractSpec spec;
            spec.name = name;
            spec.tick_size = tick;
            spec.lot_size = lot;
            spec.quanto_multiplier = quanto;
            spec.max_price = Decimal("0.10");
            
            specs[name] = spec;
            
            LOG_INFO("Loaded spec {}  tick={}  lot={}  quanto={}  last={}", name, tick.str(), lot, quanto.str(), last.str());
        }
    } catch (const json::exception& e) {
        LOG_ERROR("JSON parse error in fetch_contract_specs: {}", e.what());
    }
    
    return specs;
}

std::string RestClient::fetch_account_mode() {
    HttpResponse response = request("GET", "/futures/" + std::string(SETTLE) + "/accounts");
    
    if (!response.is_success()) {
        LOG_ERROR("Failed to fetch account mode");
        return "single";
    }
    
    try {
        json data = json::parse(response.body);
        std::string mode = data.value<std::string>("mode", "single");
        LOG_INFO("Account mode: {}", mode);
        return mode;
    } catch (const json::exception& e) {
        LOG_ERROR("JSON parse error in fetch_account_mode: {}", e.what());
        return "single";
    }
}

Decimal RestClient::fetch_balance() {
    HttpResponse response = request("GET", "/futures/" + std::string(SETTLE) + "/accounts");
    
    if (!response.is_success()) {
        return Decimal("0");
    }
    
    try {
        json data = json::parse(response.body);
        std::string available = data.value<std::string>("available", "0");
        Decimal balance = Decimal(available);
        LOG_INFO("USDT Futures balance: {}", balance.str());
        return balance;
    } catch (const json::exception& e) {
        LOG_ERROR("JSON parse error in fetch_balance: {}", e.what());
        return Decimal("0");
    }
}

int RestClient::fetch_position(const std::string& contract) {
    std::string path;
    if (mm_config.account_mode == "dual") {
        path = "/futures/" + std::string(SETTLE) + "/dual_positions/" + contract;
    } else {
        path = "/futures/" + std::string(SETTLE) + "/positions/" + contract;
    }
    
    HttpResponse response = request("GET", path);
    
    if (!response.is_success()) {
        return 0;
    }
    
    try {
        json data = json::parse(response.body);
        
        if (mm_config.account_mode == "dual") {
            int long_size = data.value<json>("long", json::object()).value<int>("size", 0);
            int short_size = data.value<json>("short", json::object()).value<int>("size", 0);
            return long_size - short_size;
        } else {
            return data.value<int>("size", 0);
        }
    } catch (const json::exception& e) {
        LOG_ERROR("JSON parse error in fetch_position: {}", e.what());
        return 0;
    }
}

std::string RestClient::place_order(
    const std::string& contract,
    int size,
    const Decimal& price,
    const std::string& tif,
    bool reduce_only,
    const std::string& text
) {
    if (mm_config.dry_run) {
        LOG_DEBUG("[DRY-RUN] place_order contract={} size={} price={} tif={}", contract, size, price.str(), tif);
        return "-1";
    }
    
    std::string path = "/futures/" + std::string(SETTLE) + "/orders";
    ContractSpec spec = mm_config.contracts[contract];
    
    // Round price to tick size
    Decimal rounded_price = round_to_tick(price, spec.tick_size);
    
    // Build JSON body
    json body_json;
    body_json["contract"] = contract;
    body_json["size"] = size;
    body_json["price"] = rounded_price.str();
    body_json["tif"] = tif;
    body_json["text"] = text;
    body_json["reduce_only"] = reduce_only;
    
    if (mm_config.account_mode == "dual" && !reduce_only) {
        body_json["auto_size"] = (size < 0) ? "close_long" : "close_short";
    }
    
    std::string body = body_json.dump();
    
    HttpResponse response = request("POST", path, {}, body);
    
    if (!response.is_success()) {
        LOG_ERROR("Failed to place order: {}", response.body);
        return "";
    }
    
    try {
        json data = json::parse(response.body);
        std::string id = data.value<std::string>("id", "");
        LOG_INFO("Placed order id={} contract={} size={} price={} status={}", id, contract, size, rounded_price.str(), data.value<std::string>("status", ""));
        return id;
    } catch (const json::exception& e) {
        LOG_ERROR("JSON parse error in place_order: {}", e.what());
        return "";
    }
}

bool RestClient::cancel_order(int order_id, const std::string& contract) {
    if (mm_config.dry_run) {
        LOG_DEBUG("[DRY-RUN] cancel_order id={}", order_id);
        return true;
    }
    
    std::string path = "/futures/" + std::string(SETTLE) + "/orders/" + std::to_string(order_id);
    HttpResponse response = request("DELETE", path);
    
    if (!response.is_success()) {
        LOG_ERROR("Failed to cancel order: {}", response.body);
        return false;
    }
    
    try {
        json data = json::parse(response.body);
        std::string id = data.value<std::string>("id", "");
        LOG_INFO("Canceled order id={} contract={} status={}", id, contract, data.value<std::string>("status", ""));
        return true;
    } catch (const json::exception& e) {
        LOG_ERROR("JSON parse error in cancel_order: {}", e.what());
        return false;
    }
}

int RestClient::cancel_all_orders(const std::string& contract) {
    if (mm_config.dry_run) {
        LOG_DEBUG("[DRY-RUN] cancel_all {}", contract);
        return 0;
    }
    
    std::string path = "/futures/" + std::string(SETTLE) + "/orders";
    std::unordered_map<std::string, std::string> query = {
        {"contract", contract},
        {"status", "open"}
    };
    
    HttpResponse response = request("DELETE", path, query);
    
    if (!response.is_success()) {
        return 0;
    }
    
    // Parse JSON to get count
    return 0;  // Placeholder
}

std::vector<std::unordered_map<std::string, std::string>> RestClient::list_open_orders(
    const std::string& contract
) {
    std::string path = "/futures/" + std::string(SETTLE) + "/orders";
    std::unordered_map<std::string, std::string> query = {
        {"contract", contract},
        {"status", "open"},
        {"limit", "100"}
    };
    
    HttpResponse response = request("GET", path, query);
    
    // Parse JSON and return list
    return {};  // Placeholder
}

Decimal RestClient::round_to_tick(const Decimal& price, const Decimal& tick) {
    // Floor price to nearest tick size
    return floor(price / tick) * tick;
}

} // namespace depthos
