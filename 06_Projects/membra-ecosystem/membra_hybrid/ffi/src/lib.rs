// FFI layer for calling C++ DNS resolver from Rust
use std::ffi::{CString, CStr};
use std::os::raw::{c_char, c_uint, c_size_t};
use std::ptr;
use std::sync::Arc;

// Opaque pointer to C++ resolver
#[repr(C)]
pub struct DnsResolver {
    _private: [u8; 0], // Zero-sized type to represent opaque pointer
}

extern "C" {
    // C++ FFI functions
    fn membra_dns_create() -> *mut DnsResolver;
    fn membra_dns_destroy(resolver: *mut DnsResolver);
    fn membra_dns_register_zone(
        resolver: *mut DnsResolver,
        did: *const c_char,
        domain: *const c_char,
        owner: *const c_char,
    ) -> bool;
    fn membra_dns_remove_zone(resolver: *mut DnsResolver, domain: *const c_char) -> bool;
    fn membra_dns_add_record(
        resolver: *mut DnsResolver,
        domain: *const c_char,
        record_type: u8,
        name: *const c_char,
        value: *const c_char,
        ttl: u32,
    ) -> bool;
    fn membra_dns_enable_cache(resolver: *mut DnsResolver, enable: bool);
    fn membra_dns_clear_cache(resolver: *mut DnsResolver);
    fn membra_dns_get_cache_size(resolver: *mut DnsResolver) -> usize;
    fn membra_dns_query(
        resolver: *mut DnsResolver,
        domain: *const c_char,
        query_name: *const c_char,
        result_size: *mut c_size_t,
    ) -> *mut c_char;
}

// Rust wrapper for C++ DNS resolver
pub struct RustDnsResolver {
    inner: *mut DnsResolver,
}

impl RustDnsResolver {
    pub fn new() -> Result<Self, String> {
        let inner = unsafe { membra_dns_create() };
        if inner.is_null() {
            return Err("Failed to create DNS resolver".to_string());
        }
        Ok(RustDnsResolver { inner })
    }
    
    pub fn register_zone(&self, did: &str, domain: &str, owner: &str) -> Result<(), String> {
        let did_cstr = CString::new(did).map_err(|e| e.to_string())?;
        let domain_cstr = CString::new(domain).map_err(|e| e.to_string())?;
        let owner_cstr = CString::new(owner).map_err(|e| e.to_string())?;
        
        let success = unsafe {
            membra_dns_register_zone(self.inner, did_cstr.as_ptr(), domain_cstr.as_ptr(), owner_cstr.as_ptr())
        };
        
        if success {
            Ok(())
        } else {
            Err("Failed to register zone".to_string())
        }
    }
    
    pub fn remove_zone(&self, domain: &str) -> Result<(), String> {
        let domain_cstr = CString::new(domain).map_err(|e| e.to_string())?;
        
        let success = unsafe {
            membra_dns_remove_zone(self.inner, domain_cstr.as_ptr())
        };
        
        if success {
            Ok(())
        } else {
            Err("Failed to remove zone".to_string())
        }
    }
    
    pub fn add_record(&self, domain: &str, record_type: u8, name: &str, value: &str, ttl: u32) -> Result<(), String> {
        let domain_cstr = CString::new(domain).map_err(|e| e.to_string())?;
        let name_cstr = CString::new(name).map_err(|e| e.to_string())?;
        let value_cstr = CString::new(value).map_err(|e| e.to_string())?;
        
        let success = unsafe {
            membra_dns_add_record(self.inner, domain_cstr.as_ptr(), record_type, name_cstr.as_ptr(), value_cstr.as_ptr(), ttl)
        };
        
        if success {
            Ok(())
        } else {
            Err("Failed to add record".to_string())
        }
    }
    
    pub fn enable_cache(&self, enable: bool) {
        unsafe {
            membra_dns_enable_cache(self.inner, enable);
        }
    }
    
    pub fn clear_cache(&self) {
        unsafe {
            membra_dns_clear_cache(self.inner);
        }
    }
    
    pub fn get_cache_size(&self) -> usize {
        unsafe {
            membra_dns_get_cache_size(self.inner)
        }
    }
    
    pub fn query(&self, domain: &str, query_name: &str) -> Result<String, String> {
        let domain_cstr = CString::new(domain).map_err(|e| e.to_string())?;
        let query_name_cstr = CString::new(query_name).map_err(|e| e.to_string())?;
        
        let mut result_size: c_size_t = 0;
        let result_ptr = unsafe {
            membra_dns_query(self.inner, domain_cstr.as_ptr(), query_name_cstr.as_ptr(), &mut result_size)
        };
        
        if result_ptr.is_null() {
            return Err("Query returned null".to_string());
        }
        
        let result = unsafe {
            CStr::from_ptr(result_ptr).to_string_lossy().into_owned()
        };
        
        // Free the C string (assuming C++ allocated it with malloc)
        unsafe {
            libc::free(result_ptr as *mut libc::c_void);
        }
        
        Ok(result)
    }
}

impl Drop for RustDnsResolver {
    fn drop(&mut self) {
        if !self.inner.is_null() {
            unsafe {
                membra_dns_destroy(self.inner);
            }
        }
    }
}

unsafe impl Send for RustDnsResolver {}
unsafe impl Sync for RustDnsResolver {}

// Thread-safe wrapper using Arc
pub struct ThreadSafeDnsResolver {
    inner: Arc<RustDnsResolver>,
}

impl ThreadSafeDnsResolver {
    pub fn new() -> Result<Self, String> {
        let resolver = RustDnsResolver::new()?;
        Ok(ThreadSafeDnsResolver {
            inner: Arc::new(resolver),
        })
    }
    
    pub fn register_zone(&self, did: &str, domain: &str, owner: &str) -> Result<(), String> {
        self.inner.register_zone(did, domain, owner)
    }
    
    pub fn remove_zone(&self, domain: &str) -> Result<(), String> {
        self.inner.remove_zone(domain)
    }
    
    pub fn add_record(&self, domain: &str, record_type: u8, name: &str, value: &str, ttl: u32) -> Result<(), String> {
        self.inner.add_record(domain, record_type, name, value, ttl)
    }
    
    pub fn enable_cache(&self, enable: bool) {
        self.inner.enable_cache(enable);
    }
    
    pub fn clear_cache(&self) {
        self.inner.clear_cache();
    }
    
    pub fn get_cache_size(&self) -> usize {
        self.inner.get_cache_size()
    }
    
    pub fn query(&self, domain: &str, query_name: &str) -> Result<String, String> {
        self.inner.query(domain, query_name)
    }
}

impl Clone for ThreadSafeDnsResolver {
    fn clone(&self) -> Self {
        ThreadSafeDnsResolver {
            inner: Arc::clone(&self.inner),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_resolver_creation() {
        let resolver = RustDnsResolver::new();
        assert!(resolver.is_ok());
    }
    
    #[test]
    fn test_thread_safe_resolver() {
        let resolver = ThreadSafeDnsResolver::new();
        assert!(resolver.is_ok());
    }
    
    #[test]
    fn test_zone_registration() {
        let resolver = RustDnsResolver::new().unwrap();
        let result = resolver.register_zone("did:example:123", "example.com", "owner123");
        // This will fail until C++ library is linked
        // assert!(result.is_ok());
    }
}