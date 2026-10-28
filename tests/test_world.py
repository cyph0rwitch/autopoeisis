import random
import unittest

from autopoiesis.llm import MockBackend
from autopoiesis.world import Config, Perturbation, World, corrupt


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

    def test_utilized_policy_rebuilds_thin_role_first(self):
        w = World(MockBackend(0), Config(role_policy="utilized"), seed=0)
        for role in ("membrane", "membrane", "metabolizer", "metabolizer", "repairer", "producer", "producer"):
            w._spawn(role, f"You are a {role} cell.", 0, None)
        w.usage.append({"membrane": (4, 4), "metabolizer": (1, 6), "repairer": (0, 1), "producer": (0, 2)})
        self.assertEqual(w._most_utilized(w.census()), "repairer")

    def test_utilized_policy_builds_most_loaded_role(self):
        w = World(MockBackend(0), Config(role_policy="utilized"), seed=0)
        for role in ("membrane", "metabolizer", "repairer", "producer") * 2:
            w._spawn(role, f"You are a {role} cell.", 0, None)
        w.usage.append({"membrane": (2, 4), "metabolizer": (1, 6), "repairer": (2, 2), "producer": (0, 2)})
        self.assertEqual(w._most_utilized(w.census()), "repairer")

    def test_feedback_reports_load_and_own_births(self):
        w = World(MockBackend(0), Config(role_policy="feedback", credit_delay=1, start_pool=0), seed=0)
        p = w._spawn("producer", "You are a producer cell.", 0, None)
        w._spawn("membrane", "You are a membrane cell.", 1, p.id)
        w.step()
        text = w._feedback(p)
        self.assertIn("membrane at tick 0", text)
        self.assertIn("a role had died out 1 ticks later", text)
        self.assertIn("producer: 0%", text)

    def test_garbage_genome_is_rejected(self):
        w = World(FixedBackend("no"), Config(decay_rate=0.0, perturbations_per_tick=0, start_pool=100), seed=0)
        w._spawn("producer", "You are a producer cell.", 0, None)
        w.step()
        self.assertEqual(len(w.cells), 1)
        self.assertEqual(w.totals["birth_failed"], 1)


if __name__ == "__main__":
    unittest.main()
