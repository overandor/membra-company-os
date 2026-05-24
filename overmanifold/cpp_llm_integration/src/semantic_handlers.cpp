#include "semantic_handlers.h"
#include <random>
#include <sstream>
#include <iomanip>
#include <openssl/sha.h>

namespace semantic_transfer {

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

// TransferPayload nonce generation
std::string TransferPayload::generate_nonce() {
    auto now = std::chrono::system_clock::now();
    auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch()).count();
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, UINT64_MAX);
    
    std::string input = std::to_string(timestamp) + std::to_string(dis(gen));
    return sha256(input).substr(0, 16);
}

// Helper function to serialize TransferPayload to JSON
nlohmann::json serializePayload(const TransferPayload& payload) {
    nlohmann::json semantic_value = {
        {"amount", payload.semantic_value.amount},
        {"currency", payload.semantic_value.currency},
        {"semantic_type", static_cast<int>(payload.semantic_value.semantic_type)},
        {"sender", payload.semantic_value.sender},
        {"recipient", payload.semantic_value.recipient},
        {"metadata", payload.semantic_value.metadata},
        {"conditions", payload.semantic_value.conditions}
    };
    
    if (payload.semantic_value.expires_at.has_value()) {
        auto expires_time_t = std::chrono::system_clock::to_time_t(payload.semantic_value.expires_at.value());
        std::stringstream ss;
        ss << std::put_time(std::localtime(&expires_time_t), "%FT%T");
        semantic_value["expires_at"] = ss.str();
    }
    
    return nlohmann::json{
        {"semantic_value", semantic_value},
        {"channel", static_cast<int>(payload.channel)},
        {"channel_address", payload.channel_address},
        {"signature", payload.signature},
        {"nonce", payload.nonce},
        {"network_id", payload.network_id},
        {"gas_limit", payload.gas_limit},
        {"gas_price", payload.gas_price}
    };
}

// SmsHandler implementation
SmsHandler::SmsHandler()
    : sms_pattern_(R"(@(\w+):([\d.]+)\.(\w+):to:([^\s:]+)(?::for:([^\s:]+))?(?::ref:([^\s:]+))?(?::exp:(\d+))?")") {
}

std::optional<TransferPayload> SmsHandler::parse(const std::string& sms_text) const {
    std::smatch matches;
    if (!std::regex_search(sms_text, matches, sms_pattern_)) {
        return std::nullopt;
    }
    
    std::string action = matches[1].str();
    double amount = std::stod(matches[2].str());
    std::string currency = matches[3].str();
    std::string recipient = matches[4].str();
    std::string purpose = matches[5].matched ? matches[5].str() : "";
    std::string reference = matches[6].matched ? matches[6].str() : "";
    std::string expiry_str = matches[7].matched ? matches[7].str() : "";
    
    SemanticValue value(amount, currency, actionToType(action), "unknown", recipient);
    
    if (!purpose.empty()) {
        value.metadata["purpose"] = purpose;
    }
    if (!reference.empty()) {
        value.metadata["reference"] = reference;
    }
    
    if (!expiry_str.empty()) {
        int64_t expiry_sec = std::stoll(expiry_str);
        value.expires_at = std::chrono::system_clock::now() + std::chrono::seconds(expiry_sec);
    }
    
    return TransferPayload(value, TransferChannel::SMS, recipient);
}

std::string SmsHandler::generate(const TransferPayload& payload) const {
    const char* action = typeToAction(payload.semantic_value.semantic_type);
    std::string purpose = payload.semantic_value.metadata.count("purpose") ? 
                          payload.semantic_value.metadata.at("purpose") : "";
    std::string reference = payload.semantic_value.metadata.count("reference") ? 
                            payload.semantic_value.metadata.at("reference") : "";
    
    std::stringstream ss;
    ss << "@" << action << ":" << payload.semantic_value.amount << "." 
       << payload.semantic_value.currency << ":to:" << payload.channel_address;
    
    if (!purpose.empty()) {
        ss << ":for:" << purpose;
    }
    if (!reference.empty()) {
        ss << ":ref:" << reference;
    }
    
    return ss.str();
}

SemanticType SmsHandler::actionToType(const std::string& action) const {
    std::string lower_action = action;
    std::transform(lower_action.begin(), lower_action.end(), lower_action.begin(), ::tolower);
    
    if (lower_action == "pay") return SemanticType::PAYMENT;
    if (lower_action == "request") return SemanticType::REQUEST;
    if (lower_action == "invoice") return SemanticType::INVOICE;
    if (lower_action == "donate") return SemanticType::DONATION;
    if (lower_action == "sub") return SemanticType::SUBSCRIPTION;
    if (lower_action == "reward") return SemanticType::REWARD;
    if (lower_action == "refund") return SemanticType::REFUND;
    if (lower_action == "escrow") return SemanticType::ESCROW;
    if (lower_action == "multisig") return SemanticType::MULTI_SIG;
    if (lower_action == "timelock") return SemanticType::TIME_LOCKED;
    if (lower_action == "conditional") return SemanticType::CONDITIONAL;
    
    return SemanticType::PAYMENT;
}

