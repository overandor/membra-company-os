#include "orchestrator.h"
#include <iostream>
#include <map>

int main() {
    std::cout << "C++ LLM Integration System Demo" << std::endl;
    std::cout << "================================" << std::endl;
    
    try {
        // Initialize orchestrator
        llm_integration::LlmOrchestrator orchestrator;
        orchestrator.initialize();
        
        std::cout << "C++ LLM Integration Systems initialized successfully" << std::endl;
        
        // Get system status
        auto status = orchestrator.get_system_status();
        std::cout << "System Status: " << status.orchestrator << std::endl;
        std::cout << "SMS Status: " << status.subsystems.at("sms").at("status") << std::endl;
        std::cout << "Email Status: " << status.subsystems.at("email").at("status") << std::endl;
        std::cout << "Blockchain Status: " << status.subsystems.at("blockchain").at("status") << std::endl;
        std::cout << "Bridge Status: " << status.subsystems.at("bridge").at("status") << std::endl;
        
        // Example: Handle user registration
        std::map<std::string, std::string> registration_data;
        registration_data["action"] = "register";
        registration_data["phone"] = "+1234567890";
        registration_data["email"] = "user@example.com";
        
        llm_integration::OrchestrationEvent registration_event(
            llm_integration::OrchestrationEventType::USER_ACTION,
            "registration",
            registration_data,
            "high"
        );
        
        std::cout << "\nProcessing user registration event..." << std::endl;
        auto result = orchestrator.orchestrate_event(registration_event);
        std::cout << "Registration event processed: " << (result.success ? "success" : "failed") << std::endl;
        
        // Example: Handle payment
        std::map<std::string, std::string> payment_data;
        payment_data["action"] = "payment";
        payment_data["from_address"] = "0x1234567890abcdef1234567890abcdef12345678";
        payment_data["to_address"] = "0x0987654321fedcba0987654321fedcba09876543";
        payment_data["amount"] = "100.0";
        payment_data["phone"] = "+1234567890";
        
        llm_integration::OrchestrationEvent payment_event(
            llm_integration::OrchestrationEventType::TRANSACTION_EVENT,
            "payment",
            payment_data,
            "high"
        );
        
        std::cout << "\nProcessing payment event..." << std::endl;
        result = orchestrator.orchestrate_event(payment_event);
        std::cout << "Payment event processed: " << (result.success ? "success" : "failed") << std::endl;
        
        std::cout << "\nC++ LLM Integration System demo completed successfully" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}