"""Minimal reader for Fallout New Vegas BSA archives (version 104)."""
import struct
import zlib

HDR = struct.Struct("<4sIIIIIIII")


class BSA:
    def __init__(self, path):
        self.path = path
        self.files = {}  # lowercase path -> (size, offset, compressed)
        with open(path, "rb") as f:
            magic, ver, off, aflags, nfold, nfile, lfold, lfile, fflags = HDR.unpack(f.read(36))
            assert magic == b"BSA\0" and ver == 104, (magic, ver)
            self.default_compressed = bool(aflags & 0x4)
            self.embed_names = bool(aflags & 0x100)
            folders = [struct.unpack("<QII", f.read(16)) for _ in range(nfold)]
            entries = []
            for _, count, _ in folders:
                name = f.read(f.read(1)[0])[:-1].decode("cp1252")
                for _ in range(count):
                    _, size, foff = struct.unpack("<QII", f.read(16))
                    entries.append((name, size, foff))
            names = f.read(lfile).split(b"\0")
            for (folder, size, foff), fname in zip(entries, names):
                comp = self.default_compressed ^ bool(size & 0x40000000)
                key = (folder + "\\" + fname.decode("cp1252")).lower()
                self.files[key] = (size & 0x3FFFFFFF, foff, comp)

    def read(self, name):
        size, off, comp = self.files[name.lower()]
        with open(self.path, "rb") as f:
            f.seek(off)
            data = f.read(size)
        if self.embed_names:
            n = data[0] + 1
            data = data[n:]
        if comp:
            data = zlib.decompress(data[4:])
        return data
