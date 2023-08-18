"""Exports the corpus to corpus/corpus.json.

Usage: `python scripts/save_corpus_to_json.py`
"""
import json
from pathlib import Path

from curiam.preprocessing import inception_tsv


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return obj.to_json()
        else:
            return json.JSONEncoder.default(self, obj)


# Serialization: https://stackoverflow.com/questions/5160077/encoding-nested-python-object-in-json
opinions_dir = Path("data/main/annotated")
opinions = [inception_tsv.process_opinion_file(opinion_path, opinion_path.name)
            for opinion_path in sorted(opinions_dir.glob("*.tsv"), key=lambda path: path.name)]
with open("corpus/corpus.json", "w", encoding="utf-8") as f:
    json.dump(opinions, f, cls=JSONEncoder)
