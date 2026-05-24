use std::env;
use std::path::PathBuf;

fn main() {
    // Build C++ consensus core
    let cpp_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap())
        .parent()
        .unwrap()
        .join("cpp");
    
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    
    // Compile C++ consensus library
    cc::Build::new()
        .cpp(true)
        .opt_level(3)
        .file(cpp_dir.join("src/consensus.cpp"))
        .include(cpp_dir.join("include"))
        .flag_if_supported("-std=c++17")
        .compile("membra_consensus");
    
    // Link the library
    println!("cargo:rustc-link-lib=static=membra_consensus");
    println!("cargo:rustc-link-search=native={}", out_dir.display());
    println!("cargo:rerun-if-changed=cpp/src/consensus.cpp");
    println!("cargo:rerun-if-changed=cpp/include/consensus.hpp");
}
