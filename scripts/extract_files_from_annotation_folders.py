"""Copies files from each annotation folder into one folder.

INCEpTION puts the annotations for each document into a document-specific folder.

This script takes a source folder (the folder with all the document-specific
folders) and copies out all of the TSV files for the admin user.

Scenario:
- Import 'somefile.txt' into INCEpTION
- Users 'bob' and 'alice' annotate the document.
- Upon export (with TSV format), a folder named 'somefile.txt' is created.
- This folder contains 'bob.tsv' and 'alice.tsv'

In this case, annotations are done under the admin account, so this script
copies all of the 'admin.tsv' annotation files from each opinion and gives them
more specific filenames.
"""

import shutil
from pathlib import Path

annotation_export_dir = Path("data/main/annotated/inception_export_06_19_23")
dirs = [x for x in annotation_export_dir.iterdir() if x.is_dir()]

for dir in dirs:
    if Path.exists(dir.joinpath("admin.tsv")):
        shutil.copy(src=dir.joinpath("admin.tsv"),
                    dst=Path(f"data/main/annotated/{dir.stem}.tsv"))
