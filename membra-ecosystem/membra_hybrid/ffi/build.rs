use std::env;
use std::path::PathBuf;

fn main() {
    // Build the C++ library
    let dst = cmake::Config::new("../cpp-core")
        .define("CMAKE_BUILD_TYPE", "Release")
        .define("BUILD_SHARED_LIBS", "ON")
        .build();
    
    println!("cargo:rustc-link-search=native={}/lib", dst.display());
    println!("cargo:rustc-link-lib=membra_dns_ffi");
    println!("cargo:rustc-link-lib=ssl");
    println!("cargo:rustc-link-lib=crypto");
    println!("cargo:rustc-link-lib=pthread");
    
    // Generate Rust bindings
    let bindings = bindgen::Builder::default()
        .header("../cpp-core/dns_resolver.hpp")
        .allowlist_function("membra_.*")
        .allowlist_type("DnsResolver")
        .opaque_type("std::.*")
        .opaque_type("membra::dns::.*")
        .generate()
        .expect("Unable to generate bindings");
    
    let out_path = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");
    
    println!("cargo:rerun-if-changed=../cpp-core/dns_resolver.hpp");
    println!("cargo:rerun-if-changed=../cpp-core/dns_resolver.cpp");
}