const char* SmsHandler::typeToAction(SemanticType type) const {
    switch (type) {
        case SemanticType::PAYMENT: return "pay";
        case SemanticType::REQUEST: return "request";
        case SemanticType::INVOICE: return "invoice";
        case SemanticType::DONATION: return "donate";
        case SemanticType::SUBSCRIPTION: return "sub";
        case SemanticType::REWARD: return "reward";
        case SemanticType::REFUND: return "refund";
        case SemanticType::ESCROW: return "escrow";
        case SemanticType::MULTI_SIG: return "multisig";
        case SemanticType::TIME_LOCKED: return "timelock";
        case SemanticType::CONDITIONAL: return "conditional";
    }
    return "pay";
}

// EmailHandler implementation
EmailHandler::EmailHandler()
    : email_pattern_(R"((\w+)://([\d.]+)\.(\w+)/to/([^\s/]+)(?:@([^\s/]+))?(?:/for/([^\s/]+))?(?:/ref/([^\s/]+))?(?:/exp/(\d+))?")") {
}

std::optional<TransferPayload> EmailHandler::parse(const std::string& email_text) const {
    std::smatch matches;
    if (!std::regex_search(email_text, matches, email_pattern_)) {
        return std::nullopt;
    }
    
    std::string action = matches[1].str();
    double amount = std::stod(matches[2].str());
    std::string currency = matches[3].str();
    std::string recipient = matches[4].str();
    std::string domain = matches[5].matched ? matches[5].str() : "";
    std::string purpose = matches[6].matched ? matches[6].str() : "";
    std::string reference = matches[7].matched ? matches[7].str() : "";
    std::string expiry_str = matches[8].matched ? matches[8].str() : "";
    
    SemanticValue value(amount, currency, actionToType(action), "unknown", recipient);
    
    if (!domain.empty()) {
        value.metadata["domain"] = domain;
    }
    if (!purpose.empty()) {
        value.metadata["purpose"] = purpose;
    }
    if (!reference.empty()) {
        value.metadata["reference"] = reference;
    }
    
    if (!expiry_str.empty()) {
        int64_t expiry_sec = std::stoll(expiry_str);
        value.expires_at = std::chrono::system_clock::now() + std::chrono::seconds(expiry_sec);
    }
    
    std::string channel_address = domain.empty() ? recipient : recipient + "@" + domain;
    
    return TransferPayload(value, TransferChannel::EMAIL, channel_address);
}

std::string EmailHandler::generate(const TransferPayload& payload) const {
    const char* action = typeToAction(payload.semantic_value.semantic_type);
    std::string purpose = payload.semantic_value.metadata.count("purpose") ? 
                          payload.semantic_value.metadata.at("purpose") : "";
    std::string reference = payload.semantic_value.metadata.count("reference") ? 
                            payload.semantic_value.metadata.at("reference") : "";
    std::string domain = payload.semantic_value.metadata.count("domain") ? 
                         payload.semantic_value.metadata.at("domain") : "membra.io";
    
    std::stringstream ss;
    ss << action << "://" << payload.semantic_value.amount << "." 
       << payload.semantic_value.currency << "/to/" << payload.channel_address 
       << "@" << domain;
    
    if (!purpose.empty()) {
        ss << "/for/" << purpose;
    }
    if (!reference.empty()) {
        ss << "/ref/" << reference;
    }
    
    return ss.str();
}

SemanticType EmailHandler::actionToType(const std::string& action) const {
    // Same as SMS handler
    std::string lower_action = action;
    std::transform(lower_action.begin(), lower_action.end(), lower_action.begin(), ::tolower);
    
    if (lower_action == "pay") return SemanticType::PAYMENT;
    if (lower_action == "request") return SemanticType::REQUEST;
    if (lower_action == "invoice") return SemanticType::INVOICE;
    if (lower_action == "donate") return SemanticType::DONATION;
    if (lower_action == "sub") return SemanticType::SUBSCRIPTION;
    if (lower_action == "reward") return SemanticType::REWARD;
    if (lower_action == "refund") return SemanticType::REFUND;
    if (lower_action == "escrow") return SemanticType::ESCROW;
    if (lower_action == "multisig") return SemanticType::MULTI_SIG;
    if (lower_action == "timelock") return SemanticType::TIME_LOCKED;
    if (lower_action == "conditional") return SemanticType::CONDITIONAL;
    
    return SemanticType::PAYMENT;
}

