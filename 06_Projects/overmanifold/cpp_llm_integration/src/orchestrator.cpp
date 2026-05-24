#include "orchestrator.h"
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <cctype>
#include <openssl/sha.h>
#include <iostream>

namespace llm_integration {

// Helper function for SHA256
std::string sha256(const std::string& input) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256_CTX sha256;
    SHA256_Init(&sha256);
    SHA256_Update(&sha256, input.c_str(), input.size());
    SHA256_Final(hash, &sha256);
    
    std::stringstream ss;
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << (int)hash[i];
    }
    return ss.str();
}

// OrchestrationEvent implementation
OrchestrationEvent::OrchestrationEvent(OrchestrationEventType type, const std::string& source,
                                        const std::map<std::string, std::string>& data, const std::string& priority)
    : event_type(type), source(source), data(data), priority(priority),
      timestamp(std::chrono::system_clock::now()), status("pending") {
    event_id = generate_event_id(type, source);
}

std::string OrchestrationEvent::generate_event_id(OrchestrationEventType type, const std::string& source) {
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    std::string input = std::to_string(static_cast<int>(type)) + source + std::to_string(timestamp);
    return sha256(input);
}

// LlmOrchestrator implementation
LlmOrchestrator::LlmOrchestrator(const std::string& openai_api_key)
    : openai_api_key_(openai_api_key) {
    
    sms_system_ = std::make_unique<LlmSmsProcessor>(openai_api_key);
    email_system_ = std::make_unique<LlmCustomEmailSystem>(openai_api_key);
    blockchain_ = std::make_unique<CustomBlockchain>(openai_api_key, "overmanifold-1");
    bridge_ = std::make_unique<CustomMembraBridge>(openai_api_key);
    
    system_status_["sms"] = "operational";
    system_status_["email"] = "operational";
    system_status_["blockchain"] = "operational";
    system_status_["bridge"] = "operational";
    system_status_["orchestrator"] = "operational";
}

void LlmOrchestrator::initialize() {
    blockchain_->initialize();
    bridge_->initialize();
    std::cout << "[Orchestrator] Initialized with all subsystems" << std::endl;
}

OrchestrationResult LlmOrchestrator::orchestrate_event(const OrchestrationEvent& event) {
    // Store event
    {
        std::unique_lock<std::shared_mutex> lock(events_mutex_);
        OrchestrationEvent event_copy = event;
        event_copy.status = "processing";
        events_[event_copy.event_id] = event_copy;
    }
    
    // Create orchestration plan
    OrchestrationPlan plan = create_orchestration_plan(event);
    
    if (plan.recommended_actions.empty()) {
        return OrchestrationResult{
            false,
            event.event_id,
            "no_actions",
            plan,
            {}
        };
    }
    
    // Execute plan
    auto execution_results = execute_orchestration_plan(event, &plan);
    
    // Update event status
    bool all_success = std::all_of(execution_results.begin(), execution_results.end(),
                                    [](const ActionExecutionResult& r) { return r.success; });
    std::string status = all_success ? "completed" : "partial";
    
    {
        std::unique_lock<std::shared_mutex> lock(events_mutex_);
        if (events_.find(event.event_id) != events_.end()) {
            events_[event.event_id].status = status;
            for (const auto& result : execution_results) {
                events_[event.event_id].processed_by.push_back(result.system);
            }
        }
    }
    
    return OrchestrationResult{
        true,
        event.event_id,
        status,
        plan,
        execution_results
    };
}

OrchestrationPlan LlmOrchestrator::create_orchestration_plan(const OrchestrationEvent& event) {
    // Simplified - use fallback plan
    return create_fallback_plan(event);
}

