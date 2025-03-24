#!/usr/bin/env python3
import sys
import os
import argparse
import json
import hashlib
import magic

from rtfd_guns_for_hands.guns_parser import RtfdGunsForHands


def compute_hashes(data: bytes):
    md5hash = hashlib.md5(data).hexdigest()
    sha1hash = hashlib.sha1(data).hexdigest()
    sha256hash = hashlib.sha256(data).hexdigest()
    return md5hash, sha1hash, sha256hash


def main():
    parser = argparse.ArgumentParser(
        description="Parse RTFD guns-for-hands blocks, extract files, and output JSON metadata. https://www.youtube.com/watch?v=Pmv8aQKO6k0"
    )
    parser.add_argument("input_file", help="Path to the RTFD file")
    parser.add_argument("--extract-dir", default="extracted_files", help="Directory to extract files into")
    parser.add_argument("--json-out", help="Output JSON file (if not provided, prints JSON to stdout)")
    args = parser.parse_args()

    # Parse the archive
    try:
        rtfd_parser = RtfdGunsForHands(args.input_file)
        # flatten returns a list of tuples: (full_path, file_data)
        flat_files = rtfd_parser.parse(flatten=True)
    except Exception as e:
        print(f"Error parsing RTFD file: {e}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.extract_dir, exist_ok=True)
    ms = magic.Magic(mime=True)

    results = []
    for full_path, file_data in flat_files:
        # Construct output path: preserve directory structure under extract-dir
        out_path = os.path.join(args.extract_dir, full_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(file_data)

        size = len(file_data)
        md5hash, sha1hash, sha256hash = compute_hashes(file_data)
        mime_type = ms.from_buffer(file_data)

        result = {
            "filename": os.path.basename(out_path),
            "full_path": out_path,
            "size": size,
            "md5": md5hash,
            "sha1": sha1hash,
            "sha256": sha256hash,
            "mime": mime_type,
        }
        results.append(result)

    output_json = json.dumps(results, indent=2)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as jf:
            jf.write(output_json)
        print(f"JSON results written to {args.json_out}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
