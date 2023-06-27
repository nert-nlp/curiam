from transformers import BertForTokenClassification
from curiam.model.load_data import get_pretty_label_names


def get_model(category, model_checkpoint):
    label_names = get_pretty_label_names(category)
    id2label = {i: label for i, label in enumerate(label_names)}
    label2id = {v: k for k, v in id2label.items()}
    model = BertForTokenClassification.from_pretrained(model_checkpoint,
                                                       id2label=id2label,
                                                       label2id=label2id)
    return model
