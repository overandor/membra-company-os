#include <catch2/catch_test_macros.hpp>
#include "config.hpp"

using namespace depthos;

TEST_CASE("Decimal: construction from string", "[decimal]") {
    Decimal d("1.5");
    REQUIRE(d == Decimal("1.5"));
}

TEST_CASE("Decimal: arithmetic", "[decimal]") {
    Decimal a("2.0");
    Decimal b("3.0");
    REQUIRE(a + b == Decimal("5.0"));
    REQUIRE(b - a == Decimal("1.0"));
}

TEST_CASE("Decimal: comparison", "[decimal]") {
    Decimal a("1.0");
    Decimal b("2.0");
    REQUIRE(a < b);
    REQUIRE(b > a);
    REQUIRE(a != b);
}

TEST_CASE("Decimal: hash is usable", "[decimal]") {
    std::unordered_map<Decimal, int> m;
    m[Decimal("1.0")] = 10;
    m[Decimal("2.0")] = 20;
    REQUIRE(m[Decimal("1.0")] == 10);
    REQUIRE(m[Decimal("2.0")] == 20);
}
