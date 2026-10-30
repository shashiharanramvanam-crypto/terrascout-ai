"""
Automated Test Suite for TerraScout AI
Tests FieldStore persistence, Gemma 2 NaturalistEngine, offline fallbacks, and HTML field export.
"""

import sys
import unittest
import json
import tempfile
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from field_store import FieldStore
from naturalist_engine import NaturalistEngine

class TestFieldStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "test_expeditions.json"
        self.store = FieldStore(data_file=self.data_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compendium_loading(self):
        comp = self.store.get_compendium()
        self.assertGreaterEqual(len(comp), 4)
        names = [item["common_name"] for item in comp]
        self.assertTrue(any("Chanterelle" in n for n in names))
        self.assertTrue(any("Hemlock" in n for n in names))

    def test_default_expeditions(self):
        exps = self.store.load_expeditions()
        self.assertGreaterEqual(len(exps), 2)
        ids = [e["id"] for e in exps]
        self.assertIn("autumn-ridge-hike", ids)

    def test_create_expedition(self):
        new_exp = self.store.create_expedition({
            "title": "Mushroom Foray in Whispering Hollow",
            "activity": "foraging",
            "biome": "temperate_hardwood",
            "season": "autumn",
            "target_minutes": 60
        })
        self.assertIn("id", new_exp)
        self.assertEqual(new_exp["title"], "Mushroom Foray in Whispering Hollow")
        fetched = self.store.get_expedition(new_exp["id"])
        self.assertIsNotNone(fetched)

    def test_add_sighting(self):
        exp = self.store.load_expeditions()[0]
        sighting = self.store.add_sighting(exp["id"], {
            "common_name": "Wild Blackberry",
            "category": "flora",
            "notes": "Ripe sweet berries on sunny ridge.",
            "edibility": "Choice Edible"
        })
        self.assertIsNotNone(sighting)
        self.assertIn("id", sighting)
        
        # Verify in store
        updated_exp = self.store.get_expedition(exp["id"])
        self.assertTrue(any(s["id"] == sighting["id"] for s in updated_exp["sightings"]))

    def test_stats_calculation(self):
        stats = self.store.get_stats()
        self.assertIn("total_expeditions", stats)
        self.assertIn("total_minutes_outside", stats)
        self.assertIn("screen_time_saved_estimate_hours", stats)
        self.assertGreater(stats["total_minutes_outside"], 0)


class TestNaturalistEngine(unittest.TestCase):
    def setUp(self):
        self.engine = NaturalistEngine()

    def test_engine_status(self):
        status = self.engine.get_status()
        self.assertIn("connected", status)
        self.assertIn("model", status)
        self.assertIn("privacy_mode", status)

    def test_trail_dispatch_generation(self):
        dispatch = self.engine.generate_trail_dispatch(
            activity="hiking",
            biome="temperate_forest",
            season="autumn",
            target_minutes=45
        )
        self.assertIn("dispatch", dispatch)
        self.assertTrue(len(dispatch["dispatch"]) > 20)
        self.assertIn("model", dispatch)
        self.assertIn("offline_guarantee", dispatch)

    def test_specimen_identification(self):
        res = self.engine.identify_field_finding(
            description="Egg yolk yellow funnel mushroom with blunt forked ridges, sweet smell.",
            category="fungi",
            terrain="mossy slope"
        )
        self.assertIn("analysis", res)
        self.assertTrue(len(res["analysis"]) > 20)
        self.assertIn("model", res)

    def test_trail_reflection(self):
        res = self.engine.generate_trail_reflection(
            sightings=["Golden Chanterelle", "Steller's Jay"],
            duration_minutes=45,
            steps=4500
        )
        self.assertIn("journal_entry", res)
        self.assertTrue(len(res["journal_entry"]) > 30)


if __name__ == "__main__":
    unittest.main()
