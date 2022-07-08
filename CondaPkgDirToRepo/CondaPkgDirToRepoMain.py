#!/usr/bin/env python3
import json
import os
import pathlib
import shutil
import tarfile
from typing import Dict, Iterator

import click


def walk_package_dir_iterator(pkg_directory: pathlib.Path) -> Iterator[pathlib.Path]:
    """
    Walks pkg directory in conda installation.
    :param pkg_directory: Path to pkg directory
    :return: yields each package.tar.bz2 path
    """
    assert pkg_directory.is_dir(), "walk_package_dir requires directory as input"
    for pkgfile in pkg_directory.iterdir():
        if pkgfile.is_file() and str(pkgfile).endswith(".tar.bz2"):
            yield pkgfile


def get_channel_from_package_filepath(package_path: pathlib.Path) -> str:
    """
    Checks if the unpacked directory of a package still exists and
    retrieves channel from package directory.
    :param package_path: Path to the .tar.bz2
    :return: Channel string or unknown, if impossible to get.
    """
    strpath = str(package_path)
    assert strpath.endswith(".tar.bz2")
    strpath = strpath[:-8]
    package_path_without_tar_bz2 = pathlib.Path(strpath)
    if not package_path_without_tar_bz2.is_dir():
        # In this case we don't have the unpacked directory anymore.
        # Download source info is lost
        return "unknown"
    repodata_path = package_path_without_tar_bz2 / "info" / "repodata_record.json"
    with repodata_path.open("rt") as infile:
        repodata = json.load(infile)
    channel = repodata["channel"]
    # We remove subdir from channel to get a valid repostructure
    subdir = repodata["subdir"]
    if channel.endswith(f"/{subdir}"):
        channel = channel[0 : -len(subdir) - 1]
    return channel


def get_subdir_from_package_index(package_index: Dict[str, str]) -> str:
    """
    Retrieves subdir from package index, trivial function.
    Returns one of noarch, linux-64, etc.
    :param package_index: conda package index file
    :return: the architecture, i.e. subdir
    """
    return package_index["subdir"]


def get_package_name_from_package_index(package_index: Dict[str, str | Dict]) -> str:
    """
    Gets the package name from the conda index file, as specified here:
    Implementation according to: https://docs.conda.io/projects/conda-build/en/latest/concepts/package-naming-conv.html
    :param package_index: Conda package index dictionary
    :return: Expected name of package on filesystem
    """
    package_name = package_index["name"]
    version = package_index["version"]
    build_string = package_index["build"]
    filename = f"{package_name}-{version}-{build_string}.tar.bz2"
    return filename


def get_conda_package_index(package_path: pathlib.Path) -> Dict[str, str]:
    """
    Extracts info/index.json, parses it and gives it back
    :param package_path: Path to a conda .tar.bz2 package
    :return: dict containing the parse package index
    """
    with package_path.open("rb") as infile:
        with tarfile.open(mode="r", fileobj=infile) as tar:
            binary_content = tar.extractfile("info/index.json").read() # type: ignore
    text_content = binary_content.decode("utf8")
    indexjson = json.loads(text_content)
    return indexjson


def normalize_channel_name(channel: str) -> str:
    """
    Cuts http(s):// and trailing /, replaces slashes
    :param channel:
    :return:
    """
    tocut_front = ["http://", "https://"]
    for tcf in tocut_front:
        if channel.startswith(tcf):
            channel = channel[len(tcf) :]
    tocut_back = ["/"]
    for tcb in tocut_back:
        if channel.endswith(tcb):
            channel = channel[0 : -len(tcb)]
    replace = {"/": "_"}
    for rep, rep_to in replace.items():
        channel = channel.replace(rep, rep_to)

    return channel


def rewrite_pkgs_dir_to_repo(pkgdir: pathlib.Path, repodir: pathlib.Path) -> None:
    """
    Iterates over all pkgs in pkgdir and tries to create multiple repository filestructures in repodir
    according to the specifications found in pkgdir. Afterwards running conda index in those directories
    should yield cache copies containing repositories with packages actually downloaded for air-gap
    conda installers
    :param pkgdir: package directory in a normal conda install
    :param repodir: target directory for the eventual repository. Does not need to be empty
    """
    for pkg in walk_package_dir_iterator(pkgdir):
        try:
            package_index = get_conda_package_index(pkg)
            subdir = get_subdir_from_package_index(package_index)
            channel = normalize_channel_name(get_channel_from_package_filepath(pkg))
            package_name = get_package_name_from_package_index(package_index) # type: ignore
            outdir = repodir / channel / subdir
            os.makedirs(outdir, exist_ok=True)
            tofile = outdir / package_name
            shutil.copy(pkg, tofile)
        except tarfile.ReadError:
            print(f"Could not read {pkg}")


@click.command
@click.option(
    "--pkg-dir",
    help="Source pkgs directory from an existing Conda or Mamba installation",
    required=True,
)
@click.option(
    "--target-dir",
    help="Target directory to create file repositories in",
    required=True,
)
def main(pkg_dir: str, target_dir: str):
    """Converts conda pkgs directory in file repository structures indexable by conda index"""
    rewrite_pkgs_dir_to_repo(pathlib.Path(pkg_dir), pathlib.Path(target_dir))


if __name__ == "__main__":
    main()
