#!/usr/bin/env bash
#
# Build a self-contained StrictDoc bundle with PyInstaller.
#
# Usage:
#   scripts/build_bundle.sh [--clean] [VERSION]
#
#   --clean   Recreate the build venv even when it could be reused.
#
# Output (relative to the repository root):
#   dist/strictdoc-<VERSION>-<PLATFORM>/          onedir bundle
#   dist/strictdoc-<VERSION>-<PLATFORM>/strictdoc[.exe]
#                                                 command-line interface
#   dist/strictdoc-<VERSION>-<PLATFORM>/strictdoc_launcher[.exe]
#                                                 desktop launcher
#   dist/strictdoc-<VERSION>-<PLATFORM>/StrictDoc.app
#                                                 desktop launcher app (macOS)
#   dist/strictdoc-<VERSION>-<PLATFORM>.zip       the same, zipped
#
# VERSION defaults to __version__ from strictdoc/__init__.py. A leading "v"
# (as in a git tag) is stripped. PLATFORM is e.g. linux-x86_64,
# windows-x86_64, macos-arm64.
#
# Environment variables:
#   PYTHON         Python for the build venv, 3.10 or newer. With uv this is
#                  a version request or interpreter path (default: a
#                  uv-managed CPython 3.12, downloaded by uv if needed). With pip it is the
#                  interpreter to run (default: python3, or python).
#   BUILD_VENV     Venv directory (default: build/bundle-venv). Reused
#                  while uv.lock, pyproject.toml, the Python request, the
#                  PyInstaller version and the installer stay the same;
#                  otherwise recreated. StrictDoc itself is reinstalled from
#                  this checkout on every run.
#   PYINSTALLER_VERSION  Pinned PyInstaller version (default below).
#   USE_UV         "1" forces uv, "0" forces pip. By default uv is used when
#                  it is on PATH. With uv, all dependencies are installed at
#                  the exact versions in uv.lock; with pip, only PyInstaller
#                  is pinned and StrictDoc's dependencies resolve to the
#                  newest allowed versions.
#
# Works on Linux, macOS and Windows (Git Bash).

set -euo pipefail

CLEAN=0
if [ "${1:-}" = "--clean" ]; then
  CLEAN=1
  shift
fi

PYINSTALLER_VERSION="${PYINSTALLER_VERSION:-6.22.2}"
# jaraco.text: pkg_resources' runtime hook fails without it in a bundle,
# see the "pyinstaller" dependency group in pyproject.toml.
JARACO_TEXT_VERSION="4.3.0"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

log() { printf '\n==> %s\n' "$*"; }

#
# Version and platform.
#
VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  VERSION="$(sed -n 's/^__version__ *= *"\(.*\)"/\1/p' strictdoc/__init__.py)"
fi
VERSION="${VERSION#v}"
if [ -z "$VERSION" ]; then
  echo "error: could not determine the version" >&2
  exit 1
fi

case "$(uname -s)" in
  Linux*) OS=linux ;;
  Darwin*) OS=macos ;;
  MINGW* | MSYS* | CYGWIN*) OS=windows ;;
  *) echo "error: unsupported OS: $(uname -s)" >&2; exit 1 ;;
esac
ARCH="$(uname -m)"
case "$ARCH" in
  amd64 | AMD64) ARCH=x86_64 ;;
  aarch64) ARCH=arm64 ;;
esac
PLATFORM="$OS-$ARCH"
NAME="strictdoc-$VERSION-$PLATFORM"

#
# Build venv.
#
if [ -z "${USE_UV:-}" ]; then
  if command -v uv >/dev/null 2>&1; then USE_UV=1; else USE_UV=0; fi
fi

PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  if [ "$USE_UV" = 1 ]; then
    # A uv-managed CPython (python-build-standalone), downloaded if needed,
    # so every platform builds with the same kind of interpreter (one that
    # includes tkinter for the launcher) regardless of what is installed.
    PYTHON=3.12
    export UV_PYTHON_PREFERENCE="${UV_PYTHON_PREFERENCE:-only-managed}"
  elif command -v python3 >/dev/null 2>&1 && python3 -c "" >/dev/null 2>&1; then
    PYTHON=python3
  else
    PYTHON=python
  fi
fi

BUILD_VENV="${BUILD_VENV:-$ROOT/build/bundle-venv}"
if [ "$OS" = windows ]; then
  VENV_BIN="$BUILD_VENV/Scripts"
  VENV_PY="$VENV_BIN/python.exe"
else
  VENV_BIN="$BUILD_VENV/bin"
  VENV_PY="$VENV_BIN/python"
fi

log "StrictDoc bundle $NAME (uv: $USE_UV, python: $PYTHON)"

# The venv is reused when everything that decides its contents is unchanged.
# The stamp holds those inputs; it is written only after a successful setup,
# so an interrupted setup is redone on the next run.
VENV_STAMP="$BUILD_VENV/.strictdoc-bundle-stamp"
venv_inputs() {
  printf 'uv=%s python=%s pyinstaller=%s jaraco=%s\n' \
    "$USE_UV" "$PYTHON" "$PYINSTALLER_VERSION" "$JARACO_TEXT_VERSION"
  cat "$ROOT/pyproject.toml" "$ROOT/uv.lock"
}
WANTED_STAMP="$(venv_inputs | cksum)"

