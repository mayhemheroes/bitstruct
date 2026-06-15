#!/usr/bin/python3
"""run_tests.py - RUN bitstruct's own unittest suite and print a parseable summary.

Invoked via the /mayhem/bitstruct-tests ELF launcher (NOT directly), so the verify-repo
sabotage oracle can neuter the launcher and prove the test oracle is behavioral:
bitstruct's suite (tests/test_bitstruct.py, tests/test_c.py) is a set of known-answer
cases that assert exact packed/unpacked bytes for the pure-Python packer AND the C
extension (e.g. pack('u1u1s6u7u9', 0, 0, -2, 65, 22) == b'\\x3e\\x82\\x16'), so a
no-op / exit(0) / behavior-altering patch to bitstruct cannot pass it.

The suite references the installed `bitstruct` package (pip install . in the image, which
builds the C extension used by test_c.py). We chdir to the repo root so unittest discovery
finds tests/.
"""
from __future__ import annotations

import os
import sys
import unittest

SRC = os.environ.get("SRC", "/mayhem")
TESTS_DIR = "tests"


def main() -> int:
    os.chdir(SRC)
    loader = unittest.TestLoader()
    suite = loader.discover(TESTS_DIR, pattern="test*.py")
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stderr)
    result = runner.run(suite)

    tests = result.testsRun
    failed = len(result.failures) + len(result.errors)
    skipped = len(result.skipped)
    passed = tests - failed - skipped

    if tests == 0:
        print("RUNTESTS tests=0 passed=0 failed=1 skipped=0")
        return 1

    print(f"RUNTESTS tests={tests} passed={passed} failed={failed} skipped={skipped}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
