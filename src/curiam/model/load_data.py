import copy
import random
from pathlib import Path
from typing import Tuple

import numpy as np
from datasets import ClassLabel, Dataset, Features, Value, Sequence
from torch.utils.data import DataLoader
from transformers import BertTokenizerFast
from transformers import DataCollatorForTokenClassification

from curiam.preprocessing import inception_tsv
from curiam import categories


def shuffle_opinions(opinion_filepaths: list[Path]) -> list[Path]:
    """Shuffles document names deterministically.

    Args:
        opinion_filepaths: A list of opinion filepaths.

    Returns:
        A shuffled copy of the input list.
    """

    # For safety, make sure seed is consistent and copy so that
    # we're not producing side effects.
    opinion_filepaths_copy = copy.deepcopy(opinion_filepaths)
    random.seed(42)
    random.shuffle(opinion_filepaths_copy)
    return opinion_filepaths_copy


def k_fold_files(opinion_paths: list,
                 test_fold_id: int = 0, k: int = 4) -> Tuple[list, list]:

    """Splits list of paths and returns training paths and test paths.

    Reinventing the wheel here because we're trying to do k-fold
    cross-validation at document level instead of sentence level.

    Args:
        opinion_paths: Filepaths to be split into test and train groups.
        test_fold_id: Identifier in [0,k) that specifies\
            which fold to use for eval/test.
        k: Number of folds for cross-validation.

    Returns:
        training_paths, test_paths
    """

    shuffled_doc_names = shuffle_opinions(opinion_paths)
    folds = np.array_split(shuffled_doc_names, k)
    test_paths = folds.pop(test_fold_id)
    training_paths = list(np.concatenate(folds))
    return training_paths, test_paths


def get_masked_wordpiece_labels(labels: list, word_ids: list) -> list:
    """Returns masked labels for wordpiece tokens.

    The first subword of each token retains the original token label and
    remaining subwords for that token are set to -100.

    Special tokens like CLS and SEP also get a label of -100.

    Subwords with value of -100 will not be included in loss calculation.
    """

    masked_labels = []
    current_word = None
    for word_id in word_ids:
        # Special tokens (CLS and SEP) don't have a word_id
        if word_id is None:
            masked_labels.append(-100)
        # Start of a new word
        elif word_id != current_word:
            current_word = word_id
            label = labels[word_id]
            masked_labels.append(label)
        # Non-first subword of token
        else:
            masked_labels.append(-100)

    return masked_labels


def tokenize_and_mask_labels(examples, tokenizer: BertTokenizerFast):
    """Tokenizes examples and mask associated labels to accomodate wordpiece."""

    tokenized_inputs = tokenizer(examples["tokens"], truncation=True,
                                 is_split_into_words=True)
    all_labels = examples["category_tags"]
    masked_labels = []
    for i, labels in enumerate(all_labels):
        word_ids = tokenized_inputs.word_ids(i)
        masked_labels.append(get_masked_wordpiece_labels(labels, word_ids))
    tokenized_inputs["labels"] = masked_labels
    return tokenized_inputs


def dataset_from_files(filepaths: list[Path], category: str,
                       tokenizer: BertTokenizerFast,
                       do_lowercase: bool) -> Dataset:
    """Reads data from files and featurize into dataset."""

    opinions = [inception_tsv.process_opinion_file(filepath, filepath.name, "Michael")
                for filepath in filepaths]

    # Get sentences (lists of token strings) and binary labels for each token for the given category

    dataset_sentences = []
    dataset_labels = []

    for opinion in opinions:
        for sentence in opinion:
            dataset_sentences.append([token.text.lower() if do_lowercase
                                      else token.text for token in sentence])
            dataset_labels.append([1 if category in token.get_categories()
                                   else 0 for token in sentence])

    names = get_pretty_label_names(category)

    features = Features(
        {"tokens": Sequence(
            feature=Value(dtype='string', id=None),
            length=-1, id=None),
         "category_tags": Sequence(
             feature=ClassLabel(num_classes=2, names=names),
             length=-1, id=None)})

    tokens_and_tags = {"tokens": dataset_sentences, "category_tags": dataset_labels}
    dataset = Dataset.from_dict(tokens_and_tags, features=features)

    tokenized_dataset = dataset.map(tokenize_and_mask_labels, batched=True,
                                    remove_columns=dataset.column_names,
                                    fn_kwargs={"tokenizer": tokenizer})

    return tokenized_dataset


def get_pretty_label_names(category: str) -> list[str]:
    """Returns pretty negative and positive label names for a category.

    Example: "Direct Quote" -> ["NOT DQ", "DQ"]

    Args:
        category: Unabbreviated category name.
    """

    category_abbrevation = categories.CATEGORIES_TO_ABBREVIATIONS[category]
    names = [f"NOT {category_abbrevation}", category_abbrevation]
    return names


def dataloader_from_dataset(dataset: Dataset, tokenizer: BertTokenizerFast,
                            batch_size: int) -> DataLoader:
    """Returns a dataloader for a preprocessed dataset."""

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer,
                                                       padding=True)

    dataloader = DataLoader(dataset, shuffle=True,
                            collate_fn=data_collator,
                            batch_size=batch_size)
    return dataloader