const char* EmailHandler::typeToAction(SemanticType type) const {
    // Same as SMS handler
    switch (type) {
        case SemanticType::PAYMENT: return "pay";
        case SemanticType::REQUEST: return "request";
        case SemanticType::INVOICE: return "invoice";
        case SemanticType::DONATION: return "donate";
        case SemanticType::SUBSCRIPTION: return "sub";
        case SemanticType::REWARD: return "reward";
        case SemanticType::REFUND: return "refund";
        case SemanticType::ESCROW: return "escrow";
        case SemanticType::MULTI_SIG: return "multisig";
        case SemanticType::TIME_LOCKED: return "timelock";
        case SemanticType::CONDITIONAL: return "conditional";
    }
    return "pay";
}

// LinkHandler implementation
LinkHandler::LinkHandler()
    : link_pattern_(R"(https?://([^.]+)\.membra\.io/([\d.]+)/(\w+)/to/([^\s/]+)(?:/for/([^\s/]+))?(?:/ref/([^\s/]+))?(?:/exp/(\d+))?")") {
}

std::optional<TransferPayload> LinkHandler::parse(const std::string& link_url) const {
    std::smatch matches;
    if (!std::regex_search(link_url, matches, link_pattern_)) {
        return std::nullopt;
    }
    
    std::string subdomain = matches[1].str();
    double amount = std::stod(matches[2].str());
    std::string currency = matches[3].str();
    std::string recipient = matches[4].str();
    std::string purpose = matches[5].matched ? matches[5].str() : "";
    std::string reference = matches[6].matched ? matches[6].str() : "";
    std::string expiry_str = matches[7].matched ? matches[7].str() : "";
    
    SemanticValue value(amount, currency, SemanticType::PAYMENT, "unknown", recipient);
    value.metadata["subdomain"] = subdomain;
    
    if (!purpose.empty()) {
        value.metadata["purpose"] = purpose;
    }
    if (!reference.empty()) {
        value.metadata["reference"] = reference;
    }
    
    if (!expiry_str.empty()) {
        int64_t expiry_sec = std::stoll(expiry_str);
        value.expires_at = std::chrono::system_clock::now() + std::chrono::seconds(expiry_sec);
    }
    
    return TransferPayload(value, TransferChannel::LINK, link_url);
}

std::string LinkHandler::generate(const TransferPayload& payload) const {
    std::string subdomain = payload.semantic_value.metadata.count("subdomain") ? 
                             payload.semantic_value.metadata.at("subdomain") : "pay";
    std::string purpose = payload.semantic_value.metadata.count("purpose") ? 
                          payload.semantic_value.metadata.at("purpose") : "";
    std::string reference = payload.semantic_value.metadata.count("reference") ? 
                            payload.semantic_value.metadata.at("reference") : "";
    
    std::stringstream ss;
    ss << "https://" << subdomain << ".membra.io/" << payload.semantic_value.amount 
       << "/" << payload.semantic_value.currency << "/to/" << payload.channel_address;
    
    if (!purpose.empty()) {
        ss << "/for/" << purpose;
    }
    if (!reference.empty()) {
        ss << "/ref/" << reference;
    }
    
    return ss.str();
}

// DomainHandler implementation
DomainHandler::DomainHandler()
    : domain_pattern_(R"(([\d.]+)\.(\w+)\.([^.]+)\.membra\.io:([^\s:]+)(?::([^\s:]+))?(?::([^\s:]+))?")") {
}

std::optional<TransferPayload> DomainHandler::parse(const std::string& domain_text) const {
    std::smatch matches;
    if (!std::regex_search(domain_text, matches, domain_pattern_)) {
        return std::nullopt;
    }
    
    double amount = std::stod(matches[1].str());
    std::string currency = matches[2].str();
    std::string action = matches[3].str();
    std::string recipient = matches[4].str();
    std::string purpose = matches[5].matched ? matches[5].str() : "";
    std::string reference = matches[6].matched ? matches[6].str() : "";
    
    SemanticValue value(amount, currency, actionToType(action), "unknown", recipient);
    
    if (!purpose.empty()) {
        value.metadata["purpose"] = purpose;
    }
    if (!reference.empty()) {
        value.metadata["reference"] = reference;
    }
    
    return TransferPayload(value, TransferChannel::DOMAIN, domain_text);
}

