#!/usr/bin/env python3
"""Packaging and README contract tests. Offline; stdlib only."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_skill_symlink_resolves(self):
        skill = ROOT / "skill"
        self.assertTrue(skill.is_symlink())
        self.assertEqual(skill.resolve(), (ROOT / "skills/agent-he").resolve())

    def test_plugin_versions_agree(self):
        versions = set()
        for path in (
            ROOT / ".claude-plugin/plugin.json",
            ROOT / ".codex-plugin/plugin.json",
            ROOT / "plugin.json",
        ):
            data = json.loads(path.read_text())
            versions.add(data["version"])
            self.assertEqual(data["name"], "agent-he")
        self.assertEqual(versions, {"0.1.0"})

    def test_readme_pins_both_installs_to_the_manifest_version(self):
        readme = (ROOT / "README.md").read_text()
        blocks = re.findall(r"```sh\n(.*?)```", readme, flags=re.S)
        pinned = [
            block
            for block in blocks
            if "git clone" in block and "trycopilotai/agent-he" in block
        ]
        self.assertEqual(len(pinned), 2)
        for block in pinned:
            self.assertIn("release=v0.1.0", block)

    def test_readme_names_five_fixture_findings(self):
        readme = (ROOT / "README.md").read_text()
        worked = (ROOT / "evidence/findings/WORKED_EXAMPLE.md").read_text()
        readme_ids = set(re.findall(r"\|\s*(F\d+)\s*\|", readme))
        worked_ids = set(re.findall(r"\|\s*(F\d+)\s*\|", worked))
        self.assertEqual(readme_ids, {"F1", "F2", "F3", "F4", "F5"})
        self.assertTrue(readme_ids.issubset(worked_ids))

    def test_worked_example_cites_inventory_transcript(self):
        inventory = (
            ROOT / "evidence/inventory/2026-10-13-fixture-inventory.txt"
        ).read_text()
        self.assertIn("FINDING", inventory)
        self.assertIn("bad.html", inventory)
        self.assertIn("good.html", inventory)

    def test_openai_yaml_prompt(self):
        text = (ROOT / "skills/agent-he/agents/openai.yaml").read_text()
        self.assertIn("$agent-he", text)


if __name__ == "__main__":
    unittest.main()
