"""display_quota_info must handle a non-object API payload gracefully."""

import quota_api_client as qc


def test_list_payload_prints_message_and_returns_none(capsys):
    assert qc.display_quota_info(["not", "a", "dict"]) is None
    assert "No quota information available" in capsys.readouterr().out


def test_none_payload_prints_message_and_returns_none(capsys):
    assert qc.display_quota_info(None) is None
    assert "No quota information available" in capsys.readouterr().out


def test_empty_object_returns_none(capsys):
    assert qc.display_quota_info({}) is None
    assert "No quota information available" in capsys.readouterr().out


def test_buckets_still_displayed(capsys):
    buckets = [
        {"modelId": "gemini-2.5-pro", "remainingFraction": 0.5, "resetTime": ""},
        {"modelId": "gemini-2.5-flash", "remainingFraction": 0.1, "resetTime": ""},
    ]
    assert qc.display_quota_info({"buckets": buckets}) == buckets
    out = capsys.readouterr().out
    assert "gemini-2.5-pro" in out
    assert "gemini-2.5-flash" in out
