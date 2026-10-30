"""
Naturalist & Trail Intelligence Engine for TerraScout AI
Powered by Google Gemma 2 2B running 100% locally via Ollama.
Provides offline backcountry field briefings, botanical identification, and sensory trail guidance.
"""

import json
import urllib.request
import urllib.error
import time
from typing import Dict, Any, Optional, List

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
PREFERRED_MODELS = ["gemma2:2b", "gemma:2b", "gemma2", "llama3.2:1b", "llama3.2"]

NATURALIST_SYSTEM_PROMPT = """You are 'TerraScout', an expert backcountry naturalist, botanist, and outdoor trail companion.
Your mission is to help humans 'Touch Grass' — to spend the shortest possible time looking at a screen, and the maximum time immersed in nature, observing birds, flora, trees, fungi, and landscape geology safely and mindfully.

Core Guidelines:
1. Be crisp, observant, and deeply grounded in real ecology, seasonal phenology, and outdoor safety.
2. For foraging questions: ALWAYS prioritize caution. Clearly flag toxic lookalikes (e.g., Jack-o'-Lantern vs Chanterelle, Poison Hemlock vs Wild Carrot, False Morel). Never give ambiguous safety advice on wild mushrooms or berries.
3. Promote 'Screen Minimization': Give the hiker 3 distinct things to spot or listen for, then explicitly instruct them to pocket their device and step onto the trail.
4. Keep answers concise, vivid, and structured (under 200 words).
"""

FALLBACK_DISPATCHES = {
    "hiking": (
        "🌲 **Trail Dispatch: Temperate Woodland Hike**\n\n"
        "1. **What to Spot:** Look for Eastern White Pine clusters — soft needles always bunched in groups of 5. Check damp decaying oak stumps for golden oyster or turkey tail mushrooms.\n"
        "2. **What to Listen For:** Black-capped Chickadees. If you hear a rapid 'chick-a-dee-dee-dee' with many 'dee' syllables, look upwards into the hemlocks — a bird of prey or small owl is perched nearby.\n"
        "3. **Safety & Foraging Rule:** Avoid any umbrella-shaped wild carrot lookalikes with purple-blotched smooth stems (Poison Hemlock).\n\n"
        "👉 *Now put your device in your pocket, take three deep breaths of pine-rich air, and start moving!*"
    ),
    "foraging": (
        "🍄 **Trail Dispatch: Wild Foraging Expedition**\n\n"
        "1. **Target of the Day:** Wild Blackberries along sunny forest margins (all aggregate drupelets without milky sap are non-toxic). Check mossy hillsides for funnel-shaped Chanterelles.\n"
        "2. **Critical Identification:** Chanterelles possess BLUNT FORKED RIDGES running down the stem, not sharp paper-thin gills. Faint sweet apricot fragrance.\n"
        "3. **Leave No Trace:** Only harvest 1/3 of any healthy patch, use a breathable mesh basket or canvas bag to disperse spores as you hike.\n\n"
        "👉 *Screen time is over. Look down at the moss, look up at the oak canopy, and tread gently.*"
    ),
    "birding": (
        "🪶 **Trail Dispatch: Canopy Birding Walk**\n\n"
        "1. **Key Species:** Steller's Jays with dark indigo feathers and shaggy crests. Watch for woodpecker drum tempos on dead snag trees.\n"
        "2. **Aural Identification:** Listen for high-frequency warbler trills at dawn and dusk. Follow calls with your ears first before raising binoculars.\n"
        "3. **Field Practice:** Keep your silhouette low against the sky and step on the outside edge of your boot to walk silently over dry leaves.\n\n"
        "👉 *Turn your phone on silent, pocket it, and tune your senses to the canopy.*"
    )
}

