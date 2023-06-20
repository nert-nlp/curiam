"""Functions for processing the TSV-formatted data exported from Inception."""

from pathlib import Path
from typing import Tuple


def split_compound_label(compound_label: str) -> Tuple[list[str], list[str]]:
    """Splits a compound token label into categories and token indexes.

    Example: ["Example Use[56]|Direct Quote[58]"] returns
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

    sublabels = compound_label.split("|")
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


def process_sentence(tsv_rows: list) -> list[list]:
    """Parses TSV rows for sentence tokens into a simpler format.

    Reindexes annotations from document level to sentence level. Single-token
    annotations (where that token only has 1 annotation)retain their -1 index.

    Example: "Direct Quote[82]|Direct Quote[83]" is a label for a token that
    is part of a nested direct quote. Assuming 82 is the first annotation
    of the sentence, the resulting token label will will be:

    {"categories": ["Direct Quote", "Direct Quote"],
     "indexes": [1, 2]}

    Each token's labels are represented as a dictionary containing "categories"
    and "indexes" which identify which categories the token has been annotated
    with and which annotation it is part of in the sentence.

    Args:
        tsv_rows: a list of tab-separated strings read from INCEpTION's TSV
          export format.

    Returns:
        A list of tokens represented as a list:
          [sentence_number, token, labels]
    """

    simplified_tokens = []
    index_offset = None  # For re-indexing to sentence instead of document
    for row_string in tsv_rows:
        row = row_string.split("\t")
        # 0-th cell has sent num and token num separated by hyphen
        sent_num = row[0][:row[0].index("-")]
        token = row[2]  # Column 3 is annotation notes, which we don't need
        label = row[4]
        empty_label_dict = {"categories": [], "indexes": []}
        if label == "_":  # Token with no annotations
            simplified_tokens.append([sent_num, token, empty_label_dict])
        elif label == "*":  # Token no category (ignore these, but warn)
            print(f"Warning: token '{token}' has label * and note: {row[3]}")
            simplified_tokens.append([sent_num, token, empty_label_dict])
        else:
            categories, annotation_indexes = split_compound_label(label)
            if index_offset is None:
                index_offset = annotation_indexes[0] - 1
            label_dict = {"categories": [], "indexes": []}
            for category, index, in zip(categories, annotation_indexes):
                label_dict["categories"].append(category)
                if index == -1:
                    label_dict["indexes"].append(index)
                else:
                    label_dict["indexes"].append(index - index_offset)
            simplified_tokens.append([sent_num, token, label_dict])
    return simplified_tokens


def process_opinion_file(opinion_path: Path) -> list:
    """Parses a TSV export from Inception.

    Returns a list of lists of tokens (i.e. a list of sentences).

    Tokens are represented as simplified TSV rows containing the sentence
    number, the token string, and the token's annotated labels."""

    with opinion_path.open("r", encoding="utf-8") as f:
        data = f.readlines()

    # Make sure sentences start in expected place
    assert data[4].startswith("#Text")

    opinion = []  # This will be a list of sentences, which are lists of tokens
    sentence_rows = []
    for row in data[4:]:
        # This indicates the start of a new sentence,
        # but we don't need to do anything with this line
        if row.startswith("#Text"):
            sentence_rows = []

        # End of sentence reached
        elif row == "\n":
            simplified_tokens = process_sentence(sentence_rows)
            opinion.append(simplified_tokens)

        # Token row
        else:
            sentence_rows.append(row)

    return opinion


def get_sentence_annotations(sentence: list, annotation_column: int = 2) -> list[list]:
    """Gets the annotations in a sentence.

    Each annotation is represented as a list:
    [category, start_token_index, stop_token_index]

    Args:
        sentence: a list of simplified token rows from process_sentence.
        annotation_column: Michael's annotations are in column 2
          and Nathan's are in column 3.

    Returns:
        A list of lists, where each sublist contains the category of the
        annotation, the start token index for the annotation, and the end token
        index for the annotation.
    """
    annotations = []

    # Annotations already have indexes indicating they are the i-th annotation
    # in a sentence. Here, we're adding start and stop indexes to indicate
    # which tokens each annotation covers.
    indexed_annotations = {}
    for i, token in enumerate(sentence):
        label_dict = token[annotation_column]
        if len(label_dict["categories"]) == 0:  # No annotation
            continue
        # Single-token annotations
        elif len(label_dict["categories"]) == 1 and label_dict["indexes"][0] == -1:
            category = label_dict["categories"][0]
            annotations.append([category, i, i])
        else:
            # Identify annotations by category and index in the sentence
            for category, index in zip(label_dict["categories"],
                                       label_dict["indexes"]):
                unique_annotation = f"{category}:{index}"
                # Add annotation to list of indexed annotations with start and
                # stop indexes
                if unique_annotation not in indexed_annotations.keys():
                    indexed_annotations[unique_annotation] = [category, i, i]
                # Update the end index the next time we see this annotation
                else:
                    indexed_annotations[unique_annotation][2] = i
    for indexed_annotation in indexed_annotations.values():
        annotations.append(indexed_annotation)
    return annotations
