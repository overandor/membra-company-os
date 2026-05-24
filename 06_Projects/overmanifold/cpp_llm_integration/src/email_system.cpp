#include "email_system.h"
#include <sstream>
#include <iomanip>
#include <random>
#include <algorithm>
#include <cctype>
#include <openssl/sha.h>
#include <openssl/rand.h>
#include <iostream>

namespace llm_integration {

// Helper function for SHA256 (same as in sms_processor.cpp)
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

// EmailMessage implementation
EmailMessage::EmailMessage(const std::string& to, const std::string& from,
                           const std::string& subject, const std::string& body,
                           const std::string& html_body)
    : to_email(to), from_email(from), subject(subject), body(body), html_body(html_body),
      timestamp(std::chrono::system_clock::now()), delivery_method(EmailDeliveryMethod::SMTP),
      status("pending"), delivery_attempts(0) {
    id = generate_message_id(to, from, subject);
}

std::string EmailMessage::generate_message_id(const std::string& to, const std::string& from, const std::string& subject) {
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    std::string input = to + from + subject + std::to_string(timestamp);
    return sha256(input);
}

// SmtpEmailDelivery implementation
SmtpEmailDelivery::SmtpEmailDelivery(const std::string& smtp_server, uint16_t smtp_port,
                                     const std::string& smtp_user, const std::string& smtp_password,
                                     bool use_tls)
    : smtp_server_(smtp_server), smtp_port_(smtp_port), smtp_user_(smtp_user),
      smtp_password_(smtp_password), use_tls_(use_tls) {
}

EmailDeliveryResult SmtpEmailDelivery::send_email(const EmailMessage& message) {
    std::cout << "[SMTP Email] Sending email to " << message.to_email << std::endl;
    
    // In production, implement actual SMTP sending
    // For now, simulate success
    return EmailDeliveryResult{
        true,
        message.id,
        EmailDeliveryMethod::SMTP,
        0.0,
        "delivered",
        "",
        std::chrono::system_clock::now(),
        "Message sent successfully"
    };
}

std::map<std::string, std::string> SmtpEmailDelivery::get_delivery_status(const std::string& message_id) {
    std::map<std::string, std::string> status;
    status["message_id"] = message_id;
    status["status"] = "delivered";
    status["method"] = "smtp";
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    status["timestamp"] = std::to_string(timestamp);
    return status;
}

// LlmEmailAnalyzer implementation
LlmEmailAnalyzer::LlmEmailAnalyzer(const std::string& openai_api_key)
    : openai_api_key_(openai_api_key) {
}

EmailAnalysis LlmEmailAnalyzer::analyze_email(const std::string& to_email, const std::string& subject,
                                               const std::string& body, const std::string& html_body) {
    if (!openai_api_key_.empty()) {
        return analyze_with_llm(to_email, subject, body, html_body);
    } else {
        return analyze_fallback(subject, body);
    }
}

EmailAnalysis LlmEmailAnalyzer::analyze_with_llm(const std::string& to_email, const std::string& subject,
                                                  const std::string& body, const std::string& html_body) {
    // Simplified LLM analysis - in production, implement actual API call
    std::cout << "[Email Analyzer] Would analyze with LLM" << std::endl;
    return analyze_fallback(subject, body);
}

EmailAnalysis LlmEmailAnalyzer::analyze_fallback(const std::string& subject, const std::string& body) {
    std::string subject_lower = subject;
    std::transform(subject_lower.begin(), subject_lower.end(), subject_lower.begin(), ::tolower);
    
    std::string email_type;
    double confidence;
    std::string delivery_method;
    
    if (subject_lower.find("verification") != std::string::npos || subject_lower.find("code") != std::string::npos) {
        email_type = "verification";
        confidence = 0.8;
        delivery_method = "smtp";
    } else if (subject_lower.find("payment") != std::string::npos || subject_lower.find("transaction") != std::string::npos) {
        email_type = "transaction";
        confidence = 0.75;
        delivery_method = "smtp";
    } else {
        email_type = "notification";
        confidence = 0.6;
        delivery_method = "smtp";
    }
    
    return EmailAnalysis{
        email_type,
        confidence,
        "normal",
        "medium",
        true,
        {},
        delivery_method,
        "Keyword-based analysis",
        0.0
    };
}

std::string LlmEmailAnalyzer::get_system_prompt() const {
    return R"(You are an intelligent email analysis system for Overmanifold Protocol. Analyze emails and determine optimal processing strategy.)";
}

std::string LlmEmailAnalyzer::http_post(const std::string& url, const std::string& json_data) const {
    std::cout << "[Email Analyzer] Would make HTTP POST to " << url << std::endl;
    return "";
}

// LlmCustomEmailSystem implementation
LlmCustomEmailSystem::LlmCustomEmailSystem(const std::string& openai_api_key)
    : openai_api_key_(openai_api_key),
      analyzer_(std::make_unique<LlmEmailAnalyzer>(openai_api_key)) {
    
    delivery_methods_[EmailDeliveryMethod::SMTP] = std::make_unique<SmtpEmailDelivery>();
}

EmailDeliveryResult LlmCustomEmailSystem::send_custom_email(const std::string& to_email, const std::string& subject,
                                                             const std::string& body, const std::string& html_body,
                                                             const std::string& from_email) {
    std::string from = from_email.empty() ? "noreply@overmanifold.io" : from_email;
    
    EmailMessage message(to_email, from, subject, body, html_body);
    
    auto analysis = analyzer_->analyze_email(to_email, subject, body, html_body);
    
    // Determine delivery method from analysis
    EmailDeliveryMethod method = EmailDeliveryMethod::SMTP;
    if (analysis.recommended_delivery_method == "api") {
        method = EmailDeliveryMethod::API;
    } else if (analysis.recommended_delivery_method == "queue") {
        method = EmailDeliveryMethod::QUEUE;
    } else if (analysis.recommended_delivery_method == "direct") {
        method = EmailDeliveryMethod::DIRECT;
    }
    
    message.delivery_method = method;
    message.priority = analysis.priority;
    
    auto delivery_interface = delivery_methods_[method].get();
    if (!delivery_interface) {
        delivery_interface = delivery_methods_[EmailDeliveryMethod::SMTP].get();
    }
    
    auto result = delivery_interface->send_email(message);
    delivery_history_[message.id] = result;
    
    std::cout << "[Email System] Email sent via " << (int)method << ": " << result.success << std::endl;
    return result;
}

std::string LlmCustomEmailSystem::send_verification_email(const std::string& email) {
    std::string code = generate_secure_code(email);
    
    std::string subject = "Overmanifold Verification Code";
    std::string body = "Your verification code is: " + code + "\n\nThis code will expire in 10 minutes.";
    std::string html_body = "<html><body><h2>Verification Code</h2><p>Your verification code is: <strong>" + 
                           code + "</strong></p><p>This code will expire in 10 minutes.</p></body></html>";
    
    auto result = send_custom_email(email, subject, body, html_body);
    
    if (result.success) {
        std::cout << "[Email System] Verification email sent to " << email << std::endl;
    } else {
        std::cerr << "[Email System] Verification email failed: " << result.error_message << std::endl;
    }
    
    return code;
}

EmailStatistics LlmCustomEmailSystem::get_email_statistics() const {
    uint64_t total_emails = delivery_history_.size();
    uint64_t successful = 0;
    double total_cost = 0.0;
    
    for (const auto& [id, result] : delivery_history_) {
        if (result.success) {
            successful++;
        }
        total_cost += result.cost;
    }
    
    uint64_t failed = total_emails - successful;
    double success_rate = total_emails > 0 ? (double)successful / total_emails : 0.0;
    
    return EmailStatistics{
        total_emails,
        successful,
        failed,
        success_rate,
        {},
        total_cost,
        total_emails > 0 ? total_cost / total_emails : 0.0
    };
}

std::string LlmCustomEmailSystem::generate_secure_code(const std::string& email) {
    unsigned char random_bytes[4];
    if (RAND_bytes(random_bytes, sizeof(random_bytes)) != 1) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 255);
        for (int i = 0; i < 4; i++) {
            random_bytes[i] = static_cast<unsigned char>(dis(gen));
        }
    }
    
    std::stringstream hex_stream;
    for (int i = 0; i < 4; i++) {
        hex_stream << std::hex << std::setw(2) << std::setfill('0') << (int)random_bytes[i];
    }
    
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    
    std::string input = email + hex_stream.str() + std::to_string(timestamp);
    std::string hash = sha256(input);
    
    std::string digits;
    for (char c : hash) {
        if (std::isdigit(c)) {
            digits += c;
        }
    }
    
    while (digits.length() < 6) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 9);
        digits += std::to_string(dis(gen));
    }
    
    return digits.substr(0, 6);
}

} // namespace llm_integration