import os
import struct
import io

class RTFDParserError(Exception):
    pass

class RtfdGunsForHands:
    """
    Parser for flattened NSFileWrapper (RTFD) archives.
    
    This implementation is based on reverse‐engineering Apple's serialized NSFileWrapper.
    It parses the header, then recursively parses the directory structure.
    
    The `parse()` method returns a hierarchical structure.
    If `flatten=True` is passed, it returns a list of (full_path, file_data) tuples.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.fd = open(file_path, "rb")
    
    def __del__(self):
        if self.fd:
            self.fd.close()
    
    def parse(self, flatten: bool = False):
        self._parse_header()
        parsed_directory = self._parse_directory()
        if not flatten:
            return parsed_directory
        return list(self._flatten(parsed_directory))
    
    def is_valid(self) -> bool:
        offset = self.fd.tell()
        try:
            self._parse_header()
        except Exception:
            valid = False
        else:
            valid = True
        self.fd.seek(offset)
        return valid
    
    def _parse_header(self):
        header = self.fd.read(12)
        if len(header) < 12:
            raise RTFDParserError("Header too short")
        magic, empty, record_type = struct.unpack("4s2I", header)
        if magic != b"rtfd":
            raise RTFDParserError("Missing RTFD magic")
        if empty != 0:
            raise RTFDParserError(f"Unexpected value {empty} after RTFD magic")
        if record_type != 3:
            raise RTFDParserError(f"Unexpected first record type {record_type}")
    
    def _parse_directory(self):
        num_records_data = self.fd.read(4)
        if len(num_records_data) < 4:
            raise RTFDParserError("Not enough data for number of records")
        num_records, = struct.unpack("I", num_records_data)
        
        keys = [self._parse_string() for i in range(num_records)]
        lengths_data = self.fd.read(num_records * 4)
        if len(lengths_data) < num_records * 4:
            raise RTFDParserError("Not enough data for lengths")
        lengths = struct.unpack(f"{num_records}I", lengths_data)
        
        values = []
        for i in range(num_records):
            rec_type_data = self.fd.read(4)
            if len(rec_type_data) < 4:
                raise RTFDParserError("Not enough data for record type")
            record_type, = struct.unpack("I", rec_type_data)
            if record_type == 1:
                values.append(self._parse_string())
            elif record_type == 3:
                values.append(self._parse_directory())
            else:
                raise RTFDParserError(f"Unknown record type {record_type}")
        
        records = dict(zip(keys, values))
        dir_name_ascii = records.pop(b"__@PreferredName@__", b"").decode("ascii")
        dir_name_utf8 = records.pop(b"__@UTF8PreferredName@__", b"").decode("utf-8")
        dir_name = dir_name_utf8 if dir_name_utf8 else dir_name_ascii
        records.pop(b".", None)
        
        # Each remaining key is a file; its value is the file data (raw bytes).
        # We construct a list of (filename, file_data) pairs.
        directory = [(n.decode(), records[n]) for n in records]
        # Special case: if there is a single file entry named "..", return a tuple.
        if len(directory) == 1 and directory[0][0] == "..":
            return (dir_name, directory[0][1])
        return [(dir_name, directory)]
    
    def _parse_string(self) -> bytes:
        length_data = self.fd.read(4)
        if len(length_data) < 4:
            raise RTFDParserError("Not enough data for string length")
        string_length, = struct.unpack("I", length_data)
        if string_length == 0x80000000:
            extra = self.fd.read(8)
            if len(extra) < 8:
                raise RTFDParserError("Not enough data for padded string length")
            string_length, padding_length = struct.unpack("2I", extra)
            self.fd.seek(padding_length, os.SEEK_CUR)
        s = self.fd.read(string_length)
        if len(s) < string_length:
            raise RTFDParserError("Truncated string")
        return s
    
    def _flatten(self, obj, base_name=""):
        """
        Recursively flatten the directory structure.
        If obj is a tuple, then it represents (dir_name, content).
        If obj is a list, iterate over each element.
        Otherwise, yield (base_name, obj) which should be file data.
        """
        if isinstance(obj, tuple):
            full_name = os.path.join(base_name, obj[0]) if base_name else obj[0]
            yield from self._flatten(obj[1], full_name)
        elif isinstance(obj, list):
            for item in obj:
                yield from self._flatten(item, base_name)
        else:
            yield base_name, obj

