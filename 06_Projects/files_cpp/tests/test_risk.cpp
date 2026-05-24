#include <catch2/catch_test_macros.hpp>
#include "risk.hpp"
#include "config.hpp"

using namespace depthos;

TEST_CASE("Risk: allowed_buy_size respects inventory cap", "[risk]") {
    RiskManager rm;
    ContractSpec spec;
    spec.name = "TEST_USDT";
    spec.tick_size = Decimal("0.001");
    spec.lot_size = 1;
    spec.quanto_multiplier = Decimal("1");
    mm_config.contracts["TEST_USDT"] = spec;
    mm_config.max_inventory_contracts = 10;
    mm_config.skew_threshold_contracts = 5;

    REQUIRE(rm.allowed_buy_size("TEST_USDT", 3) == 3);

    rm.state("TEST_USDT").net_position = 8;
    REQUIRE(rm.allowed_buy_size("TEST_USDT", 5) == 2);

    rm.state("TEST_USDT").net_position = 10;
    REQUIRE(rm.allowed_buy_size("TEST_USDT", 5) == 0);
}

TEST_CASE("Risk: daily loss halt triggers global halt", "[risk]") {
    RiskManager rm;
    mm_config.daily_loss_limit_usdt = Decimal("5.00");
    Fill f;
    f.contract = "TEST_USDT";
    f.size = 1;
    f.price = Decimal("1.0");
    f.fee = Decimal("10.0");
    f.ts_ms = epoch_ms();
    rm.on_fill(f);
    REQUIRE(rm.can_quote("TEST_USDT", ContractSpec()) == false);
}

TEST_CASE("Risk: reset_daily clears halt", "[risk]") {
    RiskManager rm;
    mm_config.daily_loss_limit_usdt = Decimal("5.00");
    Fill f;
    f.contract = "TEST_USDT";
    f.size = 1;
    f.price = Decimal("1.0");
    f.fee = Decimal("10.0");
    f.ts_ms = epoch_ms();
    rm.on_fill(f);
    REQUIRE(rm.can_quote("TEST_USDT", ContractSpec()) == false);
    rm.reset_daily();
    REQUIRE(rm.can_quote("TEST_USDT", ContractSpec()) == true);
}
