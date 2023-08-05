"""Lightweight data models for tokens, sentences, annotations, and documents."""

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class TokenAnnotation:
    """An annotation for a single token.

    Attributes:
        category: The category/label of the annotation.
        id: An int indicating this is the i-th annotation in the sentence. Starts at 0.
          This id is used to distinguish overlapping or neighboring annotations.
          Single-token annotations get an id of -1. DO NOT use ids to count annotations.
    """
    id: int
    category: str

    def to_json(self) -> dict:
        return dict(id=self.id, category=self.category)


@dataclass
class Annotation:
    """An annotation described in terms of its starting and end indexes.

    `end` is inclusive, so a single-token annotation will have the same start
    and end index.

    Attributes:
        category: The category/label of the annotation.
        start: The index of the first token covered by the annotation.
        end: The index of the last token covered by the annotation.
    """
    category: str
    start: int
    end: int = None


@dataclass
class Token:
    """Representation of a token.

    Attributes:
        text: The string representation of the token.
        id: A zero-indexed int indicating the position of the token in the sentence.
        annotations: `Annotation`s for the token.
    """
    id: int
    text: str
    annotations: list[TokenAnnotation] = None

    def get_categories(self) -> set[str]:
        categories = set()
        for token_annotation in self.annotations:
            categories.add(token_annotation.category)
        return categories

    def to_json(self) -> dict:
        result = dict(id=self.id, text=self.text)
        if self.annotations is not None:
            result["annotations"] = self.annotations
        return result


@dataclass
class Sentence:
    """Representation of a sentence.

    Attributes:
        id: A 0-indexed int indicating this is the i-th sentence in a `Document`.
        tokens: A list of `Token`s in the sentence.
    """
    id: int = None
    tokens: list[Token] = field(default_factory=list)

    def append(self, token: Token):
        self.tokens.append(token)

    def __iter__(self) -> Iterator[Token]:
        return iter(self.tokens)

    def __len__(self) -> int:
        return len(self.tokens)

    def __str__(self) -> str:
        return str([tok.text for tok in self.tokens])

    def to_json(self) -> dict:
        return dict(id=self.id, tokens=self.tokens)

    def get_annotations(self) -> list[Annotation]:
        """Reads `TokenAnnotations` from each token and returns a list of `Annotation`s.

        Allows for analyis of annotations at a sentence level.
        """

        annotations = []
        indexed_annotations = {}
        for token in self.tokens:
            for token_annotation in token.annotations:
                if token_annotation.id == -1:  # Single-token annotation
                    annotations.append(Annotation(category=token_annotation.category,
                                                  start=token.id,
                                                  end=token.id))
                else:
                    if token_annotation.id not in indexed_annotations.keys():
                        annotation = Annotation(token_annotation.category,
                                                start=token.id,
                                                end=token.id)
                        indexed_annotations[token_annotation.id] = annotation
                    else:
                        # Update the annotation's end index the next time it's seen
                        indexed_annotations[token_annotation.id].end = token.id
        for annotation in indexed_annotations.values():
            annotations.append(annotation)
        return annotations


@dataclass
class Document:
    """Representation of a document.

    Attributes:
        sentences: A list of `Sentence`s.
    """
    name: str
    sentences: list[Sentence] = field(default_factory=list)

    def append(self, sentence):
        self.sentences.append(sentence)

    def __iter__(self) -> Iterator[Sentence]:
        return iter(self.sentences)

    def __len__(self) -> int:
        return len(self.sentences)

    def to_json(self):
        return dict(name=self.name, sentences=self.sentences)
