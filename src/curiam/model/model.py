"""Retrieves a pretrained model from a checkpoint name."""

from transformers import BertForTokenClassification
from curiam.model.load_data import get_pretty_label_names


def get_model(category: str,
              model_checkpoint: str) -> BertForTokenClassification:
    """Gets a BertForTokenClassification model.

    Args:
        category: e.g., "Focal Term". Used to specify labels for the model.
        model_checkpoint: A Huggingface transformers checkpoint.
    """
    label_names = get_pretty_label_names(category)
    id2label = {i: label for i, label in enumerate(label_names)}
    label2id = {v: k for k, v in id2label.items()}
    model = BertForTokenClassification.from_pretrained(model_checkpoint,
                                                       id2label=id2label,
                                                       label2id=label2id)
    return model
