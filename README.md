# CuRIAM

Corpus data, models, and analysis for CuRIAM.

![Annotation example](example.png)

CuRIAM stands for Corpus re Interpretation and Metalanguage. For information about the corpus, see the paper.

 paper (arXiv): [_Corpus re Interpretation and Metalanguage in Supreme Court Opinions_](https://arxiv.org/abs/2305.14719)



## Corpus Data
The full corpus data is available [here](/corpus/).

## Setup
This repo has been tested in WSL on Windows and on MacOS. 



1. Create a conda environment.

    If using WSL or bare-metal linux,
    create a conda environment with the default `environment.yml` file.

    ```
    $ conda env create -f environment.yml
    $ conda activate curiam
    ```

    If you're on MacOS with Apple silicon, use `environment_apple_silicon.yml`.

    Unfortunately, training the models in this repo is not practical without GPU acceleration.

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

    Installing `pygamma-agreement` for Apple silicon is difficult. Intalling `cvxopt` via conda and then `pip install pygamma-agreement` without cbc may work, but I haven't tested it. If it does work, it may be slow.

## Acknowledgments
---
TODO

## License
---
TODO