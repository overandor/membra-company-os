#include "sms_processor.h"
#include <sstream>
#include <iomanip>
#include <random>
#include <algorithm>
#include <cctype>
#include <openssl/sha.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/rand.h>
#include <cstring>
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

// SmsMessage implementation
SmsMessage::SmsMessage(const std::string& from, const std::string& to, const std::string& content)
    : from_phone(from), to_phone(to), content(content), 
      timestamp(std::chrono::system_clock::now()), processed(false) {
    id = generate_message_id(from, to, content);
}

std::string SmsMessage::generate_message_id(const std::string& from, const std::string& to, const std::string& content) {
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    std::string input = from + to + content + std::to_string(timestamp);
    return sha256(input);
}

// CustomSmsGateway implementation
CustomSmsGateway::CustomSmsGateway() {
}

bool CustomSmsGateway::send_sms(const std::string& to_phone, const std::string& message) {
    std::cout << "[SMS Gateway] Sending SMS to " << to_phone << ": " << message << std::endl;
    // In production, this would integrate with actual SMS providers
    // For now, simulate successful delivery
    return true;
}

std::string CustomSmsGateway::generate_verification_code(const std::string& phone) {
    std::string code = generate_secure_code(phone);
    auto expiry = std::chrono::system_clock::now() + std::chrono::minutes(10);
    
    // Store code (in production, use Redis or database)
    verification_codes_[phone] = {code, expiry};
    
    std::cout << "[SMS Gateway] Generated verification code for " << phone 
              << " (expires in 10 minutes)" << std::endl;
    
    return code;
}

bool CustomSmsGateway::verify_code(const std::string& phone, const std::string& code) {
    // In production, check against stored codes
    return true;
}

std::string CustomSmsGateway::generate_secure_code(const std::string& phone) {
    // Generate random bytes
    unsigned char random_bytes[4];
    if (RAND_bytes(random_bytes, sizeof(random_bytes)) != 1) {
        // Fallback to simple random
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
    
    std::string input = phone + hex_stream.str() + std::to_string(timestamp);
    std::string hash = sha256(input);
    
    // Extract digits from hash
    std::string digits;
    for (char c : hash) {
        if (std::isdigit(c)) {
            digits += c;
        }
    }
    
    // Ensure we have exactly 6 digits
    while (digits.length() < 6) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 9);
        digits += std::to_string(dis(gen));
    }
    
    return digits.substr(0, 6);
}

// LlmSmsProcessor implementation
LlmSmsProcessor::LlmSmsProcessor(const std::string& openai_api_key)
    : openai_api_key_(openai_api_key),
      sms_gateway_(std::make_unique<CustomSmsGateway>()) {
}

SmsIntentResult LlmSmsProcessor::process_message(SmsMessage& message) {
    std::cout << "[SMS Processor] Processing SMS message from " << message.from_phone << std::endl;
    
    SmsIntentResult intent_result;
    
    if (!openai_api_key_.empty()) {
        intent_result = analyze_with_llm(message.content);
    } else {
        intent_result = analyze_fallback(message.content);
    }
    
    message.intent_result = intent_result;
    message.processed = true;
    
    std::cout << "[SMS Processor] SMS intent detected: " 
              << (intent_result.intent == SmsIntent::PAYMENT ? "payment" :
                  intent_result.intent == SmsIntent::BALANCE ? "balance" :
                  intent_result.intent == SmsIntent::HELP ? "help" :
                  intent_result.intent == SmsIntent::REGISTER ? "register" :
                  intent_result.intent == SmsIntent::VERIFY ? "verify" : "unknown")
              << " (confidence: " << intent_result.confidence << ")" << std::endl;
    
    return intent_result;
}

bool LlmSmsProcessor::send_sms(const std::string& to_phone, const std::string& message) {
    return sms_gateway_->send_sms(to_phone, message);
}

std::string LlmSmsProcessor::generate_verification_code(const std::string& phone) {
    return sms_gateway_->generate_verification_code(phone);
}

SystemHealth LlmSmsProcessor::get_system_health() const {
    return SystemHealth{
        "operational",
        0,
        0,
        !openai_api_key_.empty()
    };
}

