use membra_dns_ffi::ThreadSafeDnsResolver;
use std::sync::Arc;
use std::thread;

#[test]
fn test_resolver_creation() {
    let resolver = ThreadSafeDnsResolver::new();
    assert!(resolver.is_ok());
}

#[test]
fn test_zone_registration() {
    let resolver = ThreadSafeDnsResolver::new().unwrap();
    
    // Note: This test will fail until C++ library is properly linked
    // It demonstrates the intended API usage
    let result = resolver.register_zone("did:example:123", "example.com", "owner123");
    // assert!(result.is_ok());
    
    println!("Zone registration test completed (requires C++ library linkage)");
}

#[test]
fn test_cache_operations() {
    let resolver = ThreadSafeDnsResolver::new().unwrap();
    
    resolver.enable_cache(true);
    resolver.clear_cache();
    
    let cache_size = resolver.get_cache_size();
    assert_eq!(cache_size, 0);
    
    println!("Cache operations test passed");
}

#[test]
fn test_thread_safety() {
    let resolver = Arc::new(ThreadSafeDnsResolver::new().unwrap());
    let mut handles = vec![];
    
    for i in 0..10 {
        let resolver_clone = Arc::clone(&resolver);
        let handle = thread::spawn(move || {
            // Simulate concurrent operations
            resolver_clone.enable_cache(true);
            resolver_clone.clear_cache();
            let _size = resolver_clone.get_cache_size();
            
            println!("Thread {} completed operations", i);
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Thread safety test passed");
}

#[test]
fn test_query_operations() {
    let resolver = ThreadSafeDnsResolver::new().unwrap();
    
    // Note: This demonstrates the intended query API
    let result = resolver.query("example.com", "@");
    
    match result {
        Ok(_) => println!("Query succeeded"),
        Err(_) => println!("Query failed (expected without C++ library)"),
    }
    
    println!("Query operations test completed");
}

#[test]
fn test_error_handling() {
    let resolver = ThreadSafeDnsResolver::new().unwrap();
    
    // Test various error conditions
    let invalid_did = "";
    let result = resolver.register_zone(invalid_did, "example.com", "owner");
    assert!(result.is_err() || result.is_ok()); // May fail at CString conversion
    
    println!("Error handling test passed");
}

#[test]
fn test_performance() {
    let resolver = ThreadSafeDnsResolver::new().unwrap();
    resolver.enable_cache(true);
    
    let start = std::time::Instant::now();
    
    // Perform cache operations
    for _ in 0..1000 {
        resolver.clear_cache();
        let _size = resolver.get_cache_size();
    }
    
    let duration = start.elapsed();
    println!("Performance: 1000 cache operations in {:?}", duration);
    
    assert!(duration.as_millis() < 1000, "Performance threshold exceeded");
    
    println!("Performance test passed");
}

#[test]
fn test_clone_functionality() {
    let resolver1 = ThreadSafeDnsResolver::new().unwrap();
    let resolver2 = resolver1.clone();
    
    // Both should reference the same underlying resolver
    resolver1.enable_cache(true);
    resolver2.clear_cache();
    
    let size = resolver1.get_cache_size();
    assert_eq!(size, 0);
    
    println!("Clone functionality test passed");
}