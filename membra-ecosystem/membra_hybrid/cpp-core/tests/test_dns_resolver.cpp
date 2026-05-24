#include "../dns_resolver.hpp"
#include <cassert>
#include <iostream>
#include <thread>
#include <vector>

using namespace membra::dns;

void test_zone_creation() {
    std::cout << "Testing zone creation..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    
    bool result = resolver.register_zone("did:example:123", "example.com", "owner123");
    assert(result == true);
    
    auto zone = resolver.get_zone("example.com");
    assert(zone != nullptr);
    assert(zone->did == "did:example:123");
    assert(zone->domain == "example.com");
    assert(zone->owner == "owner123");
    
    std::cout << "✓ Zone creation test passed" << std::endl;
}

void test_duplicate_zone() {
    std::cout << "Testing duplicate zone prevention..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    
    resolver.register_zone("did:example:123", "example.com", "owner123");
    bool result = resolver.register_zone("did:example:456", "example.com", "owner456");
    assert(result == false);
    
    std::cout << "✓ Duplicate zone prevention test passed" << std::endl;
}

void test_record_addition() {
    std::cout << "Testing record addition..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    resolver.register_zone("did:example:123", "example.com", "owner123");
    
    DNSRecord record(RecordType::A, "@", "1.2.3.4", 3600);
    bool result = resolver.add_record("example.com", std::move(record));
    assert(result == true);
    
    auto records = resolver.query("example.com", "@");
    assert(records.size() == 1);
    assert(records[0].value == "1.2.3.4");
    
    std::cout << "✓ Record addition test passed" << std::endl;
}

void test_record_update() {
    std::cout << "Testing record update..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    resolver.register_zone("did:example:123", "example.com", "owner123");
    
    DNSRecord record(RecordType::A, "@", "1.2.3.4", 3600);
    resolver.add_record("example.com", std::move(record));
    
    bool result = resolver.update_record("example.com", "@", RecordType::A, "5.6.7.8");
    assert(result == true);
    
    auto records = resolver.query("example.com", "@");
    assert(records[0].value == "5.6.7.8");
    
    std::cout << "✓ Record update test passed" << std::endl;
}

void test_record_deletion() {
    std::cout << "Testing record deletion..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    resolver.register_zone("did:example:123", "example.com", "owner123");
    
    DNSRecord record(RecordType::A, "@", "1.2.3.4", 3600);
    resolver.add_record("example.com", std::move(record));
    
    bool result = resolver.remove_record("example.com", "@", RecordType::A);
    assert(result == true);
    
    auto records = resolver.query("example.com", "@");
    assert(records.empty());
    
    std::cout << "✓ Record deletion test passed" << std::endl;
}

void test_cache_functionality() {
    std::cout << "Testing cache functionality..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    resolver.register_zone("did:example:123", "example.com", "owner123");
    
    DNSRecord record(RecordType::A, "@", "1.2.3.4", 3600);
    resolver.add_record("example.com", std::move(record));
    
    resolver.enable_cache(true);
    resolver.set_cache_ttl(60);
    
    // First query - cache miss
    auto records1 = resolver.query("example.com", "@");
    auto stats1 = resolver.get_statistics();
    assert(stats1.cache_misses == 1);
    
    // Second query - cache hit
    auto records2 = resolver.query("example.com", "@");
    auto stats2 = resolver.get_statistics();
    assert(stats2.cache_hits == 1);
    
    resolver.clear_cache();
    assert(resolver.get_cache_size() == 0);
    
    std::cout << "✓ Cache functionality test passed" << std::endl;
}

void test_thread_safety() {
    std::cout << "Testing thread safety..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    resolver.register_zone("did:example:123", "example.com", "owner123");
    
    const int num_threads = 10;
    const int operations_per_thread = 100;
    std::vector<std::thread> threads;
    
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&resolver, i]() {
            for (int j = 0; j < operations_per_thread; ++j) {
                std::string name = "record" + std::to_string(i) + "_" + std::to_string(j);
                DNSRecord record(RecordType::A, name, "1.2.3." + std::to_string(j % 256), 3600);
                resolver.add_record("example.com", std::move(record));
            }
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    auto stats = resolver.get_statistics();
    assert(stats.total_records == num_threads * operations_per_thread);
    
    std::cout << "✓ Thread safety test passed" << std::endl;
}

