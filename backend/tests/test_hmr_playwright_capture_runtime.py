import asyncio

from utils import hmr_playwright_capture as capture


async def _write_fake_png(html_text, output_path, width, height):
    output_path.write_bytes(b"fake-png" * 200)


def test_playwright_capture_normal_no_event_loop(monkeypatch, tmp_path):
    monkeypatch.setattr(capture, "_capture_html_to_png", _write_fake_png)

    result = capture.resolve_hmr_playwright_capture(
        {"number": "$324", "subline": "yearly savings"},
        "savings_dashboard",
        tmp_path,
        270,
        480,
    )

    assert result["resolved_asset_type"] == "playwright_capture"
    assert result["resolved_asset_provider"] == "local_playwright_html"
    assert result["asset_resolution_status"] == "resolved"
    assert result["fallback_used"] is False
    assert result["playwright_motion_mode"] == "static_capture"
    assert result["capture_steps"] == ["static_capture"]
    assert result["visible_interaction"] is False


def test_playwright_capture_inside_running_event_loop(monkeypatch, tmp_path):
    monkeypatch.setattr(capture, "_capture_html_to_png", _write_fake_png)

    async def _call_from_async_route():
        return capture.resolve_hmr_playwright_capture(
            {"number": "$324", "subline": "yearly savings"},
            "savings_dashboard",
            tmp_path,
            270,
            480,
        )

    result = asyncio.run(_call_from_async_route())

    assert result["resolved_asset_type"] == "playwright_capture"
    assert result["asset_resolution_status"] == "resolved"
    assert result["fallback_used"] is False
    assert result["html_fallback_path"].endswith(".html")


def test_playwright_unavailable_reports_truthful_failure(monkeypatch, tmp_path):
    async def _raise_import_error(html_text, output_path, width, height):
        raise ImportError("playwright missing")

    monkeypatch.setattr(capture, "_capture_html_to_png", _raise_import_error)

    result = capture.resolve_hmr_playwright_capture(
        {"number": "$324", "subline": "yearly savings"},
        "savings_dashboard",
        tmp_path,
        270,
        480,
    )

    assert result["resolved_asset_type"] is None
    assert result["resolved_asset_path"] is None
    assert result["resolved_asset_provider"] is None
    assert result["asset_resolution_status"].startswith("playwright_unavailable:")
    assert result["fallback_used"] is True
    assert result["html_fallback_path"].endswith(".html")
    assert result["playwright_motion_mode"] == "static_capture"
    assert result["visible_interaction"] is False


def test_playwright_motion_sequence_preserves_report_fields_in_event_loop(monkeypatch, tmp_path):
    monkeypatch.setattr(capture, "_capture_html_to_png", _write_fake_png)

    async def _call_from_async_route():
        return capture.resolve_hmr_playwright_capture(
            {
                "prompt": "Compare this bill against cheaper plans.",
                "savings_number": "$324/year",
            },
            "receipt_audit_comparison",
            tmp_path,
            270,
            480,
        )

    result = asyncio.run(_call_from_async_route())

    assert result["resolved_asset_type"] == "playwright_capture"
    assert result["asset_resolution_status"] == "resolved"
    assert result["fallback_used"] is False
    assert result["playwright_motion_mode"] == "screenshot_sequence"
    assert result["capture_steps"] == [
        "empty_input",
        "typing_prompt",
        "submit_analyze",
        "results_reveal",
        "savings_result",
    ]
    assert result["visible_interaction"] is True
    assert len(result["resolved_asset_paths"]) == 5
    assert len(result["html_fallback_paths"]) == 5
