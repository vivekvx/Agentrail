from __future__ import annotations

import json
from pathlib import Path

import pytest

import app.services.rag as rag
from app.services.rag import RagError, _cosine, answer, build_index, chunk_text


def test_chunk_text_splits_on_size_and_drops_blanks() -> None:
    text = "a\n" * 100  # 200 chars
    chunks = chunk_text(text, 50)
    assert len(chunks) >= 3
    assert all(c.strip() for c in chunks)


def test_cosine_identical_is_one_orthogonal_is_zero() -> None:
    assert _cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert _cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert _cosine([0, 0], [1, 1]) == 0.0


def test_build_index_embeds_each_chunk(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hi')\n")
    (tmp_path / "img.png").write_bytes(b"\x89PNG")  # skipped (binary ext)
    monkeypatch.setattr(rag, "_embed", lambda text: [0.1, 0.2, 0.3])

    index = build_index(tmp_path)

    assert len(index) == 1
    assert index[0]["path"] == "main.py"
    assert index[0]["vec"] == [0.1, 0.2, 0.3]


def test_answer_retrieves_nearest_chunk_and_cites_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = [
        {"path": "auth.py", "text": "def login(): ...", "vec": [1.0, 0.0]},
        {"path": "db.py", "text": "engine = create_engine()", "vec": [0.0, 1.0]},
    ]
    # Question embeds parallel to auth.py.
    monkeypatch.setattr(rag, "_embed", lambda text: [1.0, 0.0])

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"response": "Login is in auth.py"}).encode()

    monkeypatch.setattr(rag.urllib.request, "urlopen", lambda req, timeout: FakeResp())

    result = answer("where is login?", index)
    assert "auth.py" in result["sources"]
    assert result["answer"] == "Login is in auth.py"


def test_answer_without_index_raises() -> None:
    with pytest.raises(RagError):
        answer("anything", [])
