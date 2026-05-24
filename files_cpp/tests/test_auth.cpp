#include <catch2/catch_test_macros.hpp>
#include "auth.hpp"

using namespace depthos;

TEST_CASE("Auth: epoch_ms increases over time", "[auth]") {
    auto t1 = epoch_ms();
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    auto t2 = epoch_ms();
    REQUIRE(t2 > t1);
}

TEST_CASE("Auth: sha512_hex is deterministic", "[auth]") {
    auto h1 = sha512_hex("hello");
    auto h2 = sha512_hex("hello");
    REQUIRE(h1 == h2);
    REQUIRE(h1.length() == 128);
}

TEST_CASE("Auth: hmac_sha512 is deterministic", "[auth]") {
    auto sig1 = hmac_sha512("secret", "payload");
    auto sig2 = hmac_sha512("secret", "payload");
    REQUIRE(sig1 == sig2);
    REQUIRE(sig1.length() == 128);
}

TEST_CASE("Auth: sign_rest produces required headers", "[auth]") {
    auto headers = sign_rest("GET", "/test", "", "", "key123", "secret456");
    REQUIRE(headers.count("KEY") == 1);
    REQUIRE(headers.count("SIGN") == 1);
    REQUIRE(headers.count("Timestamp") == 1);
    REQUIRE(headers["KEY"] == "key123");
}

TEST_CASE("Auth: ws_auth_message contains api_key", "[auth]") {
    auto msg = ws_auth_message("key123", "secret456");
    REQUIRE(msg.find("key123") != std::string::npos);
}
