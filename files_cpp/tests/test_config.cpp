#include <catch2/catch_test_macros.hpp>
#include "config.hpp"

using namespace depthos;

TEST_CASE("Config: dry_run defaults to true", "[config]") {
    MMConfig cfg;
    REQUIRE(cfg.dry_run == true);
}

TEST_CASE("Config: max_inventory is positive", "[config]") {
    MMConfig cfg;
    REQUIRE(cfg.max_inventory_contracts > 0);
}

TEST_CASE("Config: daily_loss_limit is positive", "[config]") {
    MMConfig cfg;
    REQUIRE(cfg.daily_loss_limit_usdt > Decimal("0"));
}
