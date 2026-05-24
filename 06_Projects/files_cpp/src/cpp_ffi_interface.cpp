/**
 * C FFI Interface for Python bindings
 * 
 * Exports C++ functions as C-compatible functions for ctypes
 */

#include "OrderPlacement.hpp"
#include "QueueModel.hpp"
#include "RiskEngine.hpp"
#include "BookReconciliation.hpp"
#include <cstring>
#include <cstdlib>

extern "C" {

// Order Placement FFI
struct C_OrderPlacement {
    const char* contract;
    int64_t size;
    double price;
    int tif;  // 0=GTC, 1=IOC, 2=POC
    bool reduce_only;
    const char* text;
};

struct C_OrderResponse {
    int64_t order_id;
    char status[64];
    char error[256];
    bool success;
};

struct C_FillProbabilityFactors {
    int queue_ahead;
    int queue_behind;
    double trade_intensity;
    double cancel_rate;
    double toxicity_score;
    double latency_ms;
};

struct C_PositionLimits {
    int64_t max_position;
    int64_t max_order_size;
    double max_exposure_usdt;
};

// Global instances
static depthos::OrderPlacement* g_order_placement = nullptr;
static depthos::QueueModel* g_queue_model = nullptr;
static depthos::RiskEngine* g_risk_engine = nullptr;
static depthos::BookReconciliation* g_book_reconciliation = nullptr;

// Initialize functions
void init_order_placement(const char* api_key, const char* api_secret) {
    if (!g_order_placement) {
        g_order_placement = new depthos::OrderPlacement(api_key, api_secret);
    }
}

void init_queue_model() {
    if (!g_queue_model) {
        g_queue_model = new depthos::QueueModel();
    }
}

void init_risk_engine() {
    if (!g_risk_engine) {
        g_risk_engine = new depthos::RiskEngine();
    }
}

void init_book_reconciliation() {
    if (!g_book_reconciliation) {
        g_book_reconciliation = new depthos::BookReconciliation();
    }
}

// Order placement functions
C_OrderResponse place_order(
    const char* contract,
    int64_t size,
    double price,
    int tif,
    bool reduce_only,
    const char* text)
{
    C_OrderResponse response{};
    response.order_id = 0;
    response.success = false;
    
    if (!g_order_placement) {
        std::strncpy(response.error, "OrderPlacement not initialized", 255);
        return response;
    }
    
    depthos::Order order;
    order.contract = contract;
    order.size = size;
    order.price = price;
    order.tif = static_cast<depthos::TimeInForce>(tif);
    order.reduce_only = reduce_only;
    order.text = text;
    
    depthos::OrderResponse cpp_response = g_order_placement->place_order(order);
    
    response.order_id = cpp_response.order_id;
    response.success = cpp_response.success;
    std::strncpy(response.status, cpp_response.status.c_str(), 63);
    std::strncpy(response.error, cpp_response.error.c_str(), 255);
    
    return response;
}

bool cancel_order(int64_t order_id, const char* contract) {
    if (!g_order_placement) {
        return false;
    }
    
    return g_order_placement->cancel_order(order_id, contract);
}

// Queue model functions
double calculate_fill_probability(const C_FillProbabilityFactors* factors) {
    if (!g_queue_model) {
        return 0.0;
    }
    
    depthos::FillProbabilityFactors cpp_factors;
    cpp_factors.queue_ahead = factors->queue_ahead;
    cpp_factors.queue_behind = factors->queue_behind;
    cpp_factors.trade_intensity = factors->trade_intensity;
    cpp_factors.cancel_rate = factors->cancel_rate;
    cpp_factors.toxicity_score = factors->toxicity_score;
    cpp_factors.latency_ms = factors->latency_ms;
    
    return g_queue_model->calculate_fill_probability(cpp_factors);
}

// Risk engine functions
void set_position_limits(const char* contract, const C_PositionLimits* limits) {
    if (!g_risk_engine) {
        return;
    }
    
    depthos::PositionLimits cpp_limits;
    cpp_limits.max_position = limits->max_position;
    cpp_limits.max_order_size = limits->max_order_size;
    cpp_limits.max_exposure_usdt = limits->max_exposure_usdt;
    
    g_risk_engine->set_position_limits(contract, cpp_limits);
}

int check_order_risk(const char* contract, int64_t size, double price) {
    if (!g_risk_engine) {
        return 1;  // Fail
    }
    
    depthos::RiskCheckResult result = g_risk_engine->check_order(contract, size, price);
    
    return static_cast<int>(result);
}

void set_kill_switch(bool enabled) {
    if (g_risk_engine) {
        g_risk_engine->set_kill_switch(enabled);
    }
}

double get_total_exposure() {
    if (!g_risk_engine) {
        return 0.0;
    }
    
    return g_risk_engine->get_total_exposure();
}

// Cleanup functions
void cleanup() {
    delete g_order_placement;
    delete g_queue_model;
    delete g_risk_engine;
    delete g_book_reconciliation;
    
    g_order_placement = nullptr;
    g_queue_model = nullptr;
    g_risk_engine = nullptr;
    g_book_reconciliation = nullptr;
}

} // extern "C"
