from evaluation.week4_testbench import load_cases, run_case


CASES = {case["id"]: case for case in load_cases("evaluation/week4_test_cases.json")}


def assert_case(case_id: str):
    result = run_case(CASES[case_id])
    assert result["passed"], result["failures"]
    return result["actual"]


def test_w4_01_ordinary_success_regression():
    actual = assert_case("W4-01")
    assert actual["result_type"] == "report"


def test_w4_02_missing_evidence_stops_before_provider():
    actual = assert_case("W4-02")
    assert actual["provider_calls"] == 0


def test_w4_03_missing_scope_needs_input():
    actual = assert_case("W4-03")
    assert "intended_result" in actual["missing_fields"]


def test_w4_04_fake_citation_rejected():
    actual = assert_case("W4-04")
    assert actual["code"] == "invalid_citation"


def test_w4_05_unsupported_numeric_claim_rejected():
    actual = assert_case("W4-05")
    assert actual["code"] == "unsupported_numeric_claim"


def test_w4_06_malformed_json_not_retried():
    actual = assert_case("W4-06")
    assert actual["attempts"] == 1


def test_w4_07_timeout_is_bounded_and_retryable():
    actual = assert_case("W4-07")
    assert actual["attempts"] == 2
    assert actual["retryable"] is True
    assert actual["report"] is None


def test_w4_08_run_timeout_returns_controlled_failure():
    actual = assert_case("W4-08")
    assert actual["code"] == "run_timeout"
    assert actual["report"] is None


def test_w4_09_prompt_injection_cannot_change_permissions():
    actual = assert_case("W4-09")
    assert actual["injection_flags"]
    assert actual["permission_change_from_source_text"] is False
    assert actual["external_actions_authorized"] is False
    assert actual["untrusted_source_text_enforced"] is True


def test_w4_10_conflicting_amounts_are_surfaced():
    actual = assert_case("W4-10")
    assert actual["conflicts"][0]["status"] == "unresolved"
    assert actual["conflicts"][0]["requires_expert_review"] is True


def test_w4_11_revision_preserves_trace_and_reassesses_changes():
    actual = assert_case("W4-11")
    trace = actual["revision_trace"]
    assert trace["revision_of_report_id"] == "w3-report-001"
    assert trace["prior_evidence_ids_preserved"] == ["w4-intake-1"]
    assert trace["changed_requirements_reassessed"]


def test_w4_12_oversized_output_is_rejected():
    actual = assert_case("W4-12")
    assert actual["code"] == "output_too_large"
    assert actual["retryable"] is False
