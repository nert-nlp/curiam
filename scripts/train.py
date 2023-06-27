from pathlib import Path

from curiam.model import runner
from curiam.model.config import TrainingConfig
from curiam.model.load_data import dataloader_from_dataset, dataset_from_files
from curiam.model.load_data import k_fold_files
from curiam.model.model import get_model

import hydra

from hydra.core.config_store import ConfigStore

from accelerate import Accelerator
from torch.optim import AdamW
from torch.utils.tensorboard import SummaryWriter
from transformers import BertTokenizerFast
from transformers import get_scheduler

cs = ConfigStore.instance()
cs.store(name="training_config", node=TrainingConfig)
config_name = "config"


@hydra.main(version_base=None, config_path="config", config_name=config_name)
def train(config: TrainingConfig):
    print(config)

    opinion_paths = list(Path("data/full_scale/annotated").glob("*.tsv"))
    train_filepaths, test_filepaths = k_fold_files(opinion_paths,
                                                   test_fold_id=config.experiment.fold_id,
                                                   k=4)

    assert len(set(train_filepaths).intersection(set(test_filepaths))) == 0
    do_lower = config.experiment.model_checkpoint == "nlpaueb/legal-bert-base-uncased"
    tokenizer = BertTokenizerFast.from_pretrained(config.experiment.model_checkpoint)

    train_dataset = dataset_from_files(train_filepaths,
                                       config.experiment.category,
                                       tokenizer=tokenizer,
                                       do_lowercase=do_lower,
                                       eval=False)
    test_dataset = dataset_from_files(test_filepaths,
                                      config.experiment.category,
                                      tokenizer=tokenizer,
                                      do_lowercase=do_lower,
                                      eval=True)
    train_loader = dataloader_from_dataset(train_dataset,
                                           tokenizer=tokenizer,
                                           batch_size=config.hyperparams.batch_size)
    test_loader = dataloader_from_dataset(test_dataset,
                                          tokenizer=tokenizer,
                                          batch_size=config.hyperparams.batch_size)

    model = get_model(config.experiment.category,
                      config.experiment.model_checkpoint)

    optimizer = AdamW(model.parameters(), lr=config.hyperparams.learning_rate)
    accelerator = Accelerator()
    model, optimizer, train_loader, test_loader = accelerator.prepare(
        model, optimizer, train_loader, test_loader)

    num_update_steps_per_epoch = len(train_loader)
    num_training_steps = config.hyperparams.epochs * num_update_steps_per_epoch

    lr_scheduler = get_scheduler("linear",
                                 optimizer=optimizer,
                                 num_warmup_steps=0,
                                 num_training_steps=num_training_steps)

    if config.experiment.model_checkpoint == "bert-base-cased":
        short_model_name = "bert"
    else:
        short_model_name = "legal-bert"

    tensorboard_writer = SummaryWriter(f"results/runs/{config.experiment.category}_" +
                                       f"{short_model_name}_fold_{config.experiment.fold_id}")

    # Create runners
    train_runner = runner.Runner(train_loader, model, accelerator,
                                 optimizer=optimizer, scheduler=lr_scheduler,
                                 writer=tensorboard_writer)
    test_runner = runner.Runner(test_loader, model, accelerator,
                                writer=tensorboard_writer)

    # Early stopping
    lowest_loss = 1_000_000
    num_insufficiently_improved = 0

    # Training loop
    for epoch_id in range(config.hyperparams.epochs):
        # Train for 1 epoch and then eval on a subset of the test data
        training_loss = train_runner.run_training_epoch(epoch_id)
        p, r, f1, test_subset_loss = test_runner.run_eval_epoch(test_set_portion=.25)
        global_step = (epoch_id + 1) * len(train_runner.loader)
        test_runner.writer.add_scalar("Test Subset/Loss", test_subset_loss, global_step)
        test_runner.writer.add_scalar("Test Subset/Precision", p, global_step)
        test_runner.writer.add_scalar("Test Subset/Recall", r, global_step)
        test_runner.writer.add_scalar("Test Subset/F1", f1, global_step)

        if training_loss > lowest_loss - .001:
            num_insufficiently_improved += 1
        else:
            lowest_loss = training_loss
        if num_insufficiently_improved >= 3:
            break

    # Evaluate on the whole test set
    p, r, f1, _ = test_runner.run_eval_epoch()
    test_runner.writer.add_text("Full test metrics", f"Precision: {p}, Recall: {r}, F1: {f1}")
    test_runner.writer.add_text("Training epochs", f"Training stopped after epoch {epoch_id}")


if __name__ == "__main__":
    train()
