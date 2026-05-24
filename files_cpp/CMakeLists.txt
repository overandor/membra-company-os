cmake_minimum_required(VERSION 3.16)
project(DepthOS VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
enable_testing()

find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)
find_package(Boost 1.70 REQUIRED COMPONENTS thread)
find_package(CURL REQUIRED)

include(FetchContent)

FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
)
FetchContent_MakeAvailable(json)

FetchContent_Declare(spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.14.1
)
FetchContent_MakeAvailable(spdlog)

FetchContent_Declare(Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.7.1
)
FetchContent_MakeAvailable(Catch2)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${OPENSSL_INCLUDE_DIR}
    ${CURL_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS}
)

set(SOURCES
    src/main.cpp
    src/config.cpp
    src/auth.cpp
    src/rest_client.cpp
    src/order_book.cpp
    src/risk.cpp
    src/quoting_engine.cpp
    src/ws_manager.cpp
    src/oms.cpp
    src/backtest_engine.cpp
    src/metrics.cpp
    src/OrderBook.cpp
    src/OrderPlacement.cpp
    src/QueueModel.cpp
    src/WebSocketClient.cpp
    src/BookReconciliation.cpp
    src/RiskEngine.cpp
)

add_executable(depthos ${SOURCES})

add_executable(run_backtest run_backtest.cpp src/backtest_engine.cpp src/metrics.cpp src/config.cpp src/risk.cpp src/oms.cpp src/auth.cpp src/order_book.cpp src/quoting_engine.cpp src/ws_manager.cpp src/rest_client.cpp)

# Create shared library for Python FFI
add_library(depthos_core SHARED
    src/OrderBook.cpp
    src/OrderPlacement.cpp
    src/QueueModel.cpp
    src/WebSocketClient.cpp
    src/BookReconciliation.cpp
    src/RiskEngine.cpp
    src/cpp_ffi_interface.cpp
    src/auth.cpp
)

target_link_libraries(depthos
    PRIVATE
    nlohmann_json::nlohmann_json
    spdlog::spdlog_header_only
    OpenSSL::SSL
    OpenSSL::Crypto
    CURL::libcurl
    Boost::thread
    Threads::Threads
)

target_link_libraries(run_backtest
    PRIVATE
    nlohmann_json::nlohmann_json
    spdlog::spdlog_header_only
    OpenSSL::SSL
    OpenSSL::Crypto
    CURL::libcurl
    Boost::thread
    Threads::Threads
)

target_link_libraries(depthos_core
    PRIVATE
    nlohmann_json::nlohmann_json
    spdlog::spdlog_header_only
    OpenSSL::SSL
    OpenSSL::Crypto
    CURL::libcurl
    Boost::thread
    Threads::Threads
)

if(MSVC)
    target_compile_options(depthos PRIVATE /W4)
else()
    target_compile_options(depthos PRIVATE -Wall -Wextra -Wpedantic)
endif()

set(TEST_SOURCES
    tests/test_main.cpp
    tests/test_auth.cpp
    tests/test_config.cpp
    tests/test_decimal.cpp
    tests/test_order_book.cpp
    tests/test_risk.cpp
    tests/test_rest_client.cpp
    tests/test_ws_manager.cpp
    tests/test_oms.cpp
    tests/test_backtest.cpp
    src/config.cpp
    src/auth.cpp
    src/order_book.cpp
    src/risk.cpp
    src/ws_manager.cpp
    src/oms.cpp
    src/backtest_engine.cpp
    src/metrics.cpp
)

add_executable(depthos_tests ${TEST_SOURCES})

target_link_libraries(depthos_tests
    PRIVATE
    nlohmann_json::nlohmann_json
    spdlog::spdlog_header_only
    OpenSSL::SSL
    OpenSSL::Crypto
    CURL::libcurl
    Boost::thread
    Threads::Threads
    Catch2::Catch2WithMain
)

include(CTest)
include(Catch)
catch_discover_tests(depthos_tests)

install(TARGETS depthos DESTINATION bin)