OrchestrationPlan LlmOrchestrator::create_fallback_plan(const OrchestrationEvent& event) {
    std::vector<OrchestrationAction> actions;
    
    if (event.event_type == OrchestrationEventType::USER_ACTION) {
        auto action_it = event.data.find("action");
        if (action_it != event.data.end() && action_it->second == "register") {
            auto phone_it = event.data.find("phone");
            if (phone_it != event.data.end()) {
                actions.push_back(OrchestrationAction{
                    "sms",
                    "send_verification",
                    "high",
                    {{"phone", phone_it->second}},
                    "User registration requires SMS verification"
                });
            }
            
            auto email_it = event.data.find("email");
            if (email_it != event.data.end()) {
                actions.push_back(OrchestrationAction{
                    "email",
                    "send_welcome",
                    "medium",
                    {{"email", email_it->second}},
                    "Welcome email for new user"
                });
            }
        } else if (action_it != event.data.end() && action_it->second == "payment") {
            actions.push_back(OrchestrationAction{
                "blockchain",
                "process_transaction",
                "high",
                event.data,
                "Process payment transaction"
            });
            
            auto phone_it = event.data.find("phone");
            if (phone_it != event.data.end()) {
                actions.push_back(OrchestrationAction{
                    "sms",
                    "send_notification",
                    "medium",
                    {{"phone", phone_it->second}},
                    "Notify user of payment"
                });
            }
        }
    } else if (event.event_type == OrchestrationEventType::TRANSACTION_EVENT) {
        actions.push_back(OrchestrationAction{
            "blockchain",
            "record_transaction",
            "high",
            event.data,
            "Record transaction on blockchain"
        });
        
        auto email_it = event.data.find("email");
        if (email_it != event.data.end()) {
            actions.push_back(OrchestrationAction{
                "email",
                "send_receipt",
                "medium",
                {{"email", email_it->second}},
                "Send transaction receipt"
            });
        }
    }
    
    std::vector<uint32_t> execution_order;
    for (uint32_t i = 1; i <= actions.size(); i++) {
        execution_order.push_back(i);
    }
    
    return OrchestrationPlan{
        actions,
        execution_order,
        0.0,
        60,
        "low",
        false,
        {}
    };
}

std::vector<ActionExecutionResult> LlmOrchestrator::execute_orchestration_plan(
    const OrchestrationEvent& event, const OrchestrationPlan* plan) {
    
    std::vector<ActionExecutionResult> results;
    
    // Sort actions by execution order
    std::vector<std::pair<uint32_t, const OrchestrationAction*>> sorted_actions;
    for (size_t i = 0; i < plan->recommended_actions.size(); i++) {
        sorted_actions.push_back({plan->execution_order[i], &plan->recommended_actions[i]});
    }
    std::sort(sorted_actions.begin(), sorted_actions.end(),
              [](const auto& a, const auto& b) { return a.first < b.first; });
    
    for (const auto& [order, action] : sorted_actions) {
        auto result = execute_system_action(*action);
        std::cout << "[Orchestrator] Executed " << action->system << "." << action->action 
                  << ": " << result.success << std::endl;
        results.push_back(result);
    }
    
    return results;
}

ActionExecutionResult LlmOrchestrator::execute_system_action(const OrchestrationAction& action) {
    if (action.system == "sms") {
        return execute_sms_action(action);
    } else if (action.system == "email") {
        return execute_email_action(action);
    } else if (action.system == "blockchain") {
        return execute_blockchain_action(action);
    } else if (action.system == "bridge") {
        return execute_bridge_action(action);
    } else {
        return ActionExecutionResult{
            action.system,
            action.action,
            false,
            "Unknown system",
            {}
        };
    }
}

ActionExecutionResult LlmOrchestrator::execute_sms_action(const OrchestrationAction& action) {
    if (action.action == "send_verification") {
        auto phone_it = action.parameters.find("phone");
        if (phone_it != action.parameters.end()) {
            try {
                std::string code = sms_system_->generate_verification_code(phone_it->second);
                bool success = sms_system_->send_sms(phone_it->second, "Your verification code is: " + code);
                return ActionExecutionResult{
                    "sms",
                    action.action,
                    success,
                    success ? std::nullopt : std::optional<std::string>("Failed to send SMS"),
                    {{"code", code}, {"phone", phone_it->second}}
                };
            } catch (const std::exception& e) {
                return ActionExecutionResult{
                    "sms",
                    action.action,
                    false,
                    e.what(),
                    {}
                };
            }
        }
    } else if (action.action == "send_notification") {
        auto phone_it = action.parameters.find("phone");
        auto message_it = action.parameters.find("message");
        if (phone_it != action.parameters.end()) {
            std::string message = message_it != action.parameters.end() ? message_it->second : "Transaction completed";
            try {
                bool success = sms_system_->send_sms(phone_it->second, message);
                return ActionExecutionResult{
                    "sms",
                    action.action,
                    success,
                    success ? std::nullopt : std::optional<std::string>("Failed to send SMS"),
                    {{"phone", phone_it->second}}
                };
            } catch (const std::exception& e) {
                return ActionExecutionResult{
                    "sms",
                    action.action,
                    false,
                    e.what(),
                    {}
                };
            }
        }
    }
    
    return ActionExecutionResult{
        "sms",
        action.action,
        false,
        "Unknown SMS action",
        {}
    };
}

