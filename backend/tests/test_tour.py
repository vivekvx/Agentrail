from __future__ import annotations

import json

import pytest

import app.services.tour as tour
from app.services.tour import TourError, _parse_steps, generate_tour


def test_parse_steps_accepts_steps_object() -> None:
    raw = json.dumps({"steps": [{"title": "Start here", "path": "app", "explanation": "entry"}]})
    steps = _parse_steps(raw)
    assert steps == [{"title": "Start here", "path": "app", "explanation": "entry"}]


def test_parse_steps_accepts_bare_list() -> None:
    raw = json.dumps([{"title": "X"}])
    steps = _parse_steps(raw)
    assert steps[0]["title"] == "X"
    assert steps[0]["path"] == ""


def test_parse_steps_drops_entries_without_title() -> None:
    raw = json.dumps({"steps": [{"path": "no title"}, {"title": "keep"}]})
    assert [s["title"] for s in _parse_steps(raw)] == ["keep"]


def test_parse_steps_rejects_bad_json() -> None:
    with pytest.raises(TourError):
        _parse_steps("not json")


def test_parse_steps_rejects_empty() -> None:
    with pytest.raises(TourError):
        _parse_steps(json.dumps({"steps": []}))


def test_generate_tour_uses_ollama_response(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"response": json.dumps({"steps": [{"title": "Tour"}]})}).encode()

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        return FakeResp()

    monkeypatch.setattr(tour.urllib.request, "urlopen", fake_urlopen)
    steps = generate_tour("owner/repo", [{"name": "Python"}], {"name": "r", "children": []})
    assert steps[0]["title"] == "Tour"
    assert captured["url"].endswith("/api/generate")