std::string DomainHandler::generate(const TransferPayload& payload) const {
    const char* action = typeToAction(payload.semantic_value.semantic_type);
    std::string purpose = payload.semantic_value.metadata.count("purpose") ? 
                          payload.semantic_value.metadata.at("purpose") : "";
    std::string reference = payload.semantic_value.metadata.count("reference") ? 
                            payload.semantic_value.metadata.at("reference") : "";
    
    std::stringstream ss;
    ss << payload.semantic_value.amount << "." << payload.semantic_value.currency 
       << "." << action << ".membra.io:" << payload.channel_address;
    
    if (!purpose.empty()) {
        ss << ":" << purpose;
    }
    if (!reference.empty()) {
        ss << ":" << reference;
    }
    
    return ss.str();
}

SemanticType DomainHandler::actionToType(const std::string& action) const {
    // Same as SMS handler
    std::string lower_action = action;
    std::transform(lower_action.begin(), lower_action.end(), lower_action.begin(), ::tolower);
    
    if (lower_action == "pay") return SemanticType::PAYMENT;
    if (lower_action == "request") return SemanticType::REQUEST;
    if (lower_action == "invoice") return SemanticType::INVOICE;
    if (lower_action == "donate") return SemanticType::DONATION;
    if (lower_action == "sub") return SemanticType::SUBSCRIPTION;
    if (lower_action == "reward") return SemanticType::REWARD;
    if (lower_action == "refund") return SemanticType::REFUND;
    if (lower_action == "escrow") return SemanticType::ESCROW;
    if (lower_action == "multisig") return SemanticType::MULTI_SIG;
    if (lower_action == "timelock") return SemanticType::TIME_LOCKED;
    if (lower_action == "conditional") return SemanticType::CONDITIONAL;
    
    return SemanticType::PAYMENT;
}

const char* DomainHandler::typeToAction(SemanticType type) const {
    // Same as SMS handler
    switch (type) {
        case SemanticType::PAYMENT: return "pay";
        case SemanticType::REQUEST: return "request";
        case SemanticType::INVOICE: return "invoice";
        case SemanticType::DONATION: return "donate";
        case SemanticType::SUBSCRIPTION: return "sub";
        case SemanticType::REWARD: return "reward";
        case SemanticType::REFUND: return "refund";
        case SemanticType::ESCROW: return "escrow";
        case SemanticType::MULTI_SIG: return "multisig";
        case SemanticType::TIME_LOCKED: return "timelock";
        case SemanticType::CONDITIONAL: return "conditional";
    }
    return "pay";
}

// EndpointHandler implementation
EndpointHandler::EndpointHandler() {
}

std::optional<TransferPayload> EndpointHandler::parse(const std::string& endpoint_data) const {
    try {
        nlohmann::json data = nlohmann::json::parse(endpoint_data);
        
        if (!data.contains("amount") || !data.contains("currency") || !data.contains("to")) {
            return std::nullopt;
        }
        
        double amount = data["amount"].get<double>();
        std::string currency = data["currency"].get<std::string>();
        std::string semantic_type_str = data.value("type", "payment").get<std::string>();
        std::string sender = data.value("from", "unknown").get<std::string>();
        std::string recipient = data["to"].get<std::string>();
        std::string endpoint = data.value("endpoint", "/api/v1/transfer").get<std::string>();
        
        SemanticValue value(amount, currency, stringToType(semantic_type_str), sender, recipient);
        
        // Add metadata from other fields
        for (auto& [key, val] : data.items()) {
            if (key != "amount" && key != "currency" && key != "type" && 
                key != "from" && key != "to" && key != "endpoint") {
                if (val.is_string()) {
                    value.metadata[key] = val.get<std::string>();
                }
            }
        }
        
        return TransferPayload(value, TransferChannel::ENDPOINT, endpoint);
    } catch (const std::exception& e) {
        return std::nullopt;
    }
}

std::string EndpointHandler::generate(const TransferPayload& payload) const {
    nlohmann::json endpoint_data = {
        {"amount", payload.semantic_value.amount},
        {"currency", payload.semantic_value.currency},
        {"type", typeToString(payload.semantic_value.semantic_type)},
        {"from", payload.semantic_value.sender},
        {"to", payload.channel_address},
        {"endpoint", payload.channel_address},
        {"nonce", payload.nonce},
        {"network_id", payload.network_id}
    };
    
    // Add metadata
    for (const auto& [key, value] : payload.semantic_value.metadata) {
        endpoint_data[key] = value;
    }
    
    return endpoint_data.dump();
}