if [ "$CLEAN" != 1 ] && [ -x "$VENV_PY" ] \
  && [ "$(cat "$VENV_STAMP" 2>/dev/null)" = "$WANTED_STAMP" ]; then
  log "Reusing venv $BUILD_VENV"
  if [ "$USE_UV" = 1 ]; then
    uv pip install --python "$VENV_PY" --no-deps --reinstall .
  else
    "$VENV_PY" -m pip install --quiet --no-deps --force-reinstall .
  fi
else
  rm -rf "$BUILD_VENV"

  if [ "$USE_UV" = 1 ]; then
    log "Creating venv with uv and installing locked dependencies"
    uv venv --quiet --python "$PYTHON" "$BUILD_VENV"
    # Install exactly what uv.lock pins for StrictDoc plus the "pyinstaller"
    # dependency group, then StrictDoc itself from this checkout.
    UV_PROJECT_ENVIRONMENT="$BUILD_VENV" VIRTUAL_ENV="$BUILD_VENV" \
      uv sync --frozen --no-install-project --group pyinstaller \
      --python "$PYTHON"
    uv pip install --python "$VENV_PY" --no-deps .
    uv pip install --python "$VENV_PY" "pyinstaller==$PYINSTALLER_VERSION"
  else
    log "Creating venv with $PYTHON and installing with pip"
    "$PYTHON" -m venv "$BUILD_VENV"
    "$VENV_PY" -m pip install --quiet --upgrade pip
    "$VENV_PY" -m pip install --quiet . \
      "pyinstaller==$PYINSTALLER_VERSION" \
      "jaraco.text==$JARACO_TEXT_VERSION"
  fi
  printf '%s\n' "$WANTED_STAMP" > "$VENV_STAMP"
fi

"$VENV_PY" --version
"$VENV_PY" -m PyInstaller --version

#
# PyInstaller.
#
log "Running PyInstaller"
rm -rf build/pyinstaller dist/strictdoc dist/strictdoc-app dist/StrictDoc.app \
  "dist/$NAME" "dist/$NAME.zip"
# Keep __pycache__ out of the source tree during analysis.
export PYTHONPYCACHEPREFIX="$ROOT/build/pycache"
"$VENV_PY" -m PyInstaller \
  --noconfirm \
  --clean \
  --log-level WARN \
  --workpath build/pyinstaller \
  --distpath dist \
  scripts/strictdoc.spec

mv dist/strictdoc "dist/$NAME"
if [ "$OS" = macos ]; then
  # The spec builds the app from its own COLLECT in dist/strictdoc-app.
  mv dist/StrictDoc.app "dist/$NAME/StrictDoc.app"
  rm -rf dist/strictdoc-app
fi

EXE="dist/$NAME/strictdoc"
LAUNCHER="dist/$NAME/strictdoc_launcher"
if [ "$OS" = windows ]; then
  EXE="$EXE.exe"
  LAUNCHER="$LAUNCHER.exe"
fi
log "Checking $EXE"
"$EXE" version
log "Checking $LAUNCHER"
[ -f "$LAUNCHER" ] || { echo "error: missing $LAUNCHER" >&2; exit 1; }
# The launcher runs StrictDoc commands as "strictdoc_launcher _strictdoc
# <args>". The output goes to a file: a windowed executable on Windows gets
# no console, but it gets the file as its standard output.
"$LAUNCHER" _strictdoc version >build/launcher_version.txt 2>&1
cat build/launcher_version.txt
if [ "$OS" = macos ]; then
  APP_LAUNCHER="dist/$NAME/StrictDoc.app/Contents/MacOS/strictdoc_launcher"
  [ -f "$APP_LAUNCHER" ] || { echo "error: missing $APP_LAUNCHER" >&2; exit 1; }
  "$APP_LAUNCHER" _strictdoc version >build/launcher_version.txt 2>&1
  cat build/launcher_version.txt
fi

log "Zipping"
# Like "zip -ry": symlinks (e.g. the numpy/scipy .libs on Linux) are stored as
# symlinks rather than duplicated, and Unix permissions are kept. Windows
# bundles contain no symlinks. Python is used because Git Bash has no zip.
(cd dist && "$VENV_PY" - "$NAME" <<'PY'
import os
import stat
import sys
import zipfile

name = sys.argv[1]
with zipfile.ZipFile(f"{name}.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in os.walk(name):
        dirnames.sort()
        for entry in sorted(dirnames) + sorted(filenames):
            path = os.path.join(dirpath, entry)
            arcname = path.replace(os.sep, "/")
            if os.path.islink(path):
                info = zipfile.ZipInfo(arcname)
                info.create_system = 3  # Unix, so that unzip honors the mode
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                zf.writestr(info, os.readlink(path))
            elif os.path.isfile(path):
                zf.write(path, arcname)
PY
)

log "Done"
echo "bundle: $ROOT/dist/$NAME"
echo "zip:    $ROOT/dist/$NAME.zip"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "name=$NAME"
    echo "dir=dist/$NAME"
    echo "zip=dist/$NAME.zip"
    echo "exe=$EXE"
    echo "launcher=$LAUNCHER"
  } >>"$GITHUB_OUTPUT"
fi
