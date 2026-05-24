#ifndef SMS_PROCESSOR_H
#define SMS_PROCESSOR_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <functional>

namespace llm_integration {

// SMS intent types
enum class SmsIntent {
    PAYMENT,
    BALANCE,
    HELP,
    REGISTER,
    VERIFY,
    UNKNOWN
};

// SMS intent result
struct SmsIntentResult {
    SmsIntent intent;
    double confidence;
    std::map<std::string, std::string> parameters;
    std::string reasoning;
};

// SMS message structure
struct SmsMessage {
    std::string id;
    std::string from_phone;
    std::string to_phone;
    std::string content;
    std::chrono::system_clock::time_point timestamp;
    bool processed;
    std::optional<SmsIntentResult> intent_result;
    
    SmsMessage(const std::string& from, const std::string& to, const std::string& content);
    static std::string generate_message_id(const std::string& from, const std::string& to, const std::string& content);
};

// System health status
struct SystemHealth {
    std::string status;
    uint64_t messages_processed;
    uint64_t active_sessions;
    bool llm_available;
};

// Custom SMS Gateway (No Twilio dependency)
class CustomSmsGateway {
public:
    CustomSmsGateway();
    virtual ~CustomSmsGateway() = default;
    
    // Send SMS using custom delivery methods
    virtual bool send_sms(const std::string& to_phone, const std::string& message);
    
    // Generate verification code
    virtual std::string generate_verification_code(const std::string& phone);
    
    // Verify code
    virtual bool verify_code(const std::string& phone, const std::string& code);
    
private:
    std::map<std::string, std::pair<std::string, std::chrono::system_clock::time_point>> verification_codes_;
    std::string generate_secure_code(const std::string& phone);
};

// LLM SMS processor
class LlmSmsProcessor {
public:
    LlmSmsProcessor(const std::string& openai_api_key = "");
    virtual ~LlmSmsProcessor() = default;
    
    // Process SMS message and extract intent
    virtual SmsIntentResult process_message(SmsMessage& message);
    
    // Send SMS using custom gateway
    virtual bool send_sms(const std::string& to_phone, const std::string& message);
    
    // Generate verification code
    virtual std::string generate_verification_code(const std::string& phone);
    
    // Get system health
    virtual SystemHealth get_system_health() const;
    
    // Set OpenAI API key
    void set_openai_api_key(const std::string& api_key) { openai_api_key_ = api_key; }
    
protected:
    std::string openai_api_key_;
    std::unique_ptr<CustomSmsGateway> sms_gateway_;
    
    // Analyze SMS content using OpenAI LLM
    virtual SmsIntentResult analyze_with_llm(const std::string& content);
    
    // Fallback keyword-based analysis
    virtual SmsIntentResult analyze_fallback(const std::string& content);
    
    // Build analysis prompt
    std::string build_analysis_prompt(const std::string& content) const;
    
    // Get system prompt for LLM
    std::string get_system_prompt() const;
    
    // Parse LLM response
    SmsIntentResult parse_llm_response(const std::string& response) const;
    
    // HTTP client for OpenAI API
    std::string http_post(const std::string& url, const std::string& json_data) const;
};

} // namespace llm_integration

#endif // SMS_PROCESSOR_H