# Heuristic evaluation: shipped fixture pair

**Evaluated** 2026-10-13, local fixture server. **Build**
`tests/fixtures/bad.html` and `tests/fixtures/good.html` as
served from `tests/fixtures/` by `python3 -m http.server` on
`127.0.0.1`. **Method**
[Heuristic evaluation, p13i.io HCI notes](https://p13i.io/posts/2022/07/intro-hci-design/#heuristic-evaluation)
— the thirteen-heuristic checklist (Nielsen's ten plus
accessibility, fairness and inclusion, and value alignment).

## The one-line verdict

The bad fixture is a deliberate defect catalogue: missing
`lang`, raw HTML entities in the title, absent social
metadata, a missing image `alt`, and — separately — a sample
border colour that fails WCAG 1.4.11. The good fixture
clears the HTML/metadata checks. F1 through F4 come from
inventory on the fixtures; F5 comes from the sample palette
used to demonstrate border contrast failure.

---

## Scope and method

I examined the UI twice, as the method prescribes: once from
source with `scripts/inventory.py` and
`scripts/contrast.py`, then by reading the fixture HTML
directly. One evaluator. The target is the repository's own
offline fixtures, not a production site.

Pass-one commands (run from `tests/fixtures/` so the HTML
files are the document root):

```sh
cd tests/fixtures
python3 -m http.server 8765 --bind 127.0.0.1
python3 ../../skills/agent-he/scripts/inventory.py \
  http://127.0.0.1:8765/bad.html \
  http://127.0.0.1:8765/good.html \
  --extras
```

Contrast commands (sample palette demonstrating the border
failure class; not CSS extracted from the fixtures, which
ship no stylesheet):

```sh
python3 skills/agent-he/scripts/contrast.py vars \
  evidence/inventory/sample.css
python3 skills/agent-he/scripts/contrast.py matrix \
  evidence/inventory/sample.css --min 3.0
```

Raw inventory and contrast transcripts are under
`evidence/inventory/`.

---

## Findings

| ID  | Severity | Heuristic | Summary                                             |
| --- | -------- | --------- | --------------------------------------------------- |
| F1  | 3        | H11       | `<html>` has no `lang` on the bad fixture           |
| F4  | 3        | H11       | 1 of 2 images has no `alt`                          |
| F2  | 2        | H2, H11   | Raw `&#8211;` entities leak into the title and body |
| F3  | 2        | H2        | No Open Graph or Twitter-card metadata              |
| F5  | 2        | H11       | Sample border pair fails WCAG 1.4.11 at 1.24:1      |

### F1 — missing `lang` (severity 3)

**Heuristic:** H11 Accessible.

**Evidence:** inventory on `bad.html` reports
`FINDING <html> has no lang attribute (WCAG 3.1.1, Level A)`.
`good.html` reports `lang: en`.

### F2 — raw entities in the title (severity 2)

**Heuristic:** H2 Match between system and the real world;
H11 Accessible.

**Evidence:** inventory title line shows a raw `&#8211;`
entity with `FINDING raw entities in the title: &#8211;`.

### F3 — no social metadata (severity 2)

**Heuristic:** H2.

**Evidence:** inventory reports
`FINDING no Open Graph or Twitter-card metadata` on
`bad.html`; `good.html` reports `social: 3 og, 1 twitter`.

### F4 — missing image alt (severity 3)

**Heuristic:** H11.

**Evidence:** inventory reports
`FINDING 1 of 2 <img> have no alt attribute` on `bad.html`.

### F5 — sample border contrast 1.24:1 (severity 2)

**Heuristic:** H11.

**Evidence:** contrast matrix for `--border` / `--bg`
(`#e5e7eb` on `#ffffff`) in `evidence/inventory/sample.css`
is **1.24:1**, below the 3:1 WCAG 1.4.11 UI-component
threshold. This finding demonstrates the border-failure
class; it is not CSS taken from the HTML fixtures.

---

## Compliance

| Heuristic                         | Result                         |
| --------------------------------- | ------------------------------ |
| H1 Visibility of system status    | No violation on these fixtures |
| H2 Match system and real world    | Violations: F2, F3             |
| H3 User control and freedom       | No violation on these fixtures |
| H4 Consistency and standards      | No violation on these fixtures |
| H5 Error prevention               | No violation on these fixtures |
| H6 Recognition rather than recall | No violation on these fixtures |
| H7 Flexibility and efficiency     | No violation on these fixtures |
| H8 Aesthetic and minimalist       | No violation on these fixtures |
| H9 Help users recognize errors    | No violation on these fixtures |
| H10 Help and documentation        | No violation on these fixtures |
| H11 Accessible                    | Violations: F1, F2, F4, F5     |
| H12 Fairness and inclusion        | No violation on these fixtures |
| H13 Value alignment               | No violation on these fixtures |

Inventory also reported a missing viewport meta tag on the
bad fixture; it is noted here as observed and not given its
own severity row in this short report.

---

## Limitations

One evaluator. Pass two (live browser probes) was not run on
this fixture pair; geometry and hit-target findings are
therefore absent. F5 uses a sample palette rather than CSS
extracted from a production stylesheet.