ActionExecutionResult LlmOrchestrator::execute_email_action(const OrchestrationAction& action) {
    if (action.action == "send_welcome") {
        auto email_it = action.parameters.find("email");
        if (email_it != action.parameters.end()) {
            try {
                auto result = email_system_->send_custom_email(
                    email_it->second,
                    "Welcome to Overmanifold Protocol",
                    "Welcome to Overmanifold Protocol! Your account has been created successfully.",
                    "<html><body><h1>Welcome!</h1><p>Your account has been created successfully.</p></body></html>",
                    ""
                );
                return ActionExecutionResult{
                    "email",
                    action.action,
                    result.success,
                    result.success ? std::nullopt : std::optional<std::string>(result.error_message),
                    {{"email", email_it->second}}
                };
            } catch (const std::exception& e) {
                return ActionExecutionResult{
                    "email",
                    action.action,
                    false,
                    e.what(),
                    {}
                };
            }
        }
    }
    
    return ActionExecutionResult{
        "email",
        action.action,
        false,
        "Unknown email action",
        {}
    };
}

ActionExecutionResult LlmOrchestrator::execute_blockchain_action(const OrchestrationAction& action) {
    if (action.action == "process_transaction" || action.action == "record_transaction") {
        auto from_it = action.parameters.find("from_address");
        auto to_it = action.parameters.find("to_address");
        auto amount_it = action.parameters.find("amount");
        
        if (from_it != action.parameters.end() && to_it != action.parameters.end() && amount_it != action.parameters.end()) {
            try {
                double amount = std::stod(amount_it->second);
                auto transaction = blockchain_->create_transaction(
                    from_it->second,
                    to_it->second,
                    amount,
                    TransactionType::PAYMENT,
                    ""
                );
                
                std::string tx_id = blockchain_->submit_transaction(transaction);
                auto result = blockchain_->validate_and_execute_transaction(tx_id);
                
                return ActionExecutionResult{
                    "blockchain",
                    action.action,
                    result.success,
                    result.error,
                    {{"tx_id", tx_id}}
                };
            } catch (const std::exception& e) {
                return ActionExecutionResult{
                    "blockchain",
                    action.action,
                    false,
                    e.what(),
                    {}
                };
            }
        }
    }
    
    return ActionExecutionResult{
        "blockchain",
        action.action,
        false,
        "Unknown blockchain action",
        {}
    };
}

ActionExecutionResult LlmOrchestrator::execute_bridge_action(const OrchestrationAction& action) {
    if (action.action == "process_deposit") {
        auto from_chain_it = action.parameters.find("from_chain");
        auto from_address_it = action.parameters.find("from_address");
        auto to_address_it = action.parameters.find("to_address");
        auto amount_it = action.parameters.find("amount");
        
        if (from_chain_it != action.parameters.end() && from_address_it != action.parameters.end() &&
            to_address_it != action.parameters.end() && amount_it != action.parameters.end()) {
            try {
                double amount = std::stod(amount_it->second);
                auto result = bridge_->deposit_to_overmanifold(
                    from_chain_it->second,
                    from_address_it->second,
                    to_address_it->second,
                    amount,
                    "USDC"
                );
                
                return ActionExecutionResult{
                    "bridge",
                    action.action,
                    result.success,
                    std::nullopt,
                    {{"operation_id", result.operation_id}}
                };
            } catch (const std::exception& e) {
                return ActionExecutionResult{
                    "bridge",
                    action.action,
                    false,
                    e.what(),
                    {}
                };
            }
        }
    }
    
    return ActionExecutionResult{
        "bridge",
        action.action,
        false,
        "Unknown bridge action",
        {}
    };
}

SystemStatus LlmOrchestrator::get_system_status() const {
    std::shared_lock<std::shared_mutex> lock(system_status_mutex_);
    
    SystemStatus status;
    status.orchestrator = system_status_.at("orchestrator");
    status.total_events_processed = events_.size();
    
    status.subsystems["sms"]["status"] = system_status_.at("sms");
    status.subsystems["email"]["status"] = system_status_.at("email");
    status.subsystems["blockchain"]["status"] = system_status_.at("blockchain");
    status.subsystems["bridge"]["status"] = system_status_.at("bridge");
    
    return status;
}

std::string LlmOrchestrator::get_system_prompt() const {
    return R"(You are the orchestration system for Overmanifold Protocol.)";
}

} // namespace llm_integration