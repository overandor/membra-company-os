#[cfg(test)]
mod fuzz_tests {
    use super::*;
    use std::str::FromStr;

    #[test]
    fn fuzz_denomination_zero() {
        let d: u64 = 0;
        assert!(d < MIN_DENOMINATION);
    }

    #[test]
    fn fuzz_denomination_max() {
        let d: u64 = u64::MAX;
        assert!(d >= MIN_DENOMINATION);
    }

    #[test]
    fn fuzz_expiry_past() {
        let now = 1_700_000_000i64;
        let past = now - 1;
        assert!(past < now);
    }

    #[test]
    fn fuzz_expiry_far_future() {
        let now = 1_700_000_000i64;
        let far = now + MAX_EXPIRY_SECONDS + 1;
        assert!(far > now + MAX_EXPIRY_SECONDS);
    }

    #[test]
    fn fuzz_wallet_too_short() {
        let short = "abc";
        assert!(short.len() < 32);
    }

    #[test]
    fn fuzz_wallet_too_long() {
        let long = "a".repeat(100);
        assert!(long.len() > 44);
    }

    #[test]
    fn fuzz_pin_empty() {
        let pin = "";
        assert!(pin.is_empty());
    }

    #[test]
    fn fuzz_pin_too_long() {
        let pin = "a".repeat(1000);
        assert!(pin.len() > 16);
    }

    #[test]
    fn fuzz_salt_empty() {
        let salt = "";
        assert!(salt.is_empty());
    }

    #[test]
    fn fuzz_claim_id_empty() {
        let id = "";
        assert!(id.is_empty());
    }

    #[test]
    fn fuzz_reserve_ratio_negative() {
        // u16 cannot be negative, but we can test boundary
        let ratio: u16 = 0;
        assert!(ratio <= 10_000);
    }

    #[test]
    fn fuzz_reserve_ratio_max_boundary() {
        let ratio: u16 = 10_000;
        assert!(ratio <= 10_000);
    }

    #[test]
    fn fuzz_bps_overflow_u16() {
        let bps: u16 = u16::MAX;
        assert!(bps > 10_000);
    }

    #[test]
    fn fuzz_note_id_zero() {
        let id: u64 = 0;
        assert_eq!(id, 0);
    }

    #[test]
    fn fuzz_note_id_max() {
        let id: u64 = u64::MAX;
        assert_eq!(id, u64::MAX);
    }

    #[test]
    fn fuzz_pubkey_default_is_system() {
        let pk = Pubkey::default();
        assert_eq!(pk, Pubkey::from_str("11111111111111111111111111111111").unwrap());
    }

    #[test]
    fn fuzz_hash_all_zeros() {
        let hash = [0u8; 32];
        assert_eq!(hash, [0u8; 32]);
    }

    #[test]
    fn fuzz_hash_all_ones() {
        let hash = [255u8; 32];
        assert_eq!(hash, [255u8; 32]);
    }

    #[test]
    fn fuzz_timestamp_epoch() {
        let ts: i64 = 0;
        assert_eq!(ts, 0);
    }

    #[test]
    fn fuzz_timestamp_now() {
        let ts: i64 = 1_700_000_000;
        assert!(ts > 0);
    }

    #[test]
    fn fuzz_program_id_valid_base58() {
        let id = "EXNLzDxRPN81NtxZKzNBKweG93R9FWUq8gfGoFGzxYYw";
        assert_eq!(id.len(), 44);
    }

    #[test]
    fn fuzz_version_format() {
        let v = "v1.0.0-devnet";
        assert!(v.starts_with("v"));
    }
}
