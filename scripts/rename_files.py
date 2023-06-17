"""Renames opinion files to start with docket number instead of Harverd CAP case ID/"""

import os
import shutil # noqa401

from curiam import cap_parsing

for filename in os.listdir("data/full_scale/raw/inception_files"):
    if filename.endswith(".txt"):
        # Case ID is everything before first underscore
        first_underscore_index = filename.index("_")
        case_id = filename[:first_underscore_index]
        docket_number = cap_parsing.get_docket_number_from_id(case_id)
        new_folder = "data/full_scale/processed/inception_files_with_docket_numbers"
        os.makedirs(new_folder, exist_ok=True)
        new_file_name = f"{docket_number}_{filename[first_underscore_index+1:]}"
        # Commented out so this doesn't get run and require fixing renamed files again.
        # See comment below.
        # shutil.copyfile(f"data/full_scale/raw/inception_files/{filename}",
        #                f"{new_folder}/{new_file_name}")

# After creating these files, manually rename "mixed" and those lacking opinon type and author names.
# Eventually, the filenames should be replaced in inception so that correct filenames will be exported.