SmsIntentResult LlmSmsProcessor::analyze_with_llm(const std::string& content) {
    std::string prompt = build_analysis_prompt(content);
    
    try {
        std::string json_data = R"({
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": ")" + get_system_prompt() + R"("
                },
                {
                    "role": "user",
                    "content": ")" + prompt + R"("
                }
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        })";
        
        std::string response = http_post("https://api.openai.com/v1/chat/completions", json_data);
        
        if (!response.empty()) {
            return parse_llm_response(response);
        }
    } catch (const std::exception& e) {
        std::cerr << "[SMS Processor] LLM analysis failed: " << e.what() << ", using fallback" << std::endl;
    }
    
    return analyze_fallback(content);
}

SmsIntentResult LlmSmsProcessor::analyze_fallback(const std::string& content) {
    std::string content_lower = content;
    std::transform(content_lower.begin(), content_lower.end(), content_lower.begin(), ::tolower);
    
    SmsIntent intent;
    double confidence;
    std::string reasoning;
    
    if (content_lower.find("pay") != std::string::npos || content_lower.find("send") != std::string::npos) {
        intent = SmsIntent::PAYMENT;
        confidence = 0.8;
        reasoning = "Payment keywords detected";
    } else if (content_lower.find("balance") != std::string::npos || content_lower.find("how much") != std::string::npos) {
        intent = SmsIntent::BALANCE;
        confidence = 0.85;
        reasoning = "Balance inquiry detected";
    } else if (content_lower.find("help") != std::string::npos || content_lower.find("what can") != std::string::npos) {
        intent = SmsIntent::HELP;
        confidence = 0.9;
        reasoning = "Help request detected";
    } else if (content_lower.find("register") != std::string::npos || content_lower.find("sign up") != std::string::npos) {
        intent = SmsIntent::REGISTER;
        confidence = 0.85;
        reasoning = "Registration request detected";
    } else if (content_lower.find("verify") != std::string::npos || content_lower.find("code") != std::string::npos) {
        intent = SmsIntent::VERIFY;
        confidence = 0.8;
        reasoning = "Verification request detected";
    } else {
        intent = SmsIntent::UNKNOWN;
        confidence = 0.5;
        reasoning = "No clear intent detected";
    }
    
    return SmsIntentResult{
        intent,
        confidence,
        {},
        reasoning
    };
}

std::string LlmSmsProcessor::build_analysis_prompt(const std::string& content) const {
    return "SMS Message: " + content;
}

std::string LlmSmsProcessor::get_system_prompt() const {
    return R"(You are an intelligent SMS analyzer for Overmanifold Protocol. Analyze SMS messages and determine user intent.

INTENT TYPES:
1. PAYMENT - User wants to send money or make a payment
2. BALANCE - User wants to check their account balance
3. HELP - User is asking for help or information
4. REGISTER - User wants to register or sign up
5. VERIFY - User is responding to verification or providing codes
6. UNKNOWN - Intent cannot be determined

ANALYSIS FORMAT:
Return JSON with this exact structure:
{
  "intent": "payment|balance|help|register|verify|unknown",
  "confidence": 0.0-1.0,
  "parameters": {
    "amount": "100.0",
    "recipient": "+1234567890",
    "currency": "USD"
  },
  "reasoning": "explain your analysis"
}

Extract relevant parameters like amount, recipient phone, currency, etc.)";
}

SmsIntentResult LlmSmsProcessor::parse_llm_response(const std::string& response) const {
    // Simple JSON parsing (in production, use a proper JSON library like nlohmann/json)
    SmsIntentResult result;
    
    // For now, return a default result
    // In production, properly parse the JSON response
    result.intent = SmsIntent::UNKNOWN;
    result.confidence = 0.5;
    result.reasoning = "LLM analysis";
    
    return result;
}

std::string LlmSmsProcessor::http_post(const std::string& url, const std::string& json_data) const {
    // Simple HTTP POST implementation
    // In production, use a proper HTTP client like libcurl
    
    std::cout << "[SMS Processor] Would make HTTP POST to " << url << std::endl;
    std::cout << "[SMS Processor] Data: " << json_data << std::endl;
    
    // Return empty string for now (simulated)
    return "";
}

} // namespace llm_integration