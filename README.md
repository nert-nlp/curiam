# CuRIAM

Corpus data, models, and analysis for _Corpus re Interpretation and Metalanguage in Supreme Court Opinions_.

![Annotation example](example.png)

## Corpus Data
The full corpus data is available [here](/corpus/).

## Setup
1. Create a conda environment.

```
$ conda env create -f environment.yml
$ conda activate curiam
```
2. Install the `curiam` package locally.
```
$ pip install --upgrade build
$ pip install -e .
```

3. If you plan on running the gamma agreement calculations, install [pygamma-agreement](https://pypi.org/project/pygamma-agreement/) separately.

```
$ sudo apt-get update
$ sudo apt install coinor-libcbc-dev
$ pip install "pygamma-agreement[cbc]"
```

## Acknowledgments
---
TODO

## License
---
TODO