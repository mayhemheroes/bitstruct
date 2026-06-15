#!/usr/bin/env bash
#
# bitstruct/mayhem/build.sh - compile the ELF launcher shims for the Atheris fuzz harness and the
# unittest oracle runner.
#
# bitstruct (eerimoq/bitstruct) is fuzzed through its PURE-PYTHON pack/unpack/compile/calcsize layer
# (src/bitstruct/__init__.py: binascii/re/struct only, no native code). The Atheris libFuzzer harness
# (mayhem/fuzz_pack.py) drives that real upstream code directly, so there is nothing native to
# sanitize here.
#
# Mayhem requires every target `cmd:` to be an ELF (it rejects a shebang/script wrapper and
# fuzz-smoke.sh checks the ELF magic), so we compile a tiny C shim per Python entry point that
# exec()s `python3 <script>` (see mayhem/launcher.c). The Python deps (atheris + bitstruct itself,
# whose C extension the unittest suite needs) are installed into the image system Python by the
# Dockerfile (root + network); this script does NOT pip-install, so its offline PATCH-tier re-run
# (non-root `mayhem`, --network none) stays idempotent + air-gapped: it only compiles the shims
# (clang, no network).
set -euo pipefail

# clang rejects SOURCE_DATE_EPOCH='' - must be unset or a valid integer.
[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH

SRC="${SRC:-/mayhem}"
cd "$SRC"

: "${CC:=clang}"

# $DEBUG_FLAGS threads DWARF < 4 debug info onto the shims (SPEC 6.2 item 10): clang-19's plain
# `-g` emits DWARF-5, which Mayhem's triage can't read, so force DWARF-3 explicitly.
: "${DEBUG_FLAGS:=-gdwarf-3}"

# bitstruct's fuzzed code is pure Python, run under Atheris/libFuzzer at runtime; the shims are pure
# exec() wrappers (sanitizing them would only add ASan noise on the wrapper, never on the fuzzed
# Python). Referenced for parity / so an override is visible.
echo "SANITIZER_FLAGS=${SANITIZER_FLAGS:-<unset>} (pure-Python fuzz target; not applied to the exec shims)"
echo "DEBUG_FLAGS=$DEBUG_FLAGS"

build_launcher() {
  local out="$1" script="$2"
  echo "--- compiling launcher /mayhem/$out -> $script ---"
  # Dynamically linked (default) so the verify-repo sabotage oracle's LD_PRELOAD can reach it.
  "$CC" $DEBUG_FLAGS -O1 -DPY_SCRIPT="\"$script\"" -o "/mayhem/$out" mayhem/launcher.c
  chmod +x "/mayhem/$out"
}

# Fuzz target: the preserved Atheris harness over bitstruct's pure-Python layer. Name kept for parity.
build_launcher pack-fuzz       /mayhem/mayhem/fuzz_pack.py
# Test oracle runner: runs bitstruct's real unittest suite (driven by mayhem/test.sh through this ELF
# so the sabotage check can neuter it).
build_launcher bitstruct-tests /mayhem/mayhem/run_tests.py

echo "build.sh complete:"
ls -la /mayhem/pack-fuzz /mayhem/bitstruct-tests
