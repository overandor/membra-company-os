#ifndef ORCHESTRATOR_H
#define ORCHESTRATOR_H

#include "sms_processor.h"
#include "email_system.h"
#include "blockchain.h"
#include "bridge.h"
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <shared_mutex>

namespace llm_integration {

// Orchestration event types
enum class OrchestrationEventType {
    USER_ACTION,
    SYSTEM_EVENT,
    TRANSACTION_EVENT,
    BRIDGE_EVENT,
    ALERT_EVENT,
    COMPLIANCE_EVENT
};

// Orchestration event
struct OrchestrationEvent {
    std::string event_id;
    OrchestrationEventType event_type;
    std::string source;
    std::map<std::string, std::string> data;
    std::chrono::system_clock::time_point timestamp;
    std::string priority;
    std::string status;
    std::vector<std::string> processed_by;
    std::map<std::string, std::string> results;
    
    OrchestrationEvent(OrchestrationEventType type, const std::string& source,
                       const std::map<std::string, std::string>& data, const std::string& priority);
    static std::string generate_event_id(OrchestrationEventType type, const std::string& source);
};

// Orchestration action
struct OrchestrationAction {
    std::string system;
    std::string action;
    std::string priority;
    std::map<std::string, std::string> parameters;
    std::string reasoning;
};

// Orchestration plan
struct OrchestrationPlan {
    std::vector<OrchestrationAction> recommended_actions;
    std::vector<uint32_t> execution_order;
    double total_cost_estimate;
    uint64_t estimated_time_seconds;
    std::string risk_assessment;
    bool requires_manual_approval;
    std::vector<std::string> optimization_suggestions;
};

// Action execution result
struct ActionExecutionResult {
    std::string system;
    std::string action;
    bool success;
    std::optional<std::string> error;
    std::map<std::string, std::string> result;
};

// Orchestration result
struct OrchestrationResult {
    bool success;
    std::string event_id;
    std::string status;
    OrchestrationPlan orchestration_plan;
    std::vector<ActionExecutionResult> execution_results;
};

// System status
struct SystemStatus {
    std::string orchestrator;
    std::map<std::string, std::map<std::string, std::string>> subsystems;
    uint64_t total_events_processed;
};

// LLM orchestrator
class LlmOrchestrator {
public:
    LlmOrchestrator(const std::string& openai_api_key = "");
    
    void initialize();
    OrchestrationResult orchestrate_event(const OrchestrationEvent& event);
    SystemStatus get_system_status() const;
    
    void set_openai_api_key(const std::string& api_key) { openai_api_key_ = api_key; }
    
private:
    std::string openai_api_key_;
    
    std::unique_ptr<LlmSmsProcessor> sms_system_;
    std::unique_ptr<LlmCustomEmailSystem> email_system_;
    std::unique_ptr<CustomBlockchain> blockchain_;
    std::unique_ptr<CustomMembraBridge> bridge_;
    
    mutable std::shared_mutex events_mutex_;
    std::map<std::string, OrchestrationEvent> events_;
    
    mutable std::shared_mutex system_status_mutex_;
    std::map<std::string, std::string> system_status_;
    
    OrchestrationPlan create_orchestration_plan(const OrchestrationEvent& event);
    OrchestrationPlan create_fallback_plan(const OrchestrationEvent& event);
    std::vector<ActionExecutionResult> execute_orchestration_plan(const OrchestrationEvent& event,
                                                                    const OrchestrationPlan& plan);
    ActionExecutionResult execute_system_action(const OrchestrationAction& action);
    ActionExecutionResult execute_sms_action(const OrchestrationAction& action);
    ActionExecutionResult execute_email_action(const OrchestrationAction& action);
    ActionExecutionResult execute_blockchain_action(const OrchestrationAction& action);
    ActionExecutionResult execute_bridge_action(const OrchestrationAction& action);
    std::string get_system_prompt() const;
};

} // namespace llm_integration

#endif // ORCHESTRATOR_H