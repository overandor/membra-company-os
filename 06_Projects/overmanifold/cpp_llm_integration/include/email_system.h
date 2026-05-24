#ifndef EMAIL_SYSTEM_H
#define EMAIL_SYSTEM_H

#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <optional>

namespace llm_integration {

// Email delivery methods
enum class EmailDeliveryMethod {
    SMTP,
    API,
    QUEUE,
    DIRECT
};

// Email message structure
struct EmailMessage {
    std::string id;
    std::string to_email;
    std::string from_email;
    std::string subject;
    std::string body;
    std::string html_body;
    std::string priority;
    std::chrono::system_clock::time_point timestamp;
    EmailDeliveryMethod delivery_method;
    std::string status;
    uint32_t delivery_attempts;
    std::map<std::string, std::string> metadata;
    
    EmailMessage(const std::string& to, const std::string& from, 
                 const std::string& subject, const std::string& body,
                 const std::string& html_body);
    static std::string generate_message_id(const std::string& to, const std::string& from, const std::string& subject);
};

// Email delivery result
struct EmailDeliveryResult {
    bool success;
    std::string message_id;
    EmailDeliveryMethod delivery_method;
    double cost;
    std::string status;
    std::string error_message;
    std::optional<std::chrono::system_clock::time_point> delivery_timestamp;
    std::string server_response;
};

// Email delivery interface
class IEmailDelivery {
public:
    virtual ~IEmailDelivery() = default;
    virtual EmailDeliveryResult send_email(const EmailMessage& message) = 0;
    virtual std::map<std::string, std::string> get_delivery_status(const std::string& message_id) = 0;
};

// SMTP email delivery
class SmtpEmailDelivery : public IEmailDelivery {
public:
    SmtpEmailDelivery(const std::string& smtp_server = "localhost", uint16_t smtp_port = 587,
                      const std::string& smtp_user = "", const std::string& smtp_password = "",
                      bool use_tls = true);
    
    EmailDeliveryResult send_email(const EmailMessage& message) override;
    std::map<std::string, std::string> get_delivery_status(const std::string& message_id) override;
    
private:
    std::string smtp_server_;
    uint16_t smtp_port_;
    std::string smtp_user_;
    std::string smtp_password_;
    bool use_tls_;
};

// Email analysis result
struct EmailAnalysis {
    std::string email_type;
    double confidence;
    std::string urgency;
    std::string priority;
    bool personalization_required;
    std::vector<std::string> compliance_flags;
    std::string recommended_delivery_method;
    std::string reasoning;
    double estimated_cost;
};

// Email statistics
struct EmailStatistics {
    uint64_t total_emails;
    uint64_t successful;
    uint64_t failed;
    double success_rate;
    std::map<std::string, uint64_t> method_distribution;
    double total_cost;
    double average_cost_per_email;
};

// LLM email analyzer
class LlmEmailAnalyzer {
public:
    LlmEmailAnalyzer(const std::string& openai_api_key = "");
    
    EmailAnalysis analyze_email(const std::string& to_email, const std::string& subject,
                                const std::string& body, const std::string& html_body);
    
    void set_openai_api_key(const std::string& api_key) { openai_api_key_ = api_key; }
    
private:
    std::string openai_api_key_;
    
    EmailAnalysis analyze_with_llm(const std::string& to_email, const std::string& subject,
                                   const std::string& body, const std::string& html_body);
    EmailAnalysis analyze_fallback(const std::string& subject, const std::string& body);
    std::string get_system_prompt() const;
    std::string http_post(const std::string& url, const std::string& json_data) const;
};

// LLM custom email system
class LlmCustomEmailSystem {
public:
    LlmCustomEmailSystem(const std::string& openai_api_key = "");
    
    EmailDeliveryResult send_custom_email(const std::string& to_email, const std::string& subject,
                                          const std::string& body, const std::string& html_body,
                                          const std::string& from_email = "");
    
    std::string send_verification_email(const std::string& email);
    
    EmailStatistics get_email_statistics() const;
    
    void set_openai_api_key(const std::string& api_key) { openai_api_key_ = api_key; }
    
private:
    std::string openai_api_key_;
    std::unique_ptr<LlmEmailAnalyzer> analyzer_;
    std::map<EmailDeliveryMethod, std::unique_ptr<IEmailDelivery>> delivery_methods_;
    std::map<std::string, EmailDeliveryResult> delivery_history_;
    
    std::string generate_secure_code(const std::string& email);
};

} // namespace llm_integration

#endif // EMAIL_SYSTEM_H