"""Apply the established full decode and old-asset checks to Unit 5 only."""
import verify_4a_unit4_audio as verify

verify.DRAFT = verify.ROOT / "content/drafts/4A-T1-W01-UNIT5"
verify.BASELINE = "135f062cd1272950649aad4cab0354889f7744e2"

if __name__ == "__main__":
    verify.main()
