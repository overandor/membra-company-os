#include <catch2/catch_test_macros.hpp>
#include "ws_manager.hpp"

using namespace depthos;

TEST_CASE("WSManager: start/stop does not crash", "[ws]") {
    WSManager mgr;
    mgr.start();
    mgr.stop();
    REQUIRE(true);
}