void test_performance() {
    std::cout << "Testing performance..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    resolver.enable_cache(true);
    resolver.register_zone("did:example:123", "example.com", "owner123");
    
    // Add many records
    const int num_records = 10000;
    for (int i = 0; i < num_records; ++i) {
        std::string name = "record" + std::to_string(i);
        DNSRecord record(RecordType::A, name, "1.2.3." + std::to_string(i % 256), 3600);
        resolver.add_record("example.com", std::move(record));
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    // Query many times
    const int num_queries = 10000;
    for (int i = 0; i < num_queries; ++i) {
        std::string name = "record" + std::to_string(i % num_records);
        resolver.query("example.com", name);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << "  Queried " << num_queries << " records in " << duration.count() << "ms" << std::endl;
    std::cout << "  Average: " << (duration.count() / num_queries) << "ms per query" << std::endl;
    
    auto stats = resolver.get_statistics();
    std::cout << "  Cache hit rate: " << 
        (static_cast<double>(stats.cache_hits) / stats.total_queries * 100) << "%" << std::endl;
    
    std::cout << "✓ Performance test passed" << std::endl;
}

void test_zone_removal() {
    std::cout << "Testing zone removal..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    resolver.register_zone("did:example:123", "example.com", "owner123");
    
    DNSRecord record(RecordType::A, "@", "1.2.3.4", 3600);
    resolver.add_record("example.com", std::move(record));
    
    bool result = resolver.remove_zone("example.com");
    assert(result == true);
    
    auto zone = resolver.get_zone("example.com");
    assert(zone == nullptr);
    
    auto stats = resolver.get_statistics();
    assert(stats.total_zones == 0);
    assert(stats.total_records == 0);
    
    std::cout << "✓ Zone removal test passed" << std::endl;
}

void test_query_by_type() {
    std::cout << "Testing query by type..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    resolver.register_zone("did:example:123", "example.com", "owner123");
    
    DNSRecord a_record(RecordType::A, "@", "1.2.3.4", 3600);
    DNSRecord txt_record(RecordType::TXT, "@", "test=value", 3600);
    
    resolver.add_record("example.com", std::move(a_record));
    resolver.add_record("example.com", std::move(txt_record));
    
    auto a_records = resolver.query_by_type("example.com", "@", RecordType::A);
    assert(a_records.size() == 1);
    assert(a_records[0].record_type == RecordType::A);
    
    auto txt_records = resolver.query_by_type("example.com", "@", RecordType::TXT);
    assert(txt_records.size() == 1);
    assert(txt_records[0].record_type == RecordType::TXT);
    
    std::cout << "✓ Query by type test passed" << std::endl;
}

void test_statistics() {
    std::cout << "Testing statistics..." << std::endl;
    
    HighPerformanceDNSResolver resolver;
    
    auto initial_stats = resolver.get_statistics();
    assert(initial_stats.total_zones == 0);
    assert(initial_stats.total_records == 0);
    assert(initial_stats.total_queries == 0);
    
    resolver.register_zone("did:example:123", "example.com", "owner123");
    resolver.register_zone("did:example:456", "example2.com", "owner456");
    
    DNSRecord record(RecordType::A, "@", "1.2.3.4", 3600);
    resolver.add_record("example.com", std::move(record));
    
    resolver.query("example.com", "@");
    
    auto stats = resolver.get_statistics();
    assert(stats.total_zones == 2);
    assert(stats.total_records == 1);
    assert(stats.total_queries == 1);
    
    std::cout << "✓ Statistics test passed" << std::endl;
}

int main() {
    std::cout << "=== Membra DNS Resolver Test Suite ===" << std::endl;
    std::cout << std::endl;
    
    try {
        test_zone_creation();
        test_duplicate_zone();
        test_record_addition();
        test_record_update();
        test_record_deletion();
        test_cache_functionality();
        test_thread_safety();
        test_performance();
        test_zone_removal();
        test_query_by_type();
        test_statistics();
        
        std::cout << std::endl;
        std::cout << "=== All tests passed! ===" << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "Test failed with exception: " << e.what() << std::endl;
        return 1;
    }
}