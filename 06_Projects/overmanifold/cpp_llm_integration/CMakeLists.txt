cmake_minimum_required(VERSION 3.15)
project(CppLlmIntegration VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)

# Include directories
include_directories(${OPENSSL_INCLUDE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/include)

# Source files
set(SOURCES
    src/sms_processor.cpp
    src/email_system.cpp
    src/blockchain.cpp
    src/bridge.cpp
    src/orchestrator.cpp
    src/semantic_handlers.cpp
)

# Header files
set(HEADERS
    include/sms_processor.h
    include/email_system.h
    include/blockchain.h
    include/bridge.h
    include/orchestrator.h
    include/semantic_handlers.h
)

# Create library
add_library(llm_integration STATIC ${SOURCES} ${HEADERS})

# Link libraries
target_link_libraries(llm_integration
    PRIVATE
    OpenSSL::SSL
    OpenSSL::Crypto
    Threads::Threads
)

# Create executable
add_executable(llm_demo src/main.cpp)
target_link_libraries(llm_demo PRIVATE llm_integration)

# Installation
install(TARGETS llm_integration llm_demo
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(FILES ${HEADERS} DESTINATION include/llm_integration)