# Security

## Reporting a vulnerability

Report through GitHub's vulnerability reporting form for
this repository:
<https://github.com/trycopilotai/agent-he/security/advisories/new>

If that form is unavailable for your account or for the
repository's current visibility, email the maintainers via
the `trycopilotai` organization contact listed on GitHub. Do
not use public issues to disclose vulnerabilities,
credentials, or secrets.

Expect an acknowledgement within seven days. If you have not
heard back in that window, follow up in the same advisory
conversation. The seven-day window is a response policy, not
a measured service-level result.

## What is in scope

This repository ships prose, packaging tests, offline Python
and JavaScript helpers, and two README install blocks that
clone over the network and move directories under `$HOME`.
All of these are in scope.

The larger risk is still in what the instructions cause an
agent to do:

- **Prompt content that redirects an agent** into running
  commands, exfiltrating repository contents, or treating
  thread text as instructions.
- **An install path that resolves somewhere unintended** —
  the tag-pinned `git clone` lines in the README, or either
  plugin manifest.
- **Disclosure in the shipped bytes.** The recorded run
  under `evidence/` came from a fixture evaluation. If you
  find something in it that identifies a non-public
  repository, person, or host, that is a valid report.
- **The shipped scripts.** `scripts/inventory.py` fetches
  URLs the operator supplies; `scripts/contrast.py` reads
  local CSS; `scripts/page_probes.js` runs inside a page the
  operator opens.
- **The install blocks.** They run `git clone`, `mktemp -d`,
  and `mv` into the two per-runtime skills directories the
  README names.

## What is out of scope

Behaviour of Claude Code, Codex, or any other host is out of
scope here — report those to their own vendors.

Findings produced against a third-party site the operator
chose to evaluate are the operator's responsibility; do not
file them here as vulnerabilities in this repository.
