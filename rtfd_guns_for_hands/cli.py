# rtfd_guns_for_hands/cli.py

import sys
import os
import argparse
import hashlib
import magic
import json

from .guns_parser import RtfdGunsForHands

def main():
    parser = argparse.ArgumentParser(
        description="Parse RTFD guns-for-hands blocks, extract files, and output JSON metadata."
    )
    parser.add_argument("input_file", help="Binary file to parse")
    parser.add_argument("--json-out", help="Write JSON results to this file (otherwise print to stdout)")
    parser.add_argument("--extract-dir", help="Directory to extract files into", default="extracted_files")

    args = parser.parse_args()

    # Read entire input file
    with open(args.input_file, "rb") as f:
        data = f.read()

    # Parse blocks
    guns = RtfdGunsForHands(data)
    blocks = guns.parse_all_file_blocks()

    # Ensure extraction directory exists
    os.makedirs(args.extract_dir, exist_ok=True)

    # We'll produce a JSON array, each entry describing an extracted file
    ms = magic.Magic(mime=True)
    results = []

    for i, block in enumerate(blocks, start=1):
        file_data = block["file_data"]
        file_size = len(file_data)
        used_padding = (block["pad_len"] > 0)

        # Choose a filename from repeated_utf8 or repeated_name, or fallback
        fname = block["repeated_utf8"] or block["repeated_name"] or f"file_{i}.bin"
        safe_name = fname.replace("/", "_").replace("\\", "_")
        out_path = os.path.join(args.extract_dir, safe_name)

        # Write the file to disk
        with open(out_path, "wb") as outf:
            outf.write(file_data)

        # Compute hashes & MIME
        md5hash = hashlib.md5(file_data).hexdigest()
        sha1hash = hashlib.sha1(file_data).hexdigest()
        sha256hash = hashlib.sha256(file_data).hexdigest()
        mime_type = ms.from_buffer(file_data)

        # Build JSON entry
        info = {
            "filename": fname,
            "extracted_path": out_path,
            "size": file_size,
            "padding": used_padding,
            "md5": md5hash,
            "sha1": sha1hash,
            "sha256": sha256hash,
            "mime": mime_type,
        }
        results.append(info)

    # Convert to JSON
    output_json = json.dumps(results, indent=2)

    # Output
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as jf:
            jf.write(output_json)
        print(f"JSON results written to {args.json_out}")
    else:
        print(output_json)

