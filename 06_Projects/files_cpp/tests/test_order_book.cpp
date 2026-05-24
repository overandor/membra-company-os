#include <catch2/catch_test_macros.hpp>
#include "order_book.hpp"

using namespace depthos;

TEST_CASE("OrderBook: initial BBO is null", "[order_book]") {
    OrderBook ob("TEST_USDT");
    auto bbo = ob.bbo();
    REQUIRE(bbo == nullptr);
}

TEST_CASE("OrderBook: on_book_ticker updates BBO", "[order_book]") {
    OrderBook ob("TEST_USDT");
    std::unordered_map<std::string, std::string> data;
    data["b"] = "0.05";
    data["B"] = "100";
    data["a"] = "0.06";
    data["A"] = "200";
    auto changed = ob.on_book_ticker(data);
    REQUIRE(changed != nullptr);
    REQUIRE(changed->bid_price == Decimal("0.05"));
    REQUIRE(changed->ask_price == Decimal("0.06"));
}

TEST_CASE("OrderBook: BBO valid when bid < ask", "[order_book]") {
    OrderBook ob("TEST_USDT");
    std::unordered_map<std::string, std::string> data;
    data["b"] = "0.05";
    data["B"] = "100";
    data["a"] = "0.06";
    data["A"] = "200";
    ob.on_book_ticker(data);
    auto bbo = ob.bbo();
    REQUIRE(bbo->valid());
    REQUIRE(bbo->mid() == Decimal("0.055"));
}
