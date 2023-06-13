# CuRIAM
Materials and Analysis for "Corpus re Interpretation and Metalanguage in Supreme Court Opinions"

After creating the environment,

```
$ conda env create -f environment.yml
$ conda activate curiam
```
Install the package with:
```
$ pip install --upgrade build
$ pip install -e .
```

If you plan on running the gamma agreement numbers, install [pygamma-agreement](https://pypi.org/project/pygamma-agreement/) separately:

```
$ sudo apt-get update
$ sudo apt install coinor-libcbc-dev
$ pip install "pygamma-agreement[cbc]"
```