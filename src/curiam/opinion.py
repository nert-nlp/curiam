"""Definitions for tokens, sentences, and opinions."""

from dataclasses import dataclass


@dataclass
class Token:
    text: str
    categories: list
    annotation_indexes: list


@dataclass
class Sentence:
    tokens: list[Token]


@dataclass
class Opinion:
    sentences: list[Sentence]