SemanticType EndpointHandler::stringToType(const std::string& type_str) const {
    std::string lower_type = type_str;
    std::transform(lower_type.begin(), lower_type.end(), lower_type.begin(), ::tolower);
    
    if (lower_type == "payment") return SemanticType::PAYMENT;
    if (lower_type == "request") return SemanticType::REQUEST;
    if (lower_type == "invoice") return SemanticType::INVOICE;
    if (lower_type == "donation") return SemanticType::DONATION;
    if (lower_type == "subscription") return SemanticType::SUBSCRIPTION;
    if (lower_type == "reward") return SemanticType::REWARD;
    if (lower_type == "refund") return SemanticType::REFUND;
    if (lower_type == "escrow") return SemanticType::ESCROW;
    if (lower_type == "multi_sig") return SemanticType::MULTI_SIG;
    if (lower_type == "time_locked") return SemanticType::TIME_LOCKED;
    if (lower_type == "conditional") return SemanticType::CONDITIONAL;
    
    return SemanticType::PAYMENT;
}

const char* EndpointHandler::typeToString(SemanticType type) const {
    switch (type) {
        case SemanticType::PAYMENT: return "payment";
        case SemanticType::REQUEST: return "request";
        case SemanticType::INVOICE: return "invoice";
        case SemanticType::DONATION: return "donation";
        case SemanticType::SUBSCRIPTION: return "subscription";
        case SemanticType::REWARD: return "reward";
        case SemanticType::REFUND: return "refund";
        case SemanticType::ESCROW: return "escrow";
        case SemanticType::MULTI_SIG: return "multi_sig";
        case SemanticType::TIME_LOCKED: return "time_locked";
        case SemanticType::CONDITIONAL: return "conditional";
    }
    return "payment";
}

// SemanticTransferHandler implementation
SemanticTransferHandler::SemanticTransferHandler() {
    sms_handler_ = std::make_unique<SmsHandler>();
    email_handler_ = std::make_unique<EmailHandler>();
    link_handler_ = std::make_unique<LinkHandler>();
    domain_handler_ = std::make_unique<DomainHandler>();
    endpoint_handler_ = std::make_unique<EndpointHandler>();
}

std::optional<TransferPayload> SemanticTransferHandler::parse(const std::string& input, TransferChannel channel) const {
    switch (channel) {
        case TransferChannel::SMS:
            return sms_handler_->parse(input);
        case TransferChannel::EMAIL:
            return email_handler_->parse(input);
        case TransferChannel::LINK:
            return link_handler_->parse(input);
        case TransferChannel::DOMAIN:
            return domain_handler_->parse(input);
        case TransferChannel::ENDPOINT:
            return endpoint_handler_->parse(input);
    }
}

std::string SemanticTransferHandler::generate(const TransferPayload& payload) const {
    switch (payload.channel) {
        case TransferChannel::SMS:
            return sms_handler_->generate(payload);
        case TransferChannel::EMAIL:
            return email_handler_->generate(payload);
        case TransferChannel::LINK:
            return link_handler_->generate(payload);
        case TransferChannel::DOMAIN:
            return domain_handler_->generate(payload);
        case TransferChannel::ENDPOINT:
            return endpoint_handler_->generate(payload);
    }
}

std::optional<TransferChannel> SemanticTransferHandler::autoDetectChannel(const std::string& input) const {
    if (input.size() > 0 && input[0] == '@' && input.find(':') != std::string::npos) {
        return TransferChannel::SMS;
    } else if (input.find("http://") == 0 || input.find("https://") == 0) {
        if (input.find("membra.io") != std::string::npos) {
            return TransferChannel::LINK;
        } else {
            return TransferChannel::ENDPOINT;
        }
    } else if (input.find("://") != std::string::npos) {
        return TransferChannel::EMAIL;
    } else if (input.find(".membra.io:") != std::string::npos) {
        return TransferChannel::DOMAIN;
    } else if (input.size() > 0 && input[0] == '{') {
        return TransferChannel::ENDPOINT;
    }
    
    return std::nullopt;
}

// ============================================================================
// SMART CONTRACT SYSTEM IMPLEMENTATION
// ============================================================================

// SmartContract implementation
SmartContract::SmartContract(const std::string& addr, ContractType type, const std::string& crtr)
    : address(addr), contract_type(type), creator(crtr), state(ContractState::DEPLOYED),
      code_hash(calculateCodeHash(addr, type)), created_at(std::chrono::system_clock::now()),
      updated_at(std::chrono::system_clock::now()) {
    
    // Initialize storage
    storage["owner"] = crtr;
    storage["balances"] = nlohmann::json::object();
    storage["allowances"] = nlohmann::json::object();
    storage["total_supply"] = 0;
    storage["nonce"] = 0;
}

std::string SmartContract::calculateCodeHash(const std::string& addr, ContractType type) {
    std::string code = addr + std::to_string(static_cast<int>(type));
    return sha256(code);
}