class NaturalistEngine:
    def __init__(self, host: str = DEFAULT_OLLAMA_HOST):
        self.host = host.rstrip("/")
        self.active_model: Optional[str] = None
        self.is_connected = False
        self.detect_model()

    def detect_model(self) -> Optional[str]:
        """Detect available open-weight models in Ollama."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                
                for pref in PREFERRED_MODELS:
                    for m in models:
                        if m.startswith(pref) or pref in m:
                            self.active_model = m
                            self.is_connected = True
                            return self.active_model
                
                if models:
                    self.active_model = models[0]
                    self.is_connected = True
                    return self.active_model
        except Exception:
            self.is_connected = False
            self.active_model = None
            
        return None

    def get_status(self) -> Dict[str, Any]:
        """Return engine status and model info."""
        self.detect_model()
        return {
            "connected": self.is_connected,
            "host": self.host,
            "model": self.active_model or "None (Offline Native Rulebook Active)",
            "is_gemma": "gemma" in (self.active_model or "").lower(),
            "privacy_mode": "100% Backcountry Local — Zero Signal Required, Zero Telemetry"
        }

    def _query_local_model(self, prompt: str) -> Optional[str]:
        """Send prompt to local Ollama instance."""
        if not (self.is_connected and self.active_model):
            return None
            
        try:
            full_prompt = (
                f"<start_of_turn>user\n"
                f"{NATURALIST_SYSTEM_PROMPT}\n\n"
                f"{prompt}<end_of_turn>\n"
                f"<start_of_turn>model\n"
            )
            payload = json.dumps({
                "model": self.active_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.6,
                    "top_p": 0.9,
                    "max_tokens": 300
                }
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "").strip()
        except Exception:
            return None

    def generate_trail_dispatch(
        self,
        activity: str = "hiking",
        biome: str = "temperate_forest",
        season: str = "autumn",
        target_minutes: int = 45
    ) -> Dict[str, Any]:
        """Generate a 30-second field briefing designed to get the user off their phone."""
        start_time = time.time()
        prompt = (
            f"Generate a crisp, practical 30-second outdoor trail dispatch for a {target_minutes}-minute {activity} session "
            f"in a {biome} during {season}.\n"
            f"Give exactly:\n"
            f"1. Two specific wild flora, fungi, or birds to watch/listen for.\n"
            f"2. One critical safety or toxic lookalike warning.\n"
            f"3. A closing call to pocket the phone and step onto the trail immediately."
        )

        response_text = self._query_local_model(prompt)
        elapsed = round(time.time() - start_time, 2)

        if response_text:
            return {
                "dispatch": response_text,
                "model": self.active_model,
                "source": "local_open_weight_gemma",
                "latency_seconds": elapsed,
                "offline_guarantee": "Inference ran on local device silicon. Works in mountain valleys with zero bars."
            }

        # Offline fallback
        fallback = FALLBACK_DISPATCHES.get(activity.lower(), FALLBACK_DISPATCHES["hiking"])
        return {
            "dispatch": fallback,
            "model": "TerraScout-Offline-Field-Book",
            "source": "local_fallback",
            "latency_seconds": elapsed,
            "offline_guarantee": "100% Local Air-Gapped Fallback."
        }

    def identify_field_finding(
        self,
        description: str,
        category: str = "flora",
        terrain: str = "forest"
    ) -> Dict[str, Any]:
        """Field identification of a specimen observed on the trail."""
        start_time = time.time()
        prompt = (
            f"A hiker on the trail in {terrain} terrain describes observing this {category}:\n"
            f"\"{description}\"\n\n"
            f"As an expert naturalist, provide:\n"
            f"1. Most probable species identification (Common & Scientific names).\n"
            f"2. Key diagnostic confirmation markers.\n"
            f"3. Edibility / Toxicity Assessment (with mandatory toxic lookalike caution).\n"
            f"4. An ecological fun fact."
        )

        response_text = self._query_local_model(prompt)
        elapsed = round(time.time() - start_time, 2)

        if response_text:
            return {
                "analysis": response_text,
                "model": self.active_model,
                "source": "local_open_weight_gemma",
                "latency_seconds": elapsed,
                "offline_guarantee": "No GPS or trail location data transmitted outside your laptop."
            }

        # Offline fallback
        fallback_text = (
            f"🔍 **Offline Botanical Assessment: {description[:30]}...**\n\n"
            f"• **Category:** {category.title()} in {terrain.title()} habitat.\n"
            f"• **Field Protocol:** Cross-check against the offline compendium. Inspect stem attachment, gill structure (if mushroom), and leaf arrangement (alternate vs opposite).\n"
            f"• **Foraging Caution:** Never consume wild flora or fungi without 100% verification of spore print, stem cross-section, and absence of milky sap.\n"
            f"• **Ecological Role:** Pioneer species contributing to humus layer and mycorrhizal root networks."
        )
        return {
            "analysis": fallback_text,
            "model": "TerraScout-Offline-Field-Book",
            "source": "local_fallback",
            "latency_seconds": elapsed,
            "offline_guarantee": "100% Local Air-Gapped Fallback."
        }

    def generate_trail_reflection(
        self,
        sightings: List[str],
        duration_minutes: int,
        steps: int
    ) -> Dict[str, Any]:
        """Reflect on completed trail expedition and generate a field journal entry."""
        start_time = time.time()
        sightings_str = ", ".join(sightings) if sightings else "quiet wind in the trees and rustling leaves"
        prompt = (
            f"A hiker just completed a {duration_minutes}-minute outdoor walk ({steps} steps) and 'touched grass'.\n"
            f"They logged the following field observations: {sightings_str}.\n\n"
            f"Author a short, poetic, and rewarding field journal entry (2 paragraphs) summarizing their findings, "
            f"the mental benefits of getting off the screen, and the seasonal rhythm of the wild."
        )

        response_text = self._query_local_model(prompt)
        elapsed = round(time.time() - start_time, 2)

        if response_text:
            return {
                "journal_entry": response_text,
                "model": self.active_model,
                "source": "local_open_weight_gemma",
                "latency_seconds": elapsed
            }

        fallback_entry = (
            f"The trail quieted your thoughts after {duration_minutes} minutes immersed in the wild. "
            f"With each of your {steps} steps, the artificial glow of the screen faded into the organic texture "
            f"of tree bark, damp earth, and the scent of fallen leaves.\n\n"
            f"You noted: {sightings_str}. In a world driven by constant notifications, taking time to touch grass "
            f"is not leisure — it is an essential act of reclaiming our human senses. The forest will be waiting when you return."
        )
        return {
            "journal_entry": fallback_entry,
            "model": "TerraScout-Offline-Field-Book",
            "source": "local_fallback",
            "latency_seconds": elapsed
        }
