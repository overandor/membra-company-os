#include <catch2/catch_test_macros.hpp>
#include "rest_client.hpp"
#include "config.hpp"

using namespace depthos;

TEST_CASE("RestClient: dry_run prevents order placement", "[rest]") {
    mm_config.dry_run = true;
    RestClient client;
    auto id = client.place_order("TEST_USDT", 1, Decimal("0.05"), "poc", false, "test");
    REQUIRE(id == "-1");
}

TEST_CASE("RestClient: round_to_tick floors correctly", "[rest]") {
    RestClient client;
    Decimal tick("0.001");
    Decimal price("0.0055");
    Decimal rounded = client.round_to_tick(price, tick);
    REQUIRE(rounded == Decimal("0.005"));
}
