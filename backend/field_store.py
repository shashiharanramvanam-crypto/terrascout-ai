"""
Local Field Store for TerraScout AI
Persists trail expeditions, offline botanical compendium, and field sightings in local JSON.
Guarantees complete location sovereignty — secret mushroom spots and backcountry trails stay on-device.
"""

import os
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
COMPENDIUM_FILE = DATA_DIR / "flora_fauna.json"
EXPEDITIONS_FILE = DATA_DIR / "expeditions.json"

DEFAULT_EXPEDITIONS: List[Dict[str, Any]] = [
  {
    "id": "autumn-ridge-hike",
    "title": "Autumn Ridge Trail & Foraging Walk",
    "activity": "hiking",
    "biome": "temperate_hardwood",
    "season": "autumn",
    "target_minutes": 45,
    "elapsed_minutes": 52,
    "steps": 4820,
    "completed": True,
    "created_at": "2026-10-30T09:30:00Z",
    "notes": "Crisp morning air, 48°F. Deep leaf litter, quiet canopy.",
    "sightings": [
      {
        "id": "s1",
        "common_name": "Golden Chanterelle",
        "scientific_name": "Cantharellus cibarius",
        "category": "fungi",
        "notes": "Cluster of 4 found beneath mature beech tree on north-facing mossy slope. Forked false gills verified.",
        "edibility": "Choice Edible",
        "spotted_at": "09:48 AM"
      },
      {
        "id": "s2",
        "common_name": "Steller's Jay",
        "scientific_name": "Cyanocitta stelleri",
        "category": "bird",
        "notes": "Perched on a Douglas fir branch mimicking a hawk scream. Bold crest visible.",
        "edibility": "Wildlife / Birding",
        "spotted_at": "10:05 AM"
      }
    ],
    "journal_entry": "Fifty-two minutes completely untethered from the digital noise. The forest floor was painted in ochre and amber. The sweet, faint apricot aroma of the chanterelles was unmistakable once discovered under the wet oak leaves."
  },
  {
    "id": "creekside-run",
    "title": "Creekside 5K Nature Run & Birding",
    "activity": "trail_running",
    "biome": "riparian_wetland",
    "season": "autumn",
    "target_minutes": 30,
    "elapsed_minutes": 32,
    "steps": 4150,
    "completed": True,
    "created_at": "2026-10-29T16:15:00Z",
    "notes": "Fast-paced dirt track along babbling brook.",
    "sightings": [
      {
        "id": "s3",
        "common_name": "Black-capped Chickadee",
        "scientific_name": "Poecile atricapillus",
        "category": "bird",
        "notes": "Flock of six moving through willow thickets, vocalizing clear 'fee-bee' whistles.",
        "edibility": "Songbird",
        "spotted_at": "04:30 PM"
      }
    ],
    "journal_entry": "Running through the cool mist over roots and river rocks. No music, no podcast — just the cadence of feet against soil and chickadee warning calls high in the alder trees."
  }
]

class FieldStore:
    def __init__(self, data_file: Path = EXPEDITIONS_FILE):
        self.data_file = data_file
        self.ensure_storage()

    def ensure_storage(self):
        """Ensure data directories exist and seed default expeditions."""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self.save_expeditions(DEFAULT_EXPEDITIONS)

    def get_compendium(self) -> List[Dict[str, Any]]:
        """Load pre-indexed botanical & wildlife compendium."""
        try:
            if COMPENDIUM_FILE.exists():
                with open(COMPENDIUM_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def load_expeditions(self) -> List[Dict[str, Any]]:
        """Load all recorded trail expeditions from local disk."""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_EXPEDITIONS

    def save_expeditions(self, expeditions: List[Dict[str, Any]]):
        """Persist expeditions to disk."""
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(expeditions, f, indent=2, ensure_ascii=False)

    def get_expedition(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Find an expedition by ID."""
        for e in self.load_expeditions():
            if e["id"] == exp_id:
                return e
        return None

    def create_expedition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new trail expedition."""
        expeditions = self.load_expeditions()
        new_id = data.get("id") or f"trail-{str(uuid.uuid4())[:8]}"
        new_exp = {
            "id": new_id,
            "title": data.get("title", "New Trail Expedition"),
            "activity": data.get("activity", "hiking"),
            "biome": data.get("biome", "temperate_forest"),
            "season": data.get("season", "autumn"),
            "target_minutes": int(data.get("target_minutes", 45)),
            "elapsed_minutes": int(data.get("elapsed_minutes", 0)),
            "steps": int(data.get("steps", 0)),
            "completed": data.get("completed", False),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "notes": data.get("notes", "Beginning the expedition with eyes and ears open."),
            "sightings": data.get("sightings", []),
            "journal_entry": data.get("journal_entry", "")
        }
        expeditions.insert(0, new_exp)
        self.save_expeditions(expeditions)
        return new_exp

    def add_sighting(self, exp_id: str, sighting: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a flora/fauna observation to an expedition."""
        exp = self.get_expedition(exp_id)
        if not exp:
            return None
        sighting["id"] = sighting.get("id") or f"s-{str(uuid.uuid4())[:6]}"
        if "spotted_at" not in sighting:
            sighting["spotted_at"] = datetime.datetime.now().strftime("%I:%M %p")
        exp.setdefault("sightings", []).append(sighting)
        self.update_expedition(exp_id, {"sightings": exp["sightings"]})
        return sighting

    def update_expedition(self, exp_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields on an expedition."""
        expeditions = self.load_expeditions()
        for i, e in enumerate(expeditions):
            if e["id"] == exp_id:
                expeditions[i].update(updates)
                self.save_expeditions(expeditions)
                return expeditions[i]
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Calculate total outdoor time and grass touched."""
        exps = self.load_expeditions()
        total_minutes = sum(e.get("elapsed_minutes", 0) for e in exps)
        total_steps = sum(e.get("steps", 0) for e in exps)
        total_sightings = sum(len(e.get("sightings", [])) for e in exps)
        return {
            "total_expeditions": len(exps),
            "total_minutes_outside": total_minutes,
            "total_hours_outside": round(total_minutes / 60, 1),
            "total_steps": total_steps,
            "total_sightings": total_sightings,
            "screen_time_saved_estimate_hours": round((total_minutes * 1.25) / 60, 1)
        }
