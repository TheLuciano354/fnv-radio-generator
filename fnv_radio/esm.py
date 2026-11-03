"""Minimal reader for Fallout New Vegas plugin files (.esm/.esp).

Only what is needed to inspect radio stations: records, groups and subrecords.
"""
import struct
import zlib

REC_HDR = struct.Struct("<4sIIIIHH")   # type, size, flags, formid, vc, version, unk
GRP_HDR = struct.Struct("<4sI4sIIHH")  # 'GRUP', size, label, gtype, stamp, unk, unk
COMPRESSED = 0x00040000


class Record:
    __slots__ = ("type", "flags", "formid", "subs", "parent_dial")

    def __init__(self, rtype, flags, formid, subs, parent_dial=None):
        self.type = rtype
        self.flags = flags
        self.formid = formid
        self.subs = subs
        self.parent_dial = parent_dial

    def get(self, name, default=None):
        for k, v in self.subs:
            if k == name:
                return v
        return default

    def all(self, name):
        return [v for k, v in self.subs if k == name]

    def zstr(self, name):
        v = self.get(name)
        return v.split(b"\0", 1)[0].decode("cp1252", "replace") if v is not None else None

    @property
    def edid(self):
        return self.zstr("EDID")


def parse_subs(data):
    subs = []
    i = 0
    big = None
    n = len(data)
    while i + 6 <= n:
        st = data[i:i + 4].decode("ascii", "replace")
        sz = struct.unpack_from("<H", data, i + 4)[0]
        i += 6
        if big is not None:
            sz, big = big, None
        if st == "XXXX":
            big = struct.unpack_from("<I", data, i)[0]
            i += sz
            continue
        subs.append((st, data[i:i + sz]))
        i += sz
    return subs


def read_masters(path):
    """Return the master files listed in the plugin header (TES4 MAST subrecords)."""
    with open(path, "rb") as f:
        _, size, *_ = REC_HDR.unpack(f.read(24))
        subs = parse_subs(f.read(size))
    return [v.split(b"\0", 1)[0].decode("cp1252") for k, v in subs if k == "MAST"]


def iter_records(path, want=None):
    """Yield Record objects. INFO records get parent_dial set to the DIAL formid."""
    with open(path, "rb") as f:
        buf = f.read()
    n = len(buf)

    def walk(start, end, dial):
        i = start
        while i < end:
            tag = buf[i:i + 4]
            if tag == b"GRUP":
                _, gsize, label, gtype, *_ = GRP_HDR.unpack_from(buf, i)
                d = dial
                if gtype == 7:  # topic children
                    d = struct.unpack("<I", label)[0]
                yield from walk(i + 24, i + gsize, d)
                i += gsize
                continue
            rtype, size, flags, formid, *_ = REC_HDR.unpack_from(buf, i)
            rtype = rtype.decode("ascii", "replace")
            body = i + 24
            if want is None or rtype in want:
                data = buf[body:body + size]
                if flags & COMPRESSED:
                    try:
                        data = zlib.decompress(data[4:])
                    except zlib.error:  # a few vanilla records have bad checksums
                        data = zlib.decompressobj().decompress(data[4:])
                yield Record(rtype, flags, formid, parse_subs(data),
                             dial if rtype == "INFO" else None)
            i = body + size

    # skip TES4 header record
    _, size, *_ = REC_HDR.unpack_from(buf, 0)
    yield from walk(24 + size, n, None)
