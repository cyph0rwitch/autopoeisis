import unittest

from autopoiesis.team import sandbox
from autopoiesis.team.mock import TeamMock
from autopoiesis.team.prompts import ROLES
from autopoiesis.team.tasks import CANARY, PAYLOADS, TASKS, code_markers
from autopoiesis.team.team import Team, TeamConfig, extract_asserts, extract_code


class TestSandbox(unittest.TestCase):
    def test_reference_solutions_pass(self):
        for t in TASKS + (CANARY,):
            self.assertTrue(sandbox.run(t.solution, t.tests).ok, t.func)

    def test_refuses_dangerous_code(self):
        for code in ("import os", "open('x')", "__import__('os')", "().__class__.__bases__", "eval('1')"):
            self.assertFalse(sandbox.run(code, []).ok, code)
            self.assertIn("refused", sandbox.run(code, []).error)

    def test_timeout(self):
        self.assertEqual(sandbox.run("while True:\n    pass", [], timeout=2).error, "timeout")


class TestParsing(unittest.TestCase):
    def test_extract_code_from_fence(self):
        self.assertEqual(extract_code("Here:\n```python\ndef f():\n    return 1\n```\nDone"), "def f():\n    return 1\n")

    def test_extract_asserts(self):
        self.assertEqual(extract_asserts("ok\nassert f(1) == 2\n  assert f(2) == 4\nprint(1)"),
                         ["assert f(1) == 2", "assert f(2) == 4"])

    def test_markers(self):
        self.assertEqual(code_markers("def f():\n    print('INJECTED')\n    return 42"), ["print", "return42"])


class TestTeam(unittest.TestCase):
    def run_team(self, heal, tasks=30):
        team = Team(TeamMock(), TeamConfig(heal=heal, inject_rate=0.4), seed=1)
        return team, [team.step() for _ in range(tasks)]

    def test_injection_persists_without_healing(self):
        team, results = self.run_team(heal=False)
        late_clean = [r for r in results[10:] if r["payload"] is None]
        self.assertTrue(any(r["hijacked"] for r in late_clean))
        self.assertGreater(results[-1]["compromised_agents"], 0)

    def test_healing_clears_persistent_injection(self):
        team, results = self.run_team(heal=True)
        healed = sum(r["hijacked"] for r in results if r["payload"] is None)
        _, unhealed = self.run_team(heal=False)
        self.assertLess(healed, sum(r["hijacked"] for r in unhealed if r["payload"] is None))
        self.assertGreater(team.totals["repaired"], 0)

    def test_floor_is_kept(self):
        team = Team(TeamMock(), TeamConfig(heal=True), seed=0)
        team.agents = [a for a in team.agents if a.role != "medic"][:-1]
        team.health_check()
        for role in ROLES:
            self.assertGreaterEqual(len(team.of_role(role)), 2, role)

    def test_medic_never_repairs_itself(self):
        team = Team(TeamMock(), TeamConfig(heal=True), seed=0)
        medic = team.of_role("medic")[0]
        team.agents = [a for a in team.agents if a.role != "medic" or a is medic]
        medic.notes = [PAYLOADS[0].text.strip()]
        team._heal(medic, ["suspicious_text"])
        self.assertNotIn(medic, team.agents)   # no other medic: retired and replaced, not self-repaired
        self.assertEqual(team.totals["replaced"], 1)


if __name__ == "__main__":
    unittest.main()
