# syntax=docker/dockerfile:1.7
#
# Commit-image Dockerfile (SMALL form) - builds ON TOP of the org base image
# (ghcr.io/mayhemheroes/base). The base provides debian + clang/llvm + libFuzzer + Python 3 + the
# identities + the build-contract ENV. bitstruct (eerimoq/bitstruct) packs/unpacks C bit-field
# structs; its fuzzed surface is the PURE-PYTHON pack/unpack/compile/calcsize layer, so the fuzz
# target has no native code to sanitize. Its unittest suite also exercises the optional C extension
# (bitstruct.c), so we install a C compiler + build bitstruct (which compiles that extension). This
# image installs the Atheris engine plus bitstruct into the base system Python as root, then (as
# non-root `mayhem`) compiles the ELF launcher shims and runs the real unittest suite via build.sh /
# test.sh.
#
# Build (from the repo root):
#   DOCKER_BUILDKIT=1 docker build -f mayhem/Dockerfile \
#       --build-arg COMMIT=$(git rev-parse HEAD) \
#       [--build-arg SOURCE_DATE_EPOCH=$(date +%s)] \
#       -t bitstruct-commit:test .

FROM ghcr.io/mayhemheroes/base:20260621

ARG COMMIT
ARG REPO_URL
# SOURCE_DATE_EPOCH stays an ARG (available to build.sh); never bake it as ENV - an empty value
# breaks clang. build.sh unsets it when empty.
ARG SOURCE_DATE_EPOCH
# Declared for parity with the build contract; the bitstruct fuzz target (pure-Python packer) has no
# native code to sanitize.
ARG SANITIZER_FLAGS

# Toolchain for bitstruct's optional C extension (bitstruct.c / bitstream.c), which the unittest
# suite (tests/test_c.py) imports.
USER root
RUN apt-get update && apt-get install -yq --no-install-recommends \
      python3-dev python-is-python3 gcc \
    && rm -rf /var/lib/apt/lists/*

# Atheris (the libFuzzer harness engine - builds a native module against the base clang/libFuzzer)
# goes into the base SYSTEM Python. PEP 668 marks that interpreter externally-managed, so
# --break-system-packages. This is the (networked) install step; build.sh deliberately does NOT
# pip-install, so its offline PATCH-tier re-run stays air-gapped. Atheris is pinned for a
# reproducible engine.
RUN pip install --no-cache-dir --break-system-packages atheris==3.1.0

# Source enters from the build CONTEXT (the CI checkout): the FULL repo (incl. .git history)
# is copied to /mayhem as `mayhem`; build.sh builds in place.
WORKDIR /mayhem
COPY --chown=2000:2000 . /mayhem

# Install bitstruct itself (builds the C extension with gcc) so the harness and the unittest oracle
# can `import bitstruct` / `import bitstruct.c`. --no-build-isolation reuses the already-installed
# setuptools/wheel so the build backend needs no network.
RUN pip install --no-cache-dir --break-system-packages setuptools wheel \
 && pip install --no-cache-dir --break-system-packages --no-build-isolation .

USER mayhem

# Compile the ELF launcher shims (Mayhem needs an ELF target, not a .py).
RUN bash mayhem/build.sh

# Run bitstruct's real unittest known-answer suite at build time; a failing suite fails the build.
RUN if [ -f mayhem/test.sh ]; then bash mayhem/test.sh; else echo "no mayhem/test.sh"; fi

LABEL org.opencontainers.image.source="${REPO_URL}" \
      org.opencontainers.image.revision="${COMMIT}" \
      rlenv.tier="commit" \
      rlenv.source_date_epoch="${SOURCE_DATE_EPOCH}" \
      rlenv.user="mayhem"

USER mayhem
WORKDIR /mayhem
