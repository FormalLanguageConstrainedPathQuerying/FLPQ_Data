import hashlib
import io
import pathlib
import tarfile

import pytest
import requests

import flpq_data
import flpq_data.dataset.data as data
from flpq_data.config import VERSION
from flpq_data.dataset import DATASET_KEY_PREFIX, DATASET_URL, graph_dir
from flpq_data.dataset.data import download, download_graph
from flpq_data.dataset.registry import GraphInfo

NAME = "g1"


def _make_archive(tmp_path: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Build a single-top-dir tarball; return (archive path, sha256)."""
    src = tmp_path / f"{NAME}-src" / NAME
    (src / "graph").mkdir(parents=True)
    (src / "README.md").write_text("readme")
    (src / "graph" / "a.mtx").write_text("mtx")
    archive = tmp_path / f"{NAME}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(src, arcname=NAME)
    return archive, hashlib.sha256(archive.read_bytes()).hexdigest()


class _FakeResponse:
    """Minimal stand-in for ``requests.Response`` for the download tests."""

    def __init__(self, content: bytes) -> None:
        self.raw = io.BytesIO(content)

    def raise_for_status(self) -> None:
        pass

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        pass


def _fake_info(sha256: str) -> GraphInfo:
    return GraphInfo(
        name=NAME,
        category="test",
        num_nodes=2,
        num_edges=1,
        size_mb=0.001,
        size_bytes=1000,
        sha256=sha256,
        queries=(),
    )


def _install_fixture(tmp_path: pathlib.Path, monkeypatch) -> tuple[pathlib.Path, str]:
    """Point the cache and the registry at fakes; return (archive, digest)."""
    archive, digest = _make_archive(tmp_path)
    monkeypatch.setenv("FLPQ_DATA_CACHE", str(tmp_path / "cache"))
    monkeypatch.setattr(data, "graph_info", lambda name: _fake_info(digest))
    monkeypatch.setattr(
        data.requests, "get", lambda **kwargs: _FakeResponse(archive.read_bytes())
    )
    return archive, digest


def test_url_constants():
    # The whole dataset lives under the current major-version prefix; it
    # moves only on a major release, so the literals are pinned here.
    assert DATASET_KEY_PREFIX == "6.0.0/graph"
    assert DATASET_URL == "https://cfpq-data.storage.yandexcloud.net/6.0.0/graph/"
    assert flpq_data.__version__ == VERSION


def test_graph_dir_miss_downloads_and_installs(tmp_path, monkeypatch):
    _, digest = _install_fixture(tmp_path, monkeypatch)

    path = graph_dir(NAME)

    assert path == tmp_path / "cache" / "6.0.0" / "graph" / NAME
    assert (path / "README.md").read_text() == "readme"
    assert (path / "graph" / "a.mtx").read_text() == "mtx"
    assert (path / f"{NAME}.tar.gz").is_file()
    assert (path / f"{NAME}.tar.gz.sha256").read_text().strip() == digest


def test_graph_dir_hit_no_network(tmp_path, monkeypatch):
    _install_fixture(tmp_path, monkeypatch)
    first = graph_dir(NAME)

    def no_network(**kwargs):
        raise AssertionError("the cache hit must not touch the network")

    monkeypatch.setattr(data.requests, "get", no_network)

    assert graph_dir(NAME) == first


def test_graph_dir_tampered_archive(tmp_path, monkeypatch):
    archive, digest = _install_fixture(tmp_path, monkeypatch)
    original = archive.read_bytes()
    path = graph_dir(NAME)
    stored = path / f"{NAME}.tar.gz"
    stored.write_bytes(stored.read_bytes() + b"tamper")

    # The default trusts the sidecar written at install.
    assert graph_dir(NAME) == path

    # verify=True re-hashes, misses, and reinstalls from the (fake) network.
    calls = []

    def fake_get(**kwargs):
        calls.append(kwargs)
        return _FakeResponse(original)

    monkeypatch.setattr(data.requests, "get", fake_get)
    assert graph_dir(NAME, verify=True) == path
    assert len(calls) == 1
    assert hashlib.sha256(stored.read_bytes()).hexdigest() == digest


def test_graph_dir_missing_sidecar(tmp_path, monkeypatch):
    archive, _ = _install_fixture(tmp_path, monkeypatch)
    original = archive.read_bytes()
    path = graph_dir(NAME)
    (path / f"{NAME}.tar.gz.sha256").unlink()

    # verify=True re-hashes and hits with zero network.
    def no_network(**kwargs):
        raise AssertionError("verify=True must not touch the network")

    monkeypatch.setattr(data.requests, "get", no_network)
    assert graph_dir(NAME, verify=True) == path

    # The default trusts the sidecar: a missing sidecar is a miss.
    calls = []

    def fake_get(**kwargs):
        calls.append(kwargs)
        return _FakeResponse(original)

    monkeypatch.setattr(data.requests, "get", fake_get)
    assert graph_dir(NAME) == path
    assert len(calls) == 1


def test_graph_dir_http_error_leaves_cache_untouched(tmp_path, monkeypatch):
    archive, digest = _make_archive(tmp_path)
    monkeypatch.setenv("FLPQ_DATA_CACHE", str(tmp_path / "cache"))
    monkeypatch.setattr(data, "graph_info", lambda name: _fake_info(digest))

    class _ErrorResponse(_FakeResponse):
        def raise_for_status(self) -> None:
            raise requests.HTTPError("500 Server Error")

    monkeypatch.setattr(
        data.requests, "get", lambda **kwargs: _ErrorResponse(archive.read_bytes())
    )

    with pytest.raises(requests.HTTPError):
        graph_dir(NAME)

    parent = tmp_path / "cache" / "6.0.0" / "graph"
    assert not (parent / NAME).exists()
    assert list(parent.iterdir()) == []


def test_graph_dir_sha_mismatch_leaves_cache_untouched(tmp_path, monkeypatch):
    archive, _ = _make_archive(tmp_path)
    monkeypatch.setenv("FLPQ_DATA_CACHE", str(tmp_path / "cache"))
    # The registry expects a different digest than the served bytes.
    monkeypatch.setattr(data, "graph_info", lambda name: _fake_info("0" * 64))
    monkeypatch.setattr(
        data.requests, "get", lambda **kwargs: _FakeResponse(archive.read_bytes())
    )

    with pytest.raises(ValueError, match="sha256 mismatch"):
        graph_dir(NAME)

    parent = tmp_path / "cache" / "6.0.0" / "graph"
    assert not (parent / NAME).exists()
    assert list(parent.iterdir()) == []


def test_graph_dir_unknown_name(tmp_path, monkeypatch):
    monkeypatch.setenv("FLPQ_DATA_CACHE", str(tmp_path / "cache"))
    with pytest.raises(FileNotFoundError):
        graph_dir("nonexistent")


def test_download_graph_deprecated(tmp_path, monkeypatch):
    _install_fixture(tmp_path, monkeypatch)
    with pytest.warns(DeprecationWarning, match="graph_dir"):
        assert download_graph(NAME) == tmp_path / "cache" / "6.0.0" / "graph" / NAME


def test_download_deprecated(tmp_path, monkeypatch):
    _install_fixture(tmp_path, monkeypatch)
    with pytest.warns(DeprecationWarning, match="graph_dir"):
        assert download(NAME) == tmp_path / "cache" / "6.0.0" / "graph" / NAME


def test_download_graph_unknown_name_warns_and_raises():
    with pytest.warns(DeprecationWarning, match="graph_dir"):
        with pytest.raises(FileNotFoundError):
            download_graph("")
