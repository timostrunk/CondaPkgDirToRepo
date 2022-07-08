import json
import pathlib
import tempfile
from typing import Any, Dict

import pytest

from CondaPkgDirToRepo.CondaPkgDirToRepoMain import (
    get_channel_from_package_filepath,
    get_conda_package_index,
    get_package_name_from_package_index,
    get_subdir_from_package_index,
    normalize_channel_name,
    rewrite_pkgs_dir_to_repo,
    walk_package_dir_iterator,
)


@pytest.fixture
def tmpdir():
    with tempfile.TemporaryDirectory() as td:
        yield pathlib.Path(td)


@pytest.fixture
def inputdirpath() -> pathlib.Path:
    inputsdir = pathlib.Path(__file__).absolute().parent / "inputs"
    return inputsdir


@pytest.fixture
def tarfilepath(inputdirpath: pathlib.Path):
    tarfile = inputdirpath / "testpackage.tar.bz2"
    return tarfile


@pytest.fixture
def reference_package_index_for_tarfilepath():
    jsonstr = '{"arch": null, "build": "py_0", "build_number": 0, "depends": ["python >=3.8"],' \
              ' "license": "MIT", "name": "treewalker", "noarch": "python", "platform": null,' \
              ' "subdir": "noarch", "timestamp": 1653302418288, "version": "1.0.0"}'
    reference_json = json.loads(jsonstr)
    return reference_json


def test_walk_package_dir_iterator(inputdirpath: pathlib.Path):
    pkgdir_path = inputdirpath / "sample_walk_package_dir_dir"
    reference_files = []
    for i in range(1, 5):
        reference_files.append(f"{i}.tar.bz2")
    actually_iterating = False
    for myfile, refffile in zip(sorted(walk_package_dir_iterator(pkgdir_path)), reference_files):
        assert myfile.name == refffile
        actually_iterating = True
    assert actually_iterating


def test_get_subdir_from_package_index(reference_package_index_for_tarfilepath: Dict[str, Any]):
    assert get_subdir_from_package_index(reference_package_index_for_tarfilepath) == "noarch"


def test_get_package_name_from_package_index(reference_package_index_for_tarfilepath: Dict[str, Any]):
    reference_package_name = "treewalker-1.0.0-py_0.tar.bz2"
    assert get_package_name_from_package_index(reference_package_index_for_tarfilepath) == reference_package_name


def test_get_conda_package_index(
    tarfilepath: pathlib.Path,
    reference_package_index_for_tarfilepath: Dict[str, Any | str],
):
    outjson = get_conda_package_index(tarfilepath)
    assert outjson == reference_package_index_for_tarfilepath


def test_get_repolink_from_package_filepath(inputdirpath: pathlib.Path):
    pkg_path = inputdirpath / "sample_walk_package_dir_dir" / "1.tar.bz2"
    channel = get_channel_from_package_filepath(pkg_path)
    assert channel == "conda-forge"

    pkg_path = inputdirpath / "sample_walk_package_dir_dir" / "2.tar.bz2"
    channel = get_channel_from_package_filepath(pkg_path)
    assert channel == "unknown"


def test_normalize_channel_name():
    teststring = "https://abc.def/.de/"
    outstring = normalize_channel_name(teststring)
    assert outstring == "abc.def_.de"


def test_rewrite_pkgs_dir_to_repo(tmpdir: pathlib.Path, inputdirpath: pathlib.Path):
    outfile = tmpdir / "conda-forge" / "linux-64" / "bzip2-1.0.8-h7f98852_4.tar.bz2"
    assert not outfile.exists()
    pkg_path = inputdirpath / "sample_walk_package_dir_dir"
    rewrite_pkgs_dir_to_repo(pkg_path, tmpdir)
    assert outfile.is_file()
