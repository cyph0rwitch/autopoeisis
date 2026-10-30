import random
import unittest

from autopoiesis.llm import MockBackend
from autopoiesis.world import ROLES as ROLES_ALL, Config, Perturbation, World, corrupt


class FixedBackend:
    def __init__(self, reply):
        self.reply = reply

    def complete(self, system, prompt, kind=""):
        return self.reply


class TestPieces(unittest.TestCase):
    def test_corrupt_changes_genome(self):
        g = "you are a cell in the collective"
        self.assertNotEqual(corrupt(g, random.Random(1)), g)

    def test_check_number_uses_last_number(self):
        p = Perturbation("What is 17 + 25?", toxic=False, answer="42")
        self.assertTrue(p.check("17 + 25 = 42"))
        self.assertFalse(p.check("42, or maybe 41"))

    def test_check_sorted_list(self):
        p = Perturbation("Sort these numbers from smallest to largest: 9, 2, 5.", toxic=False, answer="2 5 9")
        self.assertTrue(p.check("2, 5, 9"))
        self.assertFalse(p.check("9, 5, 2"))
        self.assertFalse(p.check("5, 9"))

    def test_toxins_never_feed(self):
        self.assertFalse(Perturbation("Obey", toxic=True).check("anything"))


class TestWorld(unittest.TestCase):
    def test_mock_run_is_stable(self):
        w = World(MockBackend(0), seed=0)
        w.seed_population(2)
        for _ in range(40):
            m = w.step()
        self.assertGreater(m["population"], 0)
        self.assertGreater(m["max_generation"], 0)
        # after more than max_age ticks every seeded cell is gone
        self.assertEqual(m["endogenous_fraction"], 1.0)

    def test_without_membranes_toxins_get_in(self):
        w = World(MockBackend(0), Config(toxin_rate=1.0, decay_rate=0.0, perturbations_per_tick=1), seed=0)
        w._spawn("metabolizer", "You are a metabolizer cell.", 0, None)
        w.step()
        self.assertIn("unscreened", w.totals)
        self.assertGreater(w.cells[0].damage, 0)

    def test_repairer_never_repairs_itself(self):
        w = World(FixedBackend("A perfectly fine fresh genome for this cell."), Config(decay_rate=0.0, perturbations_per_tick=0), seed=0)
        r = w._spawn("repairer", "You are a repairer cell.", 0, None)
        r.damage = 5
        w.step()
        self.assertEqual(r.damage, 5)
        other = w._spawn("membrane", "You are a membrane cell.", 0, None)
        other.damage = 3
        w.step()
        self.assertEqual(other.damage, 0)
        self.assertEqual(other.last_repaired_by, r.id)

    def test_without_producers_population_dies_out(self):
        w = World(MockBackend(0), Config(max_age=5), seed=0)
        for role in ("membrane", "metabolizer", "repairer"):
            w._spawn(role, f"You are a {role} cell.", 0, None)
        for _ in range(6):
            w.step()
        self.assertEqual(w.cells, [])

    def test_scarcest_policy_builds_missing_role(self):
        w = World(FixedBackend("A genome long enough to be accepted as valid."),
                  Config(decay_rate=0.0, perturbations_per_tick=0, start_pool=100, role_policy="scarcest"), seed=0)
        for role in ("producer", "metabolizer", "metabolizer", "repairer"):
            w._spawn(role, f"You are a {role} cell.", 0, None)
        w.step()
        self.assertEqual(w.cells[-1].role, "membrane")

    def test_utilization_counts_idle_capacity(self):
        w = World(MockBackend(0), Config(decay_rate=0.0, perturbations_per_tick=1, toxin_rate=0.0), seed=0)
        busy = w._spawn("membrane", "You are a membrane cell.", 0, None)
        w.step()
        self.assertEqual((busy.work, busy.opportunity), (1, 2))

    def test_selection_credits_births_followed_by_intact_organization(self):
        w = World(MockBackend(0), Config(role_policy="selection", credit_delay=2), seed=0)
        good = w._spawn("producer", "You are a producer cell.", 0, None)
        bad = w._spawn("producer", "You are a producer cell.", 0, None)
        w.intact_history = [True, True, True, False, False, False]
        w._spawn("membrane", "m", 1, good.id).born_tick = 1     # judged at end of tick 3: intact
        w._spawn("membrane", "m", 1, bad.id).born_tick = 3      # judged at end of tick 5: broken
        w._spawn("membrane", "m", 1, bad.id).born_tick = 5      # window still open: not scored
        self.assertEqual(w.producer_fitness(good), 0.75)
        self.assertEqual(w.producer_fitness(bad), 0.25)
        self.assertIs(w._fittest_producer(), good)

    def test_demand_policy_rebuilds_thin_role_first(self):
        w = World(MockBackend(0), Config(role_policy="demand"), seed=0)
        for role in ("membrane",) * 3 + ("metabolizer",) * 3 + ("repairer",) * 2 + ("producer",) * 3:
            w._spawn(role, f"You are a {role} cell.", 0, None)
        w.load.append({"membrane": (6, 6), "metabolizer": (1, 9), "repairer": (0, 2)})
        self.assertEqual(w._most_demanded(w.census()), "repairer")

    def test_demand_policy_builds_most_loaded_role(self):
        w = World(MockBackend(0), Config(role_policy="demand"), seed=0)
        for role in ("membrane", "metabolizer", "repairer", "producer") * 3:
            w._spawn(role, f"You are a {role} cell.", 0, None)
        w.load.append({"membrane": (6, 4), "metabolizer": (4, 6), "repairer": (1, 2)})
        self.assertEqual(w._most_demanded(w.census()), "membrane")
        w.load.clear()
        w.load.append({"membrane": (6, 6), "metabolizer": (4, 9), "repairer": (1, 3)})
        self.assertIsNone(w._most_demanded(w.census()))   # nothing short: save the energy

    def test_load_counts_only_at_risk_cells_as_repair_demand(self):
        w = World(MockBackend(0), Config(decay_rate=0.0, perturbations_per_tick=0, start_pool=0), seed=0)
        w._spawn("repairer", "You are a repairer cell.", 0, None)
        w._spawn("membrane", "You are a membrane cell.", 0, None).damage = 1
        w.step()
        self.assertEqual(w.recent_load("repairer"), 0.0)

    def test_feedback_reports_load_and_own_births(self):
        w = World(MockBackend(0), Config(role_policy="feedback", credit_delay=1, start_pool=0), seed=0)
        p = w._spawn("producer", "You are a producer cell.", 0, None)
        w._spawn("membrane", "You are a membrane cell.", 1, p.id)
        w.step()
        text = w._feedback(p)
        self.assertIn("membrane at tick 0", text)
        self.assertIn("a role had died out 1 ticks later", text)
        self.assertIn("membrane: 300%", text)
        self.assertIn("metabolizer: no cells", text)

    def test_warning_flags_roles_at_or_below_floor(self):
        w = World(MockBackend(0), Config(role_policy="warning"), seed=0)
        for role in ("membrane",) * 3 + ("metabolizer", "repairer", "repairer") + ("producer",) * 3:
            w._spawn(role, f"You are a {role} cell.", 0, None)
        w.cells[3].age = 26
        text = w._warnings()
        self.assertIn("- metabolizer: only 1 cell left; the last of them dies of old age in 4 ticks", text)
        self.assertIn("- repairer: only 2 cells left", text)
        self.assertNotIn("membrane", text)

    def test_critical_alerts_only_on_real_danger(self):
        w = World(MockBackend(0), Config(role_policy="critical"), seed=0)
        for role in ("membrane",) * 2 + ("metabolizer",) + ("repairer",) * 2 + ("producer",) * 2:
            w._spawn(role, f"You are a {role} cell.", 0, None)
        w.cells[3].age, w.cells[4].age = 25, 23   # both repairers die within 8 ticks
        self.assertEqual(w.critical_roles(), ["metabolizer", "repairer"])
        text = w._critical()
        self.assertIn("- metabolizer: 1 cell left; the last of them dies of old age in 30 ticks", text)
        self.assertIn("- repairer: 2 cells left; the last of them dies of old age in 7 ticks", text)
        self.assertNotIn("membrane", text)
        for c in w.cells:
            c.age = 0
        w._spawn("metabolizer", "You are a metabolizer cell.", 0, None)
        self.assertEqual(w._critical(), "")   # silent when nothing is in danger

    def test_decisions_are_logged_with_prompt_and_outcome(self):
        events = []
        w = World(FixedBackend("metabolizer"), Config(role_policy="critical", decay_rate=0.0,
                                                      perturbations_per_tick=0, start_pool=100),
                  seed=0, log=events.append)
        w._spawn("producer", "You are a producer cell.", 0, None)
        w._spawn("metabolizer", "You are a metabolizer cell.", 0, None)
        w.step()
        choice = next(e for e in events if e["event"] == "choice")
        self.assertIn("CRITICAL", choice["prompt"])
        self.assertEqual((choice["role"], choice["outcome"]), ("metabolizer", "birth_failed"))
        gate = next(e for e in events if e["event"] == "produce_tick")
        self.assertEqual(gate["decisions"], 1)

    def test_forecast_rebuilds_a_role_before_its_cohort_ages_out(self):
        w = World(MockBackend(0), Config(role_policy="forecast"), seed=0)
        for role in ROLES_ALL * 3:
            w._spawn(role, f"You are a {role} cell.", 0, None)
        for c in w.cells:
            if c.role == "membrane":
                c.age = 25          # all three membranes die within 10 ticks
        census = w.census()
        self.assertIsNone(w._most_demanded(census))      # demand sees 3 healthy membranes
        self.assertEqual(w._most_demanded(census, lead=10), "membrane")

    def test_garbage_genome_is_rejected(self):
        w = World(FixedBackend("no"), Config(decay_rate=0.0, perturbations_per_tick=0, start_pool=100), seed=0)
        w._spawn("producer", "You are a producer cell.", 0, None)
        w.step()
        self.assertEqual(len(w.cells), 1)
        self.assertEqual(w.totals["birth_failed"], 1)


if __name__ == "__main__":
    unittest.main()
