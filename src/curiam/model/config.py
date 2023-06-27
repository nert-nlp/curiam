"""Configuration object for Hydra."""

from dataclasses import dataclass


@dataclass
class Experiment:
    category: str
    fold_id: str
    model_checkpoint: str


@dataclass
class Hyperparams:
    epochs: int
    learning_rate: int
    batch_size: int


@dataclass
class TrainingConfig:
    experiment: Experiment
    hyperparams: Hyperparams
