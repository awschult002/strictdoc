# StrictDoc

StrictDoc is open-source software for technical documentation and requirements
management.

## Documentation

The main StrictDoc documentation is hosted on Read the Docs:

The documentation is hosted on Read the Docs:
[StrictDoc documentation](https://strictdoc.readthedocs.io/en/stable/).

For a quick visual overview, see the
[StrictDoc project slide deck](https://github.com/strictdoc-project/strictdoc/blob/main/about/StrictDoc.pdf).

## Installation

StrictDoc requires Python 3.10 or newer.

```bash
pip install strictdoc
```

See the
[StrictDoc user guide](https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide.html)
section of the Read the Docs site for more details.

## Standalone bundle (no Python)

A self-contained build of StrictDoc runs without Python, pip or a venv.
Each zip on the
[Releases](https://github.com/awschult002/strictdoc/releases) page holds one
platform's bundle: `strictdoc-<version>-windows-x86_64.zip`,
`strictdoc-<version>-linux-x86_64.zip` or `strictdoc-<version>-macos-arm64.zip`.

Unzip it anywhere and run the `strictdoc` executable at the top of the
folder (`strictdoc.exe` on Windows). Keep the `_internal` folder next to it.

```bash
strictdoc-0.30.1-windows-x86_64\strictdoc.exe export my_docs
strictdoc-0.30.1-windows-x86_64\strictdoc.exe server my_docs
```

To call it as plain `strictdoc`, add the folder to `PATH`.

The bundle also has a desktop launcher for users who do not use the command
line. The launcher opens or creates a project, starts the server and opens
the project in the browser:

- Windows: double-click `strictdoc_launcher.exe`. The launcher has no
  console window.
- macOS: double-click `StrictDoc.app`. Move the app to `Applications` if you
  want. The app contains its own copy of StrictDoc.
- Linux: run `strictdoc_launcher`.

When you close the launcher window, the launcher stops the server. See the
"Desktop launcher" section of the user guide for the start dialog and the
project templates.

HTML2PDF export (`--formats html2pdf`) needs Google Chrome installed; the
bundle does not include it. StrictDoc detects the installed Chrome and, on
the first PDF export, downloads the matching ChromeDriver into a per-user
cache: `$XDG_CACHE_HOME/strictdoc` or `~/.cache/strictdoc` on Linux,
`%LOCALAPPDATA%\strictdoc\cache` on Windows, `~/Library/Caches/strictdoc` on
macOS. If the project config sets `dir_for_sdoc_cache`, that folder is used
instead. The download needs internet access once. Offline, or with Chrome in
an unusual location, pass the paths explicitly:

```bash
strictdoc export my_docs --formats html2pdf \
    --chrome-binary "/path/to/chrome" --chromedriver "/path/to/chromedriver"
```

The `HTML2PDF4DOC_CHROME_BINARY` environment variable also sets the Chrome
binary.

On macOS, the bundle is not signed and not notarized. When you open
`StrictDoc.app` for the first time, macOS shows a message that it cannot
verify the app. To open the app:

1. Click `Done` in the message.
2. Open `System Settings` > `Privacy & Security`.
3. In the `Security` section, find the message about `StrictDoc.app` and click
   `Open Anyway`.
4. Confirm with your password and click `Open Anyway` again.

macOS remembers this choice for this copy of the app. On older macOS
versions, Control-click the app, select `Open` and then click `Open`.

For the command-line executable, or to allow the whole folder in one step,
run `xattr -dr com.apple.quarantine strictdoc-<version>-macos-arm64`.

To build a bundle from a checkout (Linux, macOS, or Git Bash on Windows),
run the build script, then the smoke tests against the result:

```bash
scripts/build_bundle.sh                # or: scripts/build_bundle.sh 1.2.3
scripts/smoke_bundle.sh dist/strictdoc-<version>-<platform>/strictdoc
```

`tests/bundle/run_bundle_tests.sh <exe> smoke|full|lit|all` runs a deeper
pytest suite against a bundle (see `tests/bundle/TEST_PLAN.md`); it needs
`pytest playwright openpyxl pypdf` on the test machine, not in the bundle.

The build script uses `uv` when it is installed (dependencies pinned by
`uv.lock`, CPython 3.12) and falls back to `python3 -m venv` and pip. The
`Bundle (PyInstaller)` GitHub Actions workflow runs both scripts on Linux,
Windows and macOS and attaches the zips to a GitHub Release when a `v*` tag
is pushed.

## Quick start

Create a small `hello_world.sdoc` file:

```text
[DOCUMENT]
TITLE: StrictDoc

[REQUIREMENT]
UID: SDOC-HIGH-REQS-MANAGEMENT
TITLE: Requirements management
STATEMENT: StrictDoc shall enable requirements management.
```

Export it to static HTML:

```bash
strictdoc export .
```

Or run the local web server:

```bash
strictdoc server .
```

StrictDoc starts the server on `http://127.0.0.1:5111` by default.

## Project links

- Documentation: <https://strictdoc.readthedocs.io/en/stable/>
- Source code: <https://github.com/strictdoc-project/strictdoc>
- Examples: <https://github.com/strictdoc-project/strictdoc-examples>
- Templates: <https://github.com/strictdoc-project/strictdoc-templates>

## License

StrictDoc is licensed under the Apache License 2.0. See
[LICENSE](LICENSE) for details.
