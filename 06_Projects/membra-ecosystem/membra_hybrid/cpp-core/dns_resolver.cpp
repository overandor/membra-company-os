#include "dns_resolver.hpp"
#include <openssl/sha.h>
#include <sstream>
#include <iomanip>
#include <cstring>

namespace membra {
namespace dns {

// DNSZone implementation
std::string DNSZone::generate_zone_hash() const {
    std::string data = did + domain + owner + std::to_string(created_at);
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256(reinterpret_cast<const unsigned char*>(data.c_str()), data.size(), hash);
    
    std::stringstream ss;
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        ss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(hash[i]);
    }
    return ss.str();
}

// HighPerformanceDNSResolver implementation
HighPerformanceDNSResolver::HighPerformanceDNSResolver() 
    : cache_enabled_(true), cache_ttl_(300) {
}

HighPerformanceDNSResolver::~HighPerformanceDNSResolver() {
    std::unique_lock<std::shared_mutex> lock(zones_mutex_);
    zones_.clear();
}

bool HighPerformanceDNSResolver::register_zone(const std::string& did, 
                                                const std::string& domain, 
                                                const std::string& owner) {
    std::unique_lock<std::shared_mutex> lock(zones_mutex_);
    
    if (zones_.find(domain) != zones_.end()) {
        return false; // Zone already exists
    }
    
    auto zone = std::make_shared<DNSZone>(did, domain, owner);
    zones_[domain] = zone;
    stats_.total_zones++;
    
    // Clear related cache entries
    std::unique_lock<std::shared_mutex> cache_lock(cache_mutex_);
    query_cache_.clear();
    
    return true;
}

bool HighPerformanceDNSResolver::remove_zone(const std::string& domain) {
    std::unique_lock<std::shared_mutex> lock(zones_mutex_);
    
    auto it = zones_.find(domain);
    if (it == zones_.end()) {
        return false;
    }
    
    stats_.total_records -= it->second->records.size();
    zones_.erase(it);
    stats_.total_zones--;
    
    // Clear related cache entries
    std::unique_lock<std::shared_mutex> cache_lock(cache_mutex_);
    query_cache_.clear();
    
    return true;
}

std::shared_ptr<DNSZone> HighPerformanceDNSResolver::get_zone(const std::string& domain) const {
    std::shared_lock<std::shared_mutex> lock(zones_mutex_);
    auto it = zones_.find(domain);
    return (it != zones_.end()) ? it->second : nullptr;
}

std::vector<std::shared_ptr<DNSZone>> HighPerformanceDNSResolver::list_zones() const {
    std::shared_lock<std::shared_mutex> lock(zones_mutex_);
    std::vector<std::shared_ptr<DNSZone>> result;
    result.reserve(zones_.size());
    
    for (const auto& pair : zones_) {
        result.push_back(pair.second);
    }
    
    return result;
}

bool HighPerformanceDNSResolver::add_record(const std::string& domain, DNSRecord record) {
    std::unique_lock<std::shared_mutex> lock(zones_mutex_);
    
    auto it = zones_.find(domain);
    if (it == zones_.end()) {
        return false;
    }
    
    auto& zone = it->second;
    zone->records[record.name].push_back(std::move(record));
    stats_.total_records++;
    
    // Update zone timestamp
    auto now = std::chrono::system_clock::now();
    zone->updated_at = std::chrono::duration_cast<std::chrono::seconds>(
        now.time_since_epoch()).count();
    
    // Clear related cache entries
    std::unique_lock<std::shared_mutex> cache_lock(cache_mutex_);
    query_cache_.clear();
    
    return true;
}

bool HighPerformanceDNSResolver::remove_record(const std::string& domain, 
                                               const std::string& name, 
                                               RecordType type) {
    std::unique_lock<std::shared_mutex> lock(zones_mutex_);
    
    auto it = zones_.find(domain);
    if (it == zones_.end()) {
        return false;
    }
    
    auto& zone = it->second;
    auto records_it = zone->records.find(name);
    if (records_it == zone->records.end()) {
        return false;
    }
    
    size_t original_size = records_it->second.size();
    records_it->second.erase(
        std::remove_if(records_it->second.begin(), records_it->second.end(),
            [type](const DNSRecord& r) { return r.type == type; }),
        records_it->second.end());
    
    if (records_it->second.empty()) {
        zone->records.erase(records_it);
    }
    
    size_t removed = original_size - records_it->second.size();
    if (removed > 0) {
        stats_.total_records -= removed;
        
        // Update zone timestamp
        auto now = std::chrono::system_clock::now();
        zone->updated_at = std::chrono::duration_cast<std::chrono::seconds>(
            now.time_since_epoch()).count();
        
        // Clear related cache entries
        std::unique_lock<std::shared_mutex> cache_lock(cache_mutex_);
        query_cache_.clear();
        
        return true;
    }
    
    return false;
}

bool HighPerformanceDNSResolver::update_record(const std::string& domain,
                                               const std::string& name,
                                               RecordType type,
                                               const std::string& new_value) {
    std::unique_lock<std::shared_mutex> lock(zones_mutex_);
    
    auto it = zones_.find(domain);
    if (it == zones_.end()) {
        return false;
    }
    
    auto& zone = it->second;
    auto records_it = zone->records.find(name);
    if (records_it == zone->records.end()) {
        return false;
    }
    
    for (auto& record : records_it->second) {
        if (record.type == type) {
            record.value = new_value;
            auto now = std::chrono::system_clock::now();
            record.updated_at = std::chrono::duration_cast<std::chrono::seconds>(
                now.time_since_epoch()).count();
            
            // Update zone timestamp
            zone->updated_at = record.updated_at;
            
            // Clear related cache entries
            std::unique_lock<std::shared_mutex> cache_lock(cache_mutex_);
            query_cache_.clear();
            
            return true;
        }
    }
    
    return false;
}

std::vector<DNSRecord> HighPerformanceDNSResolver::query(const std::string& domain,
                                                          const std::string& query_name) const {
    stats_.total_queries++;
    
    // Check cache first
    if (cache_enabled_) {
        std::string cache_key = generate_cache_key(domain, query_name, static_cast<RecordType>(0));
        
        std::shared_lock<std::shared_mutex> cache_lock(cache_mutex_);
        auto it = query_cache_.find(cache_key);
        if (it != query_cache_.end() && is_cache_valid(it->second)) {
            stats_.cache_hits++;
            return it->second.records;
        }
        stats_.cache_misses++;
    }
    
    // Query from data
    std::shared_lock<std::shared_mutex> lock(zones_mutex_);
    auto it = zones_.find(domain);
    if (it == zones_.end()) {
        return {};
    }
    
    auto records_it = it->second->records.find(query_name);
    if (records_it == it->second->records.end()) {
        return {};
    }
    
    auto result = records_it->second;
    
    // Update cache
    if (cache_enabled_) {
        std::string cache_key = generate_cache_key(domain, query_name, static_cast<RecordType>(0));
        uint64_t now = std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        
        std::unique_lock<std::shared_mutex> cache_lock(cache_mutex_);
        query_cache_[cache_key] = {result, now + cache_ttl_};
    }
    
    return result;
}

std::vector<DNSRecord> HighPerformanceDNSResolver::query_by_type(const std::string& domain,
                                                                  const std::string& query_name,
                                                                  RecordType type) const {
    stats_.total_queries++;
    
    // Check cache first
    if (cache_enabled_) {
        std::string cache_key = generate_cache_key(domain, query_name, type);
        
        std::shared_lock<std::shared_mutex> cache_lock(cache_mutex_);
        auto it = query_cache_.find(cache_key);
        if (it != query_cache_.end() && is_cache_valid(it->second)) {
            stats_.cache_hits++;
            return it->second.records;
        }
        stats_.cache_misses++;
    }
    
    // Query from data
    std::shared_lock<std::shared_mutex> lock(zones_mutex_);
    auto it = zones_.find(domain);
    if (it == zones_.end()) {
        return {};
    }
    
    auto records_it = it->second->records.find(query_name);
    if (records_it == it->second->records.end()) {
        return {};
    }
    
    std::vector<DNSRecord> result;
    for (const auto& record : records_it->second) {
        if (record.type == type) {
            result.push_back(record);
        }
    }
    
    // Update cache
    if (cache_enabled_) {
        std::string cache_key = generate_cache_key(domain, query_name, type);
        uint64_t now = std::chrono::duration_cast<std::chrono::seconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        
        std::unique_lock<std::shared_mutex> cache_lock(cache_mutex_);
        query_cache_[cache_key] = {result, now + cache_ttl_};
    }
    
    return result;
}

void HighPerformanceDNSResolver::enable_cache(bool enable) {
    cache_enabled_ = enable;
    if (!enable) {
        clear_cache();
    }
}

void HighPerformanceDNSResolver::set_cache_ttl(uint64_t ttl_seconds) {
    cache_ttl_ = ttl_seconds;
}

void HighPerformanceDNSResolver::clear_cache() {
    std::unique_lock<std::shared_mutex> lock(cache_mutex_);
    query_cache_.clear();
}

size_t HighPerformanceDNSResolver::get_cache_size() const {
    std::shared_lock<std::shared_mutex> lock(cache_mutex_);
    return query_cache_.size();
}

bool HighPerformanceDNSResolver::is_cache_valid(const CacheEntry& entry) const {
    uint64_t now = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    return now < entry.expiry_time;
}

std::string HighPerformanceDNSResolver::generate_cache_key(const std::string& domain,
                                                             const std::string& query_name,
                                                             RecordType type) const {
    return domain + ":" + query_name + ":" + std::to_string(static_cast<uint8_t>(type));
}

// FFI implementation
extern "C" {
    HighPerformanceDNSResolver* membra_dns_create() {
        return new HighPerformanceDNSResolver();
    }
    
    void membra_dns_destroy(HighPerformanceDNSResolver* resolver) {
        delete resolver;
    }
    
    bool membra_dns_register_zone(HighPerformanceDNSResolver* resolver,
                                   const char* did, const char* domain, const char* owner) {
        if (!resolver || !did || !domain || !owner) return false;
        return resolver->register_zone(did, domain, owner);
    }
    
    bool membra_dns_remove_zone(HighPerformanceDNSResolver* resolver, const char* domain) {
        if (!resolver || !domain) return false;
        return resolver->remove_zone(domain);
    }
    
    bool membra_dns_add_record(HighPerformanceDNSResolver* resolver,
                               const char* domain, uint8_t record_type,
                               const char* name, const char* value, uint32_t ttl) {
        if (!resolver || !domain || !name || !value) return false;
        return resolver->add_record(domain, DNSRecord(static_cast<RecordType>(record_type), name, value, ttl));
    }
    
    void membra_dns_enable_cache(HighPerformanceDNSResolver* resolver, bool enable) {
        if (resolver) resolver->enable_cache(enable);
    }
    
    void membra_dns_clear_cache(HighPerformanceDNSResolver* resolver) {
        if (resolver) resolver->clear_cache();
    }
    
    size_t membra_dns_get_cache_size(HighPerformanceDNSResolver* resolver) {
        return resolver ? resolver->get_cache_size() : 0;
    }
}

} // namespace dns
} // namespace membra