void SmartContract::setState(ContractState new_state) {
    state = new_state;
    updated_at = std::chrono::system_clock::now();
}

ContractResult SmartContract::execute(const ContractCall& call) {
    if (state != ContractState::ACTIVE) {
        return ContractResult{
            false, nlohmann::json::object(), 0, {}, 
            "Contract not active", nlohmann::json::object()
        };
    }
    
    nlohmann::json return_value;
    if (call.function_name == "transfer") {
        return_value = executeTransfer(call.parameters);
    } else if (call.function_name == "balance_of") {
        return_value = executeBalanceOf(call.parameters);
    } else if (call.function_name == "approve") {
        return_value = executeApprove(call.parameters);
    } else if (call.function_name == "process_payment") {
        return_value = executeProcessPayment(call.parameters);
    } else if (call.function_name == "create_escrow") {
        return_value = executeCreateEscrow(call.parameters);
    } else if (call.function_name == "submit_proposal") {
        return_value = executeSubmitProposal(call.parameters);
    } else if (call.function_name == "create_subscription") {
        return_value = executeCreateSubscription(call.parameters);
    } else {
        return_value = nlohmann::json{{"error", "Unknown function"}};
    }
    
    uint64_t gas_used = call.gas_limit;
    std::vector<nlohmann::json> events;
    events.push_back(generateEvent(call.function_name, call.parameters, return_value));
    
    // Update storage
    storage["nonce"] = storage["nonce"].get<int>() + 1;
    updated_at = std::chrono::system_clock::now();
    
    return ContractResult{
        true, return_value, gas_used, events, "", 
        nlohmann::json{{"nonce", storage["nonce"]}}
    };
}

nlohmann::json SmartContract::executeTransfer(const nlohmann::json& params) {
    std::string to = params.value("to", "unknown");
    double amount = params.value("amount", 0.0);
    
    auto& balances = storage["balances"];
    double from_balance = balances.value(creator, 0.0);
    
    if (from_balance < amount) {
        return nlohmann::json{{"error", "Insufficient balance"}};
    }
    
    double to_balance = balances.value(to, 0.0);
    balances[creator] = from_balance - amount;
    balances[to] = to_balance + amount;
    
    return nlohmann::json{
        {"success", true},
        {"from_balance", from_balance - amount},
        {"to_balance", to_balance + amount}
    };
}

nlohmann::json SmartContract::executeBalanceOf(const nlohmann::json& params) {
    std::string account = params.value("account", "unknown");
    auto& balances = storage["balances"];
    double balance = balances.value(account, 0.0);
    return nlohmann::json{{"balance", balance}};
}

nlohmann::json SmartContract::executeApprove(const nlohmann::json& params) {
    std::string spender = params.value("spender", "unknown");
    double amount = params.value("amount", 0.0);
    
    auto& allowances = storage["allowances"];
    if (!allowances.contains(creator)) {
        allowances[creator] = nlohmann::json::object();
    }
    allowances[creator][spender] = amount;
    
    return nlohmann::json{{"success", true}, {"spender", spender}, {"amount", amount}};
}

nlohmann::json SmartContract::executeProcessPayment(const nlohmann::json& params) {
    // Simplified payment processing
    auto payload = params["payload"];
    double amount = payload.value("amount", 0.0);
    
    if (amount <= 0.0) {
        return nlohmann::json{{"error", "Invalid amount"}};
    }
    
    int payment_count = storage.value("payment_count", 0);
    double total_volume = storage.value("total_volume", 0.0);
    
    storage["payment_count"] = payment_count + 1;
    storage["total_volume"] = total_volume + amount;
    
    return nlohmann::json{{"success", true}, {"payment_count", payment_count + 1}};
}

nlohmann::json SmartContract::executeCreateEscrow(const nlohmann::json& params) {
    auto payload = params["payload"];
    auto conditions = params.value("conditions", std::vector<std::string>{});
    
    int escrow_count = storage.value("escrow_count", 0);
    std::string escrow_id = "escrow_" + std::to_string(escrow_count + 1);
    
    auto now = std::chrono::system_clock::now();
    auto now_time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&now_time_t), "%FT%T");
    
    nlohmann::json escrow_data = {
        {"payload", payload},
        {"conditions", conditions},
        {"status", "pending"},
        {"created_at", ss.str()},
        {"released_at", nullptr},
        {"refunded_at", nullptr}
    };
    
    if (!storage.contains("escrows")) {
        storage["escrows"] = nlohmann::json::object();
    }
    storage["escrows"][escrow_id] = escrow_data;
    storage["escrow_count"] = escrow_count + 1;
    
    return nlohmann::json{{"success", true}, {"escrow_id", escrow_id}};
}

