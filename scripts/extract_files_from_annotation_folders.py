"""Copies files in each annotation folder into one folder.

INCEpTION puts the annotations for each doument into a document-specific folder.

This script takes a source folder (the folder with all the document-specific
folders) and copies all of the TSV files out.

"""

import shutil


from pathlib import Path

annotation_export_dir = Path("data/full_scale/annotated/inception_export_06_19_23")
dirs = [x for x in annotation_export_dir.iterdir() if x.is_dir()]


for dir in dirs:
    if Path.exists(dir.joinpath("admin.tsv")):
        # Folders are named after the file that was imported to INCEpTION
        # so they will have .txt suffixes
        # Take just the stem of the folder name and add .tsv suffix
        shutil.copy(dir.joinpath("admin.tsv"), Path("data", "full_scale", "annotated", dir.stem + ".tsv"))
