# CondaPkgDirToRepo

This repo allows to reconstruct a folder hierarchy for a repository based on an installed package directory. This is not a supported Anaconda project, but rather something we ([Nanomatch GmbH](https://www.nanomatch.de)) use in-house to generate air-gapped conda-forge repositories containing only the packages we use.

### Usage

* Install a clean [Mambaforge](https://github.com/conda-forge/miniforge) in a throwaway directory. Miniconda and Miniforge should also work, but we never tested them.
* Install your packages or install your environment file

    mamba env create -f yourenvfile.yml
* Run
    
    CondaPkgDirToRepo --pkg-dir /path/to/your/conda/pkgs --target-dir /any/empty/folder

If you did not install this package, you can also use it directly:

    /path/to/repo/CondaPkgDirToRepo/CondaPkgDirToRepoMain.py --pkg-dir /path/to/your/conda/pkgs --target-dir /any/empty/folder

It will result in a package hierachy like this:

* conda.anaconda.org\_conda-forge/{noarch, linux-64}
* conda.anaconda.org\_otherchannel/{noarch}
* notexistprivaterepo\_yourchannel/noarch

Usually there is also a folder conda-forge/noarch ..., which in my experience contains the files, which were bundled in the mambaforge installer. For our air-gapped installed, we delete this and provide the installer.

To use these as repositories you will need to run conda index in each created directory. Afterwards you can specify them using

    
    -c file:///absolute/path/to/channel

### Limitations

* Only works with .tar.bz2 packages
* Does not work if package cache was previously emptied

### Alternatives
Alternatives are:

* [conda-pack](https://conda.github.io/conda-pack/): Best alternative. Works well to pack an environment without hassle. Does not allow updating this environment by updating the air-gapped package cache. Basically requires transfering the whole env again.
* *Packing the pkgs folder and unzipping, then installing*: Works, but does not maintain the repo priority hierarchy
* *Downloading and picking all .tar.bz2 packages manually*: How we did it before and absolutely not scalable.



### Disclaimer
This project is not supported by Anaconda. It can break at any time, if package formats, package hierarchies, etc. change.
