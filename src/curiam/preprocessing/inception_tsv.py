"""Functions for processing the TSV-formatted data exported from Inception."""

from pathlib import Path
from typing import Tuple

from curiam.document import Document, Sentence, Token, TokenAnnotation


def split_complex_label(complex_label: str) -> Tuple[list[str], list[str]]:
    """Splits a complex token label into categories and token indexes.

    Example: "Example Use[56]|Direct Quote[58]" returns
    (["Example Use", "Direct Quote"], [56, 58]).

    If an annotation isn't indexed, it only covers a single token and there's
    only one annotation on that token. These are given these an annotation
    index of -1.

    Single-token spans on a token with multiple annotations do get indexed.

    Args:
        label: A pipe-separated string of annotations. A single annotation
          is the category followed by its index in square brackets.

    Returns:
        A list of categories and a list of corresponding indexes.
    """

    sublabels = complex_label.split("|")
    categories = []
    annotation_indexes = []
    for sublabel in sublabels:
        if "[" not in sublabel:
            categories.append(sublabel)
            annotation_indexes.append(-1)
        else:
            # Remove the close bracket and then split on the open bracket
            sublabel = sublabel.replace("]", "")
            category, annotation_index = sublabel.split("[")
            annotation_index = int(annotation_index)
            categories.append(category)
            annotation_indexes.append(annotation_index)
    return categories, annotation_indexes


def process_sentence(tsv_rows: list) -> Sentence:
    """Parses TSV rows representing tokens into a `Sentence`.

    Args:
        tsv_rows: a list of tab-separated strings read from INCEpTION's TSV
          export format.

    Returns:
        A `Sentence`.
    """
    sentence = Sentence()
    index_offset = None
    for i, row_string in enumerate(tsv_rows):
        row = row_string.split("\t")
        sentence.id = row[0][:row[0].index("-")]
        text = row[2]  # Column 3 is annotation notes, which we don't need
        complex_label = row[4]
        if complex_label == "_":  # Token with no annotations
            sentence.append(Token(text=text, id=i))
        elif "*" in complex_label:  # Token no category (ignore these, but warn)
            # I think these are tokens that didn't get annotated with a category, but do have a note
            print(f"Warning: token '{text}' has label {complex_label} and note: {row[3]}")
            sentence.append(Token(text=text, id=i))
        else:
            categories, annotation_ids = split_complex_label(complex_label)
            if index_offset is None and annotation_ids[0] != -1:
                index_offset = annotation_ids[0]
            for j, annotation_id in enumerate(annotation_ids):
                if annotation_id == -1:
                    continue
                else:
                    annotation_ids[j] = annotation_id - index_offset

            annotations = []
            for category, annotation_id in zip(categories, annotation_ids):
                annotations.append(TokenAnnotation(category=category,
                                                   id=annotation_id))
            sentence.append(Token(text=text,
                                  id=i,
                                  annotations=annotations))
    return sentence


def process_opinion_file(opinion_path: Path, name: int) -> Document:
    """Parses a TSV export from INCEpTION and returns a document."""

    with opinion_path.open("r", encoding="utf-8") as f:
        data = f.readlines()

    # Make sure sentences start in expected place
    assert data[4].startswith("#Text")

    opinion = Document(name=name)
    sentence_rows = []
    sentence_id = 0
    for row in data[4:]:
        # This indicates the start of a new sentence,
        # but we don't need to do anything with this line
        if row.startswith("#Text"):
            sentence_rows = []  # Reset sentence rows

        # End of sentence reached
        elif row == "\n":
            sentence = process_sentence(sentence_rows)
            sentence.id = sentence_id
            opinion.append(sentence)
            sentence_id += 1

        # Token row
        else:
            sentence_rows.append(row)

    return opinion
