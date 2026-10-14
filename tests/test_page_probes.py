"""Tests for the in-page probe library.

The probes run in a browser, so what can be tested here is
that the file is valid JavaScript and exposes the API the
skill documents. The `node` checks skip when node is absent.
"""

import json
import os
import shutil
import subprocess
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBES = os.path.join(REPO, "skill", "scripts", "page_probes.js")
SKILL = os.path.join(REPO, "skill", "SKILL.md")

DOCUMENTED = (
    "viewport",
    "hitTargets",
    "tabOrder",
    "mediaState",
    "centering",
    "spacing",
    "emptyState",
    "headings",
    "links",
    "all",
)

NODE = shutil.which("node")


class TestSource(unittest.TestCase):
    def test_file_exists(self):
        self.assertTrue(os.path.exists(PROBES))

    def test_every_documented_probe_is_defined(self):
        with open(PROBES, "r", encoding="utf-8") as handle:
            source = handle.read()
        for name in DOCUMENTED:
            self.assertIn("api." + name + " = function", source, name)

    def test_wcag_target_minimum_is_twenty_four(self):
        with open(PROBES, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("var MIN_TARGET = 24;", source)


@unittest.skipIf(NODE is None, "node is not installed")
class TestWithNode(unittest.TestCase):
    def test_parses(self):
        result = subprocess.run(
            [NODE, "--check", PROBES],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_exposes_the_documented_api(self):
        script = (
            "const fs = require('fs');"
            "const vm = require('vm');"
            "const src = fs.readFileSync(process.argv[1], 'utf8');"
            "const sandbox = {};"
            "vm.createContext(sandbox);"
            "vm.runInContext(src, sandbox);"
            "console.log(JSON.stringify(Object.keys(sandbox.agentHE)));"
        )
        result = subprocess.run(
            [NODE, "-e", script, PROBES],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        exposed = json.loads(result.stdout.strip())
        for name in DOCUMENTED:
            self.assertIn(name, exposed)


class TestSkillDocumentation(unittest.TestCase):
    def test_skill_mentions_every_probe(self):
        with open(SKILL, "r", encoding="utf-8") as handle:
            skill = handle.read()
        for name in DOCUMENTED:
            if name == "all":
                continue
            self.assertIn("agentHE." + name, skill, name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