nlohmann::json SmartContract::executeSubmitProposal(const nlohmann::json& params) {
    auto payload = params["payload"];
    std::string proposer = params.value("proposer", "unknown");
    
    int proposal_count = storage.value("proposal_count", 0);
    std::string proposal_id = "proposal_" + std::to_string(proposal_count + 1);
    
    auto now = std::chrono::system_clock::now();
    auto now_time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&now_time_t), "%FT%T");
    
    nlohmann::json proposal_data = {
        {"payload", payload},
        {"proposer", proposer},
        {"approvals", nlohmann::json::array()},
        {"executed", false},
        {"created_at", ss.str()}
    };
    
    if (!storage.contains("proposals")) {
        storage["proposals"] = nlohmann::json::object();
    }
    storage["proposals"][proposal_id] = proposal_data;
    storage["proposal_count"] = proposal_count + 1;
    
    return nlohmann::json{{"success", true}, {"proposal_id", proposal_id}};
}

nlohmann::json SmartContract::executeCreateSubscription(const nlohmann::json& params) {
    std::string subscriber = params.value("subscriber", "unknown");
    double amount = params.value("amount", 0.0);
    int interval_days = params.value("interval_days", 30);
    
    int sub_count = storage.value("subscription_count", 0);
    std::string subscription_id = "sub_" + std::to_string(sub_count + 1);
    
    auto next_payment = std::chrono::system_clock::now() + std::chrono::hours(24 * interval_days);
    auto next_payment_time_t = std::chrono::system_clock::to_time_t(next_payment);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&next_payment_time_t), "%FT%T");
    
    auto now = std::chrono::system_clock::now();
    auto now_time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss2;
    ss2 << std::put_time(std::localtime(&now_time_t), "%FT%T");
    
    nlohmann::json subscription_data = {
        {"subscriber", subscriber},
        {"amount", amount},
        {"interval_days", interval_days},
        {"next_payment", ss.str()},
        {"active", true},
        {"created_at", ss2.str()}
    };
    
    if (!storage.contains("subscriptions")) {
        storage["subscriptions"] = nlohmann::json::object();
    }
    storage["subscriptions"][subscription_id] = subscription_data;
    storage["subscription_count"] = sub_count + 1;
    
    return nlohmann::json{{"success", true}, {"subscription_id", subscription_id}};
}

nlohmann::json SmartContract::generateEvent(const std::string& function_name, const nlohmann::json& params, const nlohmann::json& result) {
    auto now = std::chrono::system_clock::now();
    auto now_time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&now_time_t), "%FT%T");
    
    return nlohmann::json{
        {"event_type", "contract_event"},
        {"function_name", function_name},
        {"contract_address", address},
        {"timestamp", ss.str()},
        {"parameters", params},
        {"result", result}
    };
}

// CustomNetwork implementation
CustomNetwork::CustomNetwork(const std::string& net_id)
    : network_id(net_id), block_number(0), transaction_count(0),
      semantic_handler(std::make_unique<SemanticTransferHandler>()) {}

std::string CustomNetwork::deployContract(std::shared_ptr<SmartContract> contract) {
    contract->setState(ContractState::ACTIVE);
    contracts[contract->address] = contract;
    block_number++;
    return contract->address;
}

ContractResult CustomNetwork::executeContract(const ContractCall& call) {
    auto it = contracts.find(call.contract_address);
    if (it == contracts.end()) {
        return ContractResult{
            false, nlohmann::json::object(), 0, {}, 
            "Contract not found", nlohmann::json::object()
        };
    }
    
    auto result = it->second->execute(call);
    if (result.success) {
        transaction_count++;
    }
    return result;
}

ContractResult CustomNetwork::processSemanticTransfer(const TransferPayload& payload) {
    switch (payload.semantic_value.semantic_type) {
        case SemanticType::PAYMENT:
            return processPayment(payload);
        case SemanticType::ESCROW:
            return processEscrow(payload);
        case SemanticType::MULTI_SIG:
            return processMultiSig(payload);
        case SemanticType::SUBSCRIPTION:
            return processSubscription(payload);
        default:
            return processGenericTransfer(payload);
    }
}

ContractResult CustomNetwork::processPayment(const TransferPayload& payload) {
    auto contract = getOrCreatePaymentContract();
    
    ContractCall call{
        contract->address,
        "process_payment",
        nlohmann::json{{"payload", serializePayload(payload)}},
        payload.semantic_value.sender,
        21000,
        0.00001,
        payload.nonce,
        std::chrono::system_clock::now()
    };
    
    return executeContract(call);
}

