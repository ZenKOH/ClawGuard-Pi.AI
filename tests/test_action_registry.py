from backend.action_registry import ActionRegistry


def test_registry_executes_camera_frame():
    registry = ActionRegistry(mode="simulator")
    result = registry.execute("capture_camera_frame", {"reason": "test"})
    assert result["action"] == "capture_camera_frame"
    assert result["mode"] == "simulator"


def test_registry_exports_rehab_summary():
    registry = ActionRegistry(mode="simulator")
    result = registry.execute("export_rehab_session_summary", {"case_id": "case-demo-01"})
    assert result["summary"]["clinician_review_required"] is True
    assert result["summary"]["case_id"] == "case-demo-01"
