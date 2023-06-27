import statistics

from typing import Any, Optional

import evaluate
import torch
from tqdm import tqdm

from torch.utils.data.dataloader import DataLoader
from accelerate import Accelerator
from transformers import BertForTokenClassification
from torch.utils.tensorboard import SummaryWriter


class Runner:
    def __init__(self,
                 loader: DataLoader[Any],
                 model: BertForTokenClassification,
                 accelerator: Accelerator,
                 optimizer: Optional[torch.optim.Optimizer] = None,
                 scheduler=None,
                 writer: SummaryWriter = None
                 ):
        self.loader = loader
        self.model = model
        self.accelerator = accelerator
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.writer = writer
        self.mode = "eval" if optimizer is None else "train"
        self.precision_metric = evaluate.load("precision")
        self.recall_metric = evaluate.load("recall")
        self.f1_metric = evaluate.load("f1")

    def run_training_epoch(self, epoch_id):
        if self.mode == "train":

            losses = []
            self.model.train()
            for i, batch in enumerate(tqdm(self.loader, ncols=80)):
                batch_loss = self._run_training_batch(batch, i, epoch_id)
                losses.append(batch_loss)
            average_loss_for_epoch = statistics.mean(losses)
            self.writer.add_scalar("Training/Epoch loss", average_loss_for_epoch,
                                   (epoch_id + 1) * len(self.loader))
            return average_loss_for_epoch

    def run_eval_epoch(self, test_set_portion: int = 1):
        self.model.eval()
        stopping_point = int(len(self.loader) * test_set_portion)
        losses = []
        with torch.no_grad():
            for batch in tqdm(list(self.loader)[:stopping_point], ncols=80):
                batch_loss = self._run_eval_batch(batch)
                losses.append(batch_loss)
            p = self.precision_metric.compute()["precision"]
            r = self.recall_metric.compute()["recall"]
            f1 = self.f1_metric.compute()["f1"]

        average_loss_for_epoch = statistics.mean(losses)

        return p, r, f1, average_loss_for_epoch

    def _run_training_batch(self, batch, i, epoch_id):
        outputs = self.model(**batch)
        loss = outputs.loss
        offset = len(self.loader) * epoch_id
        self.writer.add_scalar("Training/Loss for all batches", loss, offset + i)
        self.accelerator.backward(loss)
        self.optimizer.step()
        self.scheduler.step()
        self.optimizer.zero_grad()
        return loss.item()

    def _run_eval_batch(self, batch):
        outputs = self.model(**batch)
        loss = outputs.loss
        predictions = outputs.logits.argmax(dim=-1)
        labels = batch["labels"]

        predictions = self.accelerator.pad_across_processes(predictions, dim=1,
                                                            pad_index=-100)
        labels = self.accelerator.pad_across_processes(labels, dim=1,
                                                       pad_index=-100)

        predictions_gathered = self.accelerator.gather(predictions)
        labels_gathered = self.accelerator.gather(labels)

        filtered_predictions, filtered_labels = postprocess(predictions_gathered,
                                                            labels_gathered)
        self.precision_metric.add_batch(predictions=filtered_predictions,
                                        references=filtered_labels)
        self.recall_metric.add_batch(predictions=filtered_predictions,
                                     references=filtered_labels)
        self.f1_metric.add_batch(predictions=filtered_predictions,
                                 references=filtered_labels)
        return loss.item()


def postprocess(predictions, labels):
    predictions = predictions.detach().cpu().clone().numpy()
    labels = labels.detach().cpu().clone().numpy()

    # Remove ignored index (special tokens) and convert to labels
    filtered_labels = [[y for y in label if y != -100] for label in labels]
    filtered_predictions = [
        [p for (p, y) in zip(prediction, label) if y != -100]
        for prediction, label in zip(predictions, labels)]

    flat_labels = [item for sublist in filtered_labels
                   for item in sublist]
    flat_predictions = [item for sublist in filtered_predictions
                        for item in sublist]
    return flat_labels, flat_predictions
