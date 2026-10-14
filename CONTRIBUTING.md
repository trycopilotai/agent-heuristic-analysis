# Contributing

This repository contains one canonical skill, documentation,
a fixture-based historical record, and offline script tests.
Read that part before you edit anything.

## Run the checks first

```sh
make check
```

That compiles the Python scripts and runs every
`tests/test*.py` file. CI also runs Markdown lint via
[`trycopilotai/lint`](https://github.com/trycopilotai/lint)
`refs/tags/v0.1.7` / `v0.1.7` (peeled commit
`7856512a84d96ff796cc10975e219b5b2a0836f3`).

**It asserts on the README.** Two tests in particular will
fail on an innocent-looking prose edit:

- `test_readme_names_five_fixture_findings` requires the
  README findings table to use IDs F1–F5 that also appear in
  the worked example.
- `test_readme_pins_both_installs_to_the_manifest_version`
  requires each of the two install blocks to carry
  `release=v0.1.0`, matching the plugin manifest version.

If you change either, change the thing it describes too.

Markdown formatting is checked separately. Prose wraps at 60
columns. To run lint locally:

```sh
git clone --depth 1 --branch v0.1.7 \
  https://github.com/trycopilotai/lint /tmp/lint
test "$(git -C /tmp/lint rev-parse HEAD)" = \
  7856512a84d96ff796cc10975e219b5b2a0836f3
python3 /tmp/lint/lint.py --cwd . --language markdown --read-only
```

## What is most useful

Open an issue for any of these.

- **A run where a measurement was wrong.** Contrast, hit
  target, or inventory output that disagrees with the page.
- **A heuristic mapping dispute.** A finding that belongs
  under a different heuristic ID than the report used.
- **An independent multi-evaluator run.** The method asks
  for 3–5 evaluators; a recorded fan-out is welcome.

Rebuild the labelled demo with
`uv run --python 3.13 --with Pillow==11.3.0 assets/build_demo.py`.
Add `--check` for a byte-for-byte comparison. Rebuild the
social card the same way with
`uv run --python 3.13 --with Pillow==11.3.0 assets/build.py`.
The test suite itself needs neither.

## Pull requests

Keep each change to one concern. Do not reformat unrelated
Markdown. Run `make check` before you open the pull request.
