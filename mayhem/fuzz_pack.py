#!/usr/bin/env python3
"""Atheris harness for bitstruct's pure-Python format-string interpreter.

Honest successor of the old `pack-fuzz` target: split the fuzz input into a
format string and a data buffer, then drive bitstruct's core
compile/pack/unpack/calcsize path over them.
"""

import re
import struct
import sys

import atheris
import fuzz_helpers

with atheris.instrument_imports():
    import bitstruct

# bitstruct field sizes come from `\d+` in the format string with no upper
# bound, so a single field such as `r9999999999` would ask Python to allocate
# gigabytes and OOM benignly. Bound the format length (and reject absurdly
# large numeric runs) so we exercise the parser/packer logic, not the allocator.
MAX_FMT_LEN = 256
MAX_FIELD_SIZE = 1 << 16

# Exceptions bitstruct (and the std machinery it leans on) raises on bad input.
EXPECTED = (
    bitstruct.Error,
    ValueError,
    KeyError,
    IndexError,
    struct.error,
    OverflowError,
    UnicodeDecodeError,
    UnicodeEncodeError,
)


def _has_huge_field(fmt: str) -> bool:
    # Mirror bitstruct's own field-size lexing (re `\d+`, then int()), so we
    # reject exactly the absurdly-large fields the library would otherwise try
    # to allocate — including Unicode decimal digits, which `\d` accepts.
    for run in re.findall(r"\d+", fmt):
        if len(run) > 7 or int(run) > MAX_FIELD_SIZE:
            return True
    return False


def TestOneInput(data):
    fdp = fuzz_helpers.EnhancedFuzzedDataProvider(data)

    fmt = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, MAX_FMT_LEN))
    if _has_huge_field(fmt):
        return -1
    buf = fdp.ConsumeRemainingBytes()

    try:
        cf = bitstruct.compile(fmt)
        size_bytes = (cf.calcsize() + 7) // 8
        if size_bytes > MAX_FIELD_SIZE:
            return -1

        # unpack the fuzzed buffer (tolerate short buffers via allow_truncated).
        if len(buf) >= size_bytes:
            values = cf.unpack(buf)
            # round-trip: pack the unpacked values back.
            cf.pack(*values)
        else:
            cf.unpack(buf, allow_truncated=True)

        # also exercise the module-level helpers directly on the format string.
        bitstruct.calcsize(fmt)
        bitstruct.byteswap("12", buf[:3])
    except EXPECTED:
        return -1
    except MemoryError:
        return -1


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
