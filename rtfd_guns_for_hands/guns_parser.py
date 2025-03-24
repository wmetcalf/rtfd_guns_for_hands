# rtfd_guns_for_hands/guns_parser.py

import sys
import struct


def debug(msg):
    """Helper debug function; prints to stderr so it doesn't pollute normal output."""
    print(f"DEBUG: {msg}", file=sys.stderr)


COMBINED_MARKER = b"\x13\x00\x00\x00\x5f\x5f\x40\x50\x72\x65\x66\x65\x72\x72\x65\x64\x4e\x61\x6d\x65\x40\x5f\x5f\x17\x00\x00\x00\x5f\x5f\x40\x55\x54\x46\x38\x50\x72\x65\x66\x65\x72\x72\x65\x64\x4e\x61\x6d\x65\x40\x5f\x5f"


class RtfdGunsForHands:
    """
    Parses 'RTFD guns for hands' blocks from a bytes object.
    Each block is structured as:
      - Combined marker (COMBINED_MARKER)
      - skip 21 unknown bytes
      - read marker => 01 00 00 00
      - next 4 => if 00 00 00 80 => read next 8 => (file_len, pad_len), else file_len
      - skip pad_len
      - read file_len => file_data
      - repeated_name => marker + length
      - repeated_utf8 => marker + length
    """

    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0
        self.length = len(data)

    def skip_rtfd_magic(self):
        """Skip 'rtfd' if present."""
        if self.data.startswith(b"rtfd"):
            debug("Found 'rtfd' at the start; skipping 4 bytes.")
            self.offset += 4

    def parse_all_file_blocks(self):
        """
        1) skip 'rtfd' if present
        2) find next COMBINED_MARKER
        3) parse a block
        4) store results
        5) repeat until no marker found or parse fails
        Returns a list of dicts, each with:
          {
            'file_len': int,
            'pad_len': int,
            'file_data': bytes,
            'repeated_name': str,
            'repeated_utf8': str
          }
        """
        blocks = []
        if self.offset == 0 and not self.data.startswith(b"rtfd"):
            debug("No 'rtfd' at start => returning empty list.")
            return blocks
        self.skip_rtfd_magic()

        while True:
            pos = self.data.find(COMBINED_MARKER, self.offset)
            if pos == -1:
                debug("No more COMBINED_MARKER found => done.")
                break

            block, new_off = self.parse_file_block(pos)
            if block is None:
                debug("parse_file_block => fail => stopping.")
                break

            blocks.append(block)
            self.offset = new_off
        return blocks

    def parse_file_block(self, start_offset: int):
        """Parse exactly one block from start_offset.
        Return (block_dict, new_offset) or (None, start_offset) if fail.
        """
        marker_len = len(COMBINED_MARKER)
        if start_offset + marker_len > self.length:
            debug("Truncated => not enough data for COMBINED_MARKER.")
            return None, start_offset

        actual = self.data[start_offset : start_offset + marker_len]
        if actual != COMBINED_MARKER:
            debug("Marker mismatch => not combined marker.")
            return None, start_offset

        offset = start_offset + marker_len
        debug(f"parse_file_block: matched combined marker => offset={offset}")

        # skip 21 unknown bytes
        if offset + 21 > self.length:
            debug("Truncated => not enough data for 21 unknown bytes.")
            return None, start_offset
        offset += 21

        # read 4 => should be 01 00 00 00
        if offset + 4 > self.length:
            debug("Truncated => not enough data for marker 01 00 00 00.")
            return None, start_offset
        marker = self.data[offset : offset + 4]
        if marker != b"\x01\x00\x00\x00":
            debug(f"Marker mismatch => expected 01 00 00 00, got {marker!r}")
            return None, start_offset
        offset += 4

        # next 4 => if 00 00 00 80 => read next 8 => (file_len, pad_len), else file_len
        if offset + 4 > self.length:
            debug("Truncated => not enough data for file_len/padding.")
            return None, start_offset
        maybe_padding = self.data[offset : offset + 4]
        offset += 4

        pad_len = 0
        file_len = 0
        if maybe_padding == b"\x00\x00\x00\x80":
            debug("Detected 00 00 00 80 => read next 8 => (file_len, pad_len).")
            if offset + 8 > self.length:
                debug("Truncated => not enough for file_len, pad_len.")
                return None, start_offset
            file_len = struct.unpack_from("<I", self.data, offset)[0]
            pad_len = struct.unpack_from("<I", self.data, offset + 4)[0]
            offset += 8
        else:
            # interpret as file_len
            file_len = struct.unpack_from("<I", maybe_padding, 0)[0]
            debug(f"No padding => file_len={file_len}")

        # skip pad_len
        if offset + pad_len > self.length:
            debug("Truncated => not enough to skip pad_len.")
            return None, start_offset
        offset += pad_len

        # read file_data
        if offset + file_len > self.length:
            debug("Truncated => not enough for file_data.")
            return None, start_offset
        file_data = self.data[offset : offset + file_len]
        offset += file_len

        # repeated_name
        rep_name, offset = self._parse_repeated_string(offset)
        if rep_name is None:
            debug("Failed repeated_name parse.")
            return None, start_offset

        # repeated_utf8
        rep_utf8, offset = self._parse_repeated_string(offset)
        if rep_utf8 is None:
            debug("Failed repeated_utf8 parse.")
            return None, start_offset

        block_info = {
            "file_len": file_len,
            "pad_len": pad_len,
            "file_data": file_data,
            "repeated_name": rep_name,
            "repeated_utf8": rep_utf8,
        }
        return block_info, offset

    def _parse_repeated_string(self, offset: int):
        """Read marker 01 00 00 00 => 4 => length => read => decode."""
        if offset + 4 > self.length:
            return None, offset
        marker = self.data[offset : offset + 4]
        if marker != b"\x01\x00\x00\x00":
            return None, offset
        offset += 4

        if offset + 4 > self.length:
            return None, offset
        name_len = struct.unpack_from("<I", self.data, offset)[0]
        offset += 4

        if offset + name_len > self.length:
            return None, offset
        raw = self.data[offset : offset + name_len]
        offset += name_len
        try:
            name_str = raw.decode("utf-8", errors="replace")
        except:
            name_str = raw.decode("ascii", errors="replace")
        return name_str, offset
