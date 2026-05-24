#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <future>
#include "config.hpp"

namespace depthos {

// Forward declarations
struct ContractSpec;

// HTTP response wrapper
struct HttpResponse {
    int status_code;
    std::string body;
    std::string error;
    
    bool is_success() const { return status_code >= 200 && status_code < 300; }
};

// HTTP client for REST API
class RestClient {
public:
    RestClient();
    ~RestClient();
    
    // Core HTTP request with retry logic
    HttpResponse request(
        const std::string& method,
        const std::string& path,
        const std::unordered_map<std::string, std::string>& query = {},
        const std::string& body = "",
        bool signed_request = true
    );
    
    // Bootstrap methods
    std::unordered_map<std::string, ContractSpec> fetch_contract_specs(
        const std::vector<std::string>& contract_names
    );
    
    std::string fetch_account_mode();
    Decimal fetch_balance();
    int fetch_position(const std::string& contract);
    
    // Order management
    std::string place_order(
        const std::string& contract,
        int size,  // positive=buy, negative=sell
        const Decimal& price,
        const std::string& tif = "gtc",  // gtc | ioc | poc
        bool reduce_only = false,
        const std::string& text = "t-mm"
    );
    
    bool cancel_order(int order_id, const std::string& contract);
    int cancel_all_orders(const std::string& contract);
    std::vector<std::unordered_map<std::string, std::string>> list_open_orders(
        const std::string& contract
    );
    
private:
    void* curl_handle_;  // CURL* handle
    
    // Helper to round price to tick size
    Decimal round_to_tick(const Decimal& price, const Decimal& tick);
};

} // namespace depthos
