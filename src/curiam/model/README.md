# Model
Source code for the BERT and LEGAL-BERT models described in the paper.

## Training
### Multirun
To train all models, run:
```
$ python scripts/train.py
```

This training script makes use of [Hydra](https://hydra.cc) to manage experiments, and the default config file is [all_experiments.yaml](../../../scripts/config/all_experiements.yaml). Hydra reads the possible experiment settings from this file and will sweep over all combinations those settings. In other words, it will automatically run the training script multiple times (serially) with the different settings.

### Single Experiment
If you only want to run a single experiment, you can pass in an alternate configuration file with  ``--config-name`` argument for an alternate configuration file, like so:

```
$ python scripts/train.py --config-name single_experiment
```
