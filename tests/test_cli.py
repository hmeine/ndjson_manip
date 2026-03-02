import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def env_with_pythonpath(repo_root):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_same_exports(expected_dir: Path, generated_dir: Path):
    expected_files = sorted(expected_dir.glob("*.json"))
    generated_files = sorted(generated_dir.glob("*.json"))

    # check that the same set of files was generated
    assert [path.name for path in generated_files] == [
        path.name for path in expected_files
    ]

    # now also check their contents
    for expected_file in expected_files:
        generated_file = generated_dir / expected_file.name
        assert _load_json(generated_file) == _load_json(expected_file)


def test_unpack(tmp_path, env_with_pythonpath, repo_root):
    source_ndjson = repo_root / "tests" / "export-flights.ndjson"
    expected_export_dir = repo_root / "tests" / "export-flights"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "ndjson_manip.unpack",
            "--file",
            str(source_ndjson),
        ],
        cwd=tmp_path,
        env=env_with_pythonpath,
        check=True,
    )

    check_same_exports(expected_export_dir, tmp_path)


def test_repack(tmp_path, env_with_pythonpath, repo_root):
    unpacked_directory = repo_root / "tests" / "export-flights"
    expected_ndjson = repo_root / "tests" / "export-flights.ndjson"

    repacked_ndjson = tmp_path / "repacked.ndjson"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ndjson_manip.repack",
            "--output",
            str(repacked_ndjson),
            str(unpacked_directory),
        ],
        env=env_with_pythonpath,
        check=True,
    )

    # we cannot directly compare the generated NDJSON with the expected one,
    # because the order of the lines and of the JSON keys may differ.  Instead,
    # we unpack the generated NDJSON again and check that we get the same files
    # as in the original unpacked directory.

    repacked_unpack_dir = tmp_path / "repacked-unpack"
    repacked_unpack_dir.mkdir()
    unpack_repacked_cmd = [
        sys.executable,
        "-m",
        "ndjson_manip.unpack",
        "--file",
        str(repacked_ndjson),
    ]
    subprocess.run(
        unpack_repacked_cmd,
        cwd=repacked_unpack_dir,
        env=env_with_pythonpath,
        check=True,
    )

    check_same_exports(unpacked_directory, repacked_unpack_dir)
