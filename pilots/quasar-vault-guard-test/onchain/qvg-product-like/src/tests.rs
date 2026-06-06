use super::*;

#[test]
fn accepts_nonzero_instruction_hash() {
    assert!(ensure_nonzero_hash([9; 32]).is_ok());
}

#[test]
fn rejects_zero_instruction_hash() {
    assert!(ensure_nonzero_hash([0; 32]).is_err());
}

#[test]
fn accepts_nonzero_reason_code() {
    assert!(ensure_nonzero_reason(3).is_ok());
}

#[test]
fn rejects_zero_reason_code() {
    assert!(ensure_nonzero_reason(0).is_err());
}

fn deterministic_hash(seed: u8) -> [u8; 32] {
    let mut hash = [0u8; 32];
    for (index, byte) in hash.iter_mut().enumerate() {
        *byte = seed.wrapping_mul(31).wrapping_add(index as u8).wrapping_add(1);
    }
    hash
}

#[test]
fn property_nonzero_hashes_are_accepted_for_deterministic_cases() {
    for seed in 1u8..=255 {
        assert!(ensure_nonzero_hash(deterministic_hash(seed)).is_ok());
    }
}

#[test]
fn property_zero_hash_is_the_rejected_hash_case() {
    for seed in 0u8..=255 {
        let hash = if seed == 0 { [0; 32] } else { deterministic_hash(seed) };
        let result = ensure_nonzero_hash(hash);
        assert_eq!(result.is_err(), seed == 0);
    }
}

#[test]
fn property_all_nonzero_reason_codes_are_accepted() {
    for reason_code in 1u8..=255 {
        assert!(ensure_nonzero_reason(reason_code).is_ok());
    }
}

#[test]
fn client_flow_sequence_keeps_all_public_invariants_local() {
    let review_hash = deterministic_hash(11);
    let receipt_hash = deterministic_hash(29);

    assert!(ensure_nonzero_hash(review_hash).is_ok());
    assert!(ensure_nonzero_hash(receipt_hash).is_ok());
    assert!(ensure_nonzero_reason(7).is_ok());
}
