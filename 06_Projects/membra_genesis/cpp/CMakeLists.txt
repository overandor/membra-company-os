cmake_minimum_required(VERSION 3.16)
project(membra_genesis LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# C++ consensus core shared library (for FFI)
add_library(membra_consensus SHARED
    src/consensus.cpp
)

target_include_directories(membra_consensus PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Optimize for speed
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(membra_consensus PRIVATE -O3 -march=native -DNDEBUG)
endif()

# Genesis node executable
add_executable(genesis_node
    src/main.cpp
)

target_link_libraries(genesis_node PRIVATE membra_consensus)

# Install
install(TARGETS membra_consensus genesis_node
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)
