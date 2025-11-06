// Full copy of rust_hasher/src/hasher.rs
use sha2::{Sha256, Digest};

pub fn hash_input(input: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(input.as_bytes());
    format!("{:x}", hasher.finalize())
}
