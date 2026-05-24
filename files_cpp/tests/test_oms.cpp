#include <catch2/catch_test_macros.hpp>
#include "oms.hpp"
#include "config.hpp"

using namespace depthos;

TEST_CASE("OMS: get_or_create returns state", "[oms]") {
    OMS o;
    auto& s = o.get_or_create("TEST_USDT");
    REQUIRE(s.contract == "TEST_USDT");
    REQUIRE(s.bid_order_id == 0);
    REQUIRE(s.ask_order_id == 0);
}

TEST_CASE("OMS: live_order_count starts at zero", "[oms]") {
    OMS o;
    REQUIRE(o.live_order_count() == 0);
}
