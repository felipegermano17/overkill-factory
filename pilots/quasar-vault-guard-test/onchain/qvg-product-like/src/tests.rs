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
