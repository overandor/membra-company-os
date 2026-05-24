#ifndef MEMBRA_DNS_RESOLVER_HPP
#define MEMBRA_DNS_RESOLVER_HPP

#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <atomic>
#include <chrono>
#include <cstdint>

namespace membra {
namespace dns {

// DNS record types
enum class RecordType : uint8_t {
    A = 1,
    AAAA = 28,
    CNAME = 5,
    TXT = 16,
    MX = 15,
    SRV = 33
};

// DNS record structure
struct DNSRecord {
    RecordType type;
    std::string name;
    std::string value;
    uint32_t ttl;
    uint64_t created_at;
    uint64_t updated_at;
    
    DNSRecord(RecordType t, std::string n, std::string v, uint32_t ttl_val)
        : type(t), name(std::move(n)), value(std::move(v)), ttl(ttl_val) {
        auto now = std::chrono::system_clock::now();
        created_at = updated_at = std::chrono::duration_cast<std::chrono::seconds>(
            now.time_since_epoch()).count();
    }
};

// DNS zone structure
struct DNSZone {
    std::string did;
    std::string domain;
    std::string owner;
    std::unordered_map<std::string, std::vector<DNSRecord>> records;
    uint64_t created_at;
    uint64_t updated_at;
    std::string zone_hash;
    
    DNSZone(std::string d, std::string dom, std::string own)
        : did(std::move(d)), domain(std::move(dom)), owner(std::move(own)) {
        auto now = std::chrono::system_clock::now();
        created_at = updated_at = std::chrono::duration_cast<std::chrono::seconds>(
            now.time_since_epoch()).count();
        zone_hash = generate_zone_hash();
    }
    
private:
    std::string generate_zone_hash() const;
};

// High-performance DNS resolver
class HighPerformanceDNSResolver {
public:
    HighPerformanceDNSResolver();
    ~HighPerformanceDNSResolver();
    
    // Zone management
    bool register_zone(const std::string& did, const std::string& domain, const std::string& owner);
    bool remove_zone(const std::string& domain);
    std::shared_ptr<DNSZone> get_zone(const std::string& domain) const;
    std::vector<std::shared_ptr<DNSZone>> list_zones() const;
    
    // Record management
    bool add_record(const std::string& domain, DNSRecord record);
    bool remove_record(const std::string& domain, const std::string& name, RecordType type);
    bool update_record(const std::string& domain, const std::string& name, RecordType type, const std::string& new_value);
    
    // Query operations
    std::vector<DNSRecord> query(const std::string& domain, const std::string& query_name) const;
    std::vector<DNSRecord> query_by_type(const std::string& domain, const std::string& query_name, RecordType type) const;
    
    // Performance optimization
    void enable_cache(bool enable);
    void set_cache_ttl(uint64_t ttl_seconds);
    void clear_cache();
    size_t get_cache_size() const;
    
    // Statistics
    struct Statistics {
        std::atomic<uint64_t> total_queries;
        std::atomic<uint64_t> cache_hits;
        std::atomic<uint64_t> cache_misses;
        std::atomic<uint64_t> total_zones;
        std::atomic<uint64_t> total_records;
        
        Statistics() : total_queries(0), cache_hits(0), cache_misses(0), 
                      total_zones(0), total_records(0) {}
    };
    
    const Statistics& get_statistics() const { return stats_; }
    
private:
    mutable std::shared_mutex zones_mutex_;
    std::unordered_map<std::string, std::shared_ptr<DNSZone>> zones_;
    
    // Cache for performance
    struct CacheEntry {
        std::vector<DNSRecord> records;
        uint64_t expiry_time;
    };
    
    mutable std::shared_mutex cache_mutex_;
    std::unordered_map<std::string, CacheEntry> query_cache_;
    std::atomic<bool> cache_enabled_;
    std::atomic<uint64_t> cache_ttl_;
    
    Statistics stats_;
    
    // Helper functions
    bool is_cache_valid(const CacheEntry& entry) const;
    std::string generate_cache_key(const std::string& domain, const std::string& query_name, RecordType type) const;
};

// C-compatible FFI interface
extern "C" {
    // Zone management
    bool membra_dns_register_zone(HighPerformanceDNSResolver* resolver, 
                                   const char* did, const char* domain, const char* owner);
    bool membra_dns_remove_zone(HighPerformanceDNSResolver* resolver, const char* domain);
    
    // Record management  
    bool membra_dns_add_record(HighPerformanceDNSResolver* resolver,
                               const char* domain, uint8_t record_type,
                               const char* name, const char* value, uint32_t ttl);
    
    // Query operations
    char* membra_dns_query(HighPerformanceDNSResolver* resolver,
                           const char* domain, const char* query_name,
                           size_t* result_size);
    
    // Cache management
    void membra_dns_enable_cache(HighPerformanceDNSResolver* resolver, bool enable);
    void membra_dns_clear_cache(HighPerformanceDNSResolver* resolver);
    size_t membra_dns_get_cache_size(HighPerformanceDNSResolver* resolver);
    
    // Lifecycle
    HighPerformanceDNSResolver* membra_dns_create();
    void membra_dns_destroy(HighPerformanceDNSResolver* resolver);
}

} // namespace dns
} // namespace membra

#endif // MEMBRA_DNS_RESOLVER_HPP