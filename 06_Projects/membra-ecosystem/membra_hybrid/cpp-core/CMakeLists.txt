cmake_minimum_required(VERSION 3.15)
project(membra_dns_core VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler flags for performance and security
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG -fomit-frame-pointer -funroll-loops")

# OpenSSL for cryptographic operations
find_package(OpenSSL REQUIRED)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${OPENSSL_INCLUDE_DIR}
)

# DNS resolver library
add_library(membra_dns_core SHARED
    dns_resolver.cpp
    dns_resolver.hpp
)

target_link_libraries(membra_dns_core
    ${OPENSSL_LIBRARIES}
    pthread
)

# Set library properties
set_target_properties(membra_dns_core PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
    PUBLIC_HEADER "dns_resolver.hpp"
)

# Performance library with optimizations
add_library(membra_dns_perf STATIC
    dns_resolver.cpp
    dns_resolver.hpp
)

target_link_libraries(membra_dns_perf
    ${OPENSSL_LIBRARIES}
    pthread
)

target_compile_definitions(membra_dns_perf PRIVATE MEMBRA_PERFORMANCE_BUILD)

# FFI library for Rust integration
add_library(membra_dns_ffi SHARED
    dns_resolver.cpp
)

target_link_libraries(membra_dns_ffi
    ${OPENSSL_LIBRARIES}
    pthread
)

set_target_properties(membra_dns_ffi PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
)

# Test executable
enable_testing()
add_executable(dns_resolver_test
    tests/test_dns_resolver.cpp
)

target_link_libraries(dns_resolver_test
    membra_dns_core
    ${OPENSSL_LIBRARIES}
    pthread
)

add_test(NAME dns_resolver_test COMMAND dns_resolver_test)

# Benchmark executable
add_executable(dns_resolver_bench
    tests/benchmark_dns_resolver.cpp
)

target_link_libraries(dns_resolver_bench
    membra_dns_perf
    ${OPENSSL_LIBRARIES}
    pthread
)

# Installation
install(TARGETS membra_dns_core membra_dns_ffi
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    PUBLIC_HEADER DESTINATION include
)

install(FILES dns_resolver.hpp DESTINATION include/membra/dns)

# Packaging
set(CPACK_PACKAGE_NAME "membra-dns-core")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "High-performance DNS resolver for Membra network")
set(CPACK_GENERATOR "DEB;RPM;TGZ")
include(CPack)