ContractResult CustomNetwork::processEscrow(const TransferPayload& payload) {
    auto contract = getOrCreateEscrowContract();
    
    ContractCall call{
        contract->address,
        "create_escrow",
        nlohmann::json{
            {"payload", serializePayload(payload)},
            {"conditions", payload.semantic_value.conditions}
        },
        payload.semantic_value.sender,
        21000,
        0.00001,
        payload.nonce,
        std::chrono::system_clock::now()
    };
    
    return executeContract(call);
}

ContractResult CustomNetwork::processMultiSig(const TransferPayload& payload) {
    auto contract = getOrCreateMultiSigContract();
    
    ContractCall call{
        contract->address,
        "submit_proposal",
        nlohmann::json{
            {"payload", serializePayload(payload)},
            {"proposer", payload.semantic_value.sender}
        },
        payload.semantic_value.sender,
        21000,
        0.01,
        payload.nonce,
        std::chrono::system_clock::now()
    };
    
    return executeContract(call);
}

ContractResult CustomNetwork::processSubscription(const TransferPayload& payload) {
    auto contract = getOrCreateSubscriptionContract();
    
    ContractCall call{
        contract->address,
        "create_subscription",
        nlohmann::json{
            {"subscriber", payload.semantic_value.recipient},
            {"amount", payload.semantic_value.amount},
            {"interval_days", 30}
        },
        payload.semantic_value.sender,
        21000,
        0.00001,
        payload.nonce,
        std::chrono::system_clock::now()
    };
    
    return executeContract(call);
}

ContractResult CustomNetwork::processGenericTransfer(const TransferPayload& payload) {
    auto contract = getOrCreateTokenContract();
    
    ContractCall call{
        contract->address,
        "transfer",
        nlohmann::json{
            {"to", payload.semantic_value.recipient},
            {"amount", payload.semantic_value.amount}
        },
        payload.semantic_value.sender,
        21000,
        0.00001,
        payload.nonce,
        std::chrono::system_clock::now()
    };
    
    return executeContract(call);
}

std::shared_ptr<SmartContract> CustomNetwork::getOrCreatePaymentContract() {
    auto it = contracts.find("payment_contract_001");
    if (it != contracts.end()) {
        return it->second;
    }
    
    auto contract = std::make_shared<SmartContract>("payment_contract_001", ContractType::PAYMENT, "network");
    deployContract(contract);
    return contract;
}

std::shared_ptr<SmartContract> CustomNetwork::getOrCreateEscrowContract() {
    auto it = contracts.find("escrow_contract_001");
    if (it != contracts.end()) {
        return it->second;
    }
    
    auto contract = std::make_shared<SmartContract>("escrow_contract_001", ContractType::ESCROW, "network");
    deployContract(contract);
    return contract;
}

std::shared_ptr<SmartContract> CustomNetwork::getOrCreateMultiSigContract() {
    auto it = contracts.find("multisig_contract_001");
    if (it != contracts.end()) {
        return it->second;
    }
    
    auto contract = std::make_shared<SmartContract>("multisig_contract_001", ContractType::MULTI_SIG, "network");
    deployContract(contract);
    return contract;
}

std::shared_ptr<SmartContract> CustomNetwork::getOrCreateSubscriptionContract() {
    auto it = contracts.find("subscription_contract_001");
    if (it != contracts.end()) {
        return it->second;
    }
    
    auto contract = std::make_shared<SmartContract>("subscription_contract_001", ContractType::SUBSCRIPTION, "network");
    deployContract(contract);
    return contract;
}

std::shared_ptr<SmartContract> CustomNetwork::getOrCreateTokenContract() {
    auto it = contracts.find("token_contract_001");
    if (it != contracts.end()) {
        return it->second;
    }
    
    auto contract = std::make_shared<SmartContract>("token_contract_001", ContractType::TOKEN, "network");
    
    // Initialize token contract
    contract->storage["name"] = "Membra Token";
    contract->storage["symbol"] = "MEMBRA";
    contract->storage["decimals"] = 18;
    contract->storage["total_supply"] = 1000000000;
    contract->storage["balances"]["network"] = 1000000000;
    
    deployContract(contract);
    return contract;
}

nlohmann::json CustomNetwork::getNetworkStatus() const {
    nlohmann::json contract_info = nlohmann::json::object();
    for (const auto& [addr, contract] : contracts) {
        contract_info[addr] = {
            {"type", static_cast<int>(contract->contract_type)},
            {"state", static_cast<int>(contract->state)},
            {"creator", contract->creator}
        };
    }
    
    return nlohmann::json{
        {"network_id", network_id},
        {"block_number", block_number},
        {"transaction_count", transaction_count},
        {"contract_count", contracts.size()},
        {"contracts", contract_info}
    };
}

} // namespace semantic_transfer