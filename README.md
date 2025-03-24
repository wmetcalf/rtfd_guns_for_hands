# rtfd_guns_for_hands
https://www.youtube.com/watch?v=Pmv8aQKO6k0

# Install 
pip3 install git+https://github.com/wmetcalf/rtfd_guns_for_hands.git

# Usage
```
rtfd-guns-parse /home/coz/Downloads/6d71b42135cbc61bc7991b43f86ddc6e0fcc563d11a76fa323bc7633678d244b.doc --extract-dir=poopship8 --json-out results.json
DEBUG: Found 'rtfd' at the start; skipping 4 bytes.
DEBUG: parse_file_block: matched combined marker => offset=72
DEBUG: Detected 00 00 00 80 => read next 8 => (file_len, pad_len).
DEBUG: No more COMBINED_MARKER found => done.
JSON results written to results.json

coz@genesis:~$ cat results.json | jq
[
  {
    "filename": "Резюме Айжан.doc",
    "extracted_path": "poopship8/Резюме Айжан.doc",
    "size": 195584,
    "padding": true,
    "md5": "ddb9983888962247a8622d720a44f46b",
    "sha1": "0eef695c2594a85de19d2461575936ebe4eeb10c",
    "sha256": "af65de3e156d812e1a930f03b95b634e3f85c3f2834e5e34bf23e88bffad3bdb",
    "mime": "application/msword"
  }
]
```

