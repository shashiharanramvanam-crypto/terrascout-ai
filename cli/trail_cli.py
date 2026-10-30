"""
Offline Trail CLI & Backcountry Oracle for TerraScout AI
Command-line field companion for backpacker laptops in zero-signal wilderness.
"""

import sys
import time
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from naturalist_engine import NaturalistEngine
from field_store import FieldStore

# ANSI Color codes
GREEN = "\033[38;5;71m"
EMERALD = "\033[38;5;120m"
AMBER = "\033[38;5;214m"
BROWN = "\033[38;5;137m"
GRAY = "\033[38;5;244m"
CYAN = "\033[38;5;51m"
RED = "\033[38;5;196m"
BOLD = "\033[1m"
RESET = "\033[0m"

BANNER = f"""
{GREEN}
       /\\
      /  \\  /\\
     / /\\ \\/  \\      {EMERALD}TERRASCOUT AI : TOUCH GRASS{GREEN}
    / /  \\ \\/\\ \\     {BROWN}Offline Field Naturalist & Trail Dispatcher{GREEN}
   / / /\\ \\ \\ \\ \\    {GRAY}Powered by Google Gemma 2B Open Weights{RESET}
"""

def typewriter(text: str, delay: float = 0.012, color: str = GREEN):
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RESET + "\n")

def main():
    os.system("") # Enable ANSI on Windows console
    print(BANNER)

    engine = NaturalistEngine()
    store = FieldStore()

    status = engine.get_status()
    print(f"{GRAY}[Status: Model: {status['model']} | Connected: {status['connected']} | Mode: {status['privacy_mode']}]{RESET}\n")
    print(f"{EMERALD}Welcome to TerraScout!{RESET} Designed to minimize your screen time and maximize your wilderness experience.")
    print(f"{GRAY}Type 'help' for commands, or type 'dispatch' to get your 30-second field briefing and step outside.{RESET}\n")

    while True:
        try:
            cmd = input(f"{GREEN}🌲 [TerraScout]{RESET} > ").strip()
            if not cmd:
                continue

            cmd_lower = cmd.lower()

            if cmd_lower in ["exit", "quit", "q"]:
                typewriter("Pocket your phone, breathe in the fresh air, and enjoy the trail. Farewell!", 0.015, EMERALD)
                break

            elif cmd_lower == "help":
                print(f"""
{BOLD}Backcountry Commands:{RESET}
  {EMERALD}dispatch{RESET}             - Generate a 30-second field briefing & go touch grass
  {EMERALD}identify <specimen>{RESET}  - Identify wild plant, bird call, or mushroom with toxicity assessment
  {EMERALD}compendium{RESET}           - Browse offline catalog of edible vs toxic species
  {EMERALD}expeditions{RESET}          - View logged trail sessions & screen time saved
  {EMERALD}status{RESET}               - Check local Gemma engine status & offline guarantee
  {EMERALD}clear{RESET}                - Clear terminal screen
""")

            elif cmd_lower.startswith("dispatch"):
                print(f"\n{AMBER}[Consulting local Gemma 2 naturalist engine...]{RESET}")
                res = engine.generate_trail_dispatch(activity="hiking", biome="temperate_forest", season="autumn")
                print(f"\n{res['dispatch']}\n")
                print(f"{GRAY}[Latency: {res['latency_seconds']}s | Model: {res['model']} | {res['offline_guarantee']}]{RESET}\n")

            elif cmd_lower.startswith("identify"):
                parts = cmd.split(" ", 1)
                if len(parts) < 2:
                    query = input("Describe what you observed (color, gills, leaves, calls): ").strip()
                else:
                    query = parts[1]

                print(f"\n{AMBER}[Analyzing specimen across offline botanical knowledge base...]{RESET}")
                res = engine.identify_field_finding(query)
                print(f"\n{res['analysis']}\n")
                print(f"{GRAY}[Latency: {res['latency_seconds']}s | Model: {res['model']}]{RESET}\n")

            elif cmd_lower == "compendium":
                items = store.get_compendium()
                print(f"\n{BOLD}Offline Botanical & Wildlife Safety Compendium ({len(items)} entries):{RESET}")
                for it in items:
                    tag_color = RED if "toxic" in it.get("category", "") or "POISON" in it.get("edibility", "") else EMERALD
                    print(f"  {tag_color}✦ [{it.get('category').upper()}]{RESET} {BOLD}{it.get('common_name')}{RESET} ({it.get('scientific_name')})")
                    print(f"    {GRAY}Status: {it.get('edibility')} | Season: {it.get('season')}{RESET}")
                    if it.get("toxic_lookalike"):
                        print(f"    {AMBER}⚠️ Toxic Lookalike: {it.get('toxic_lookalike')}{RESET}")
                print()

            elif cmd_lower == "expeditions":
                stats = store.get_stats()
                print(f"\n{BOLD}Touch Grass Telemetry:{RESET}")
                print(f"  Total Expeditions:        {stats['total_expeditions']}")
                print(f"  Total Time Outside:       {EMERALD}{stats['total_minutes_outside']} minutes ({stats['total_hours_outside']} hours){RESET}")
                print(f"  Total Trail Steps:        {stats['total_steps']}")
                print(f"  Screen Time Saved (Est):  {AMBER}{stats['screen_time_saved_estimate_hours']} hours{RESET}\n")

            elif cmd_lower == "status":
                s = engine.get_status()
                print(f"\n{BOLD}Engine Telemetry:{RESET}")
                print(f"  Model:            {s['model']}")
                print(f"  Ollama Host:      {s['host']}")
                print(f"  Connected:        {s['connected']}")
                print(f"  Gemma 2 Active:   {s['is_gemma']}")
                print(f"  Offline Mode:     {EMERALD}{s['privacy_mode']}{RESET}\n")

            elif cmd_lower == "clear":
                os.system("cls" if os.name == "nt" else "clear")
                print(BANNER)

            else:
                # Direct naturalist query
                print(f"\n{AMBER}[Thinking...]{RESET}")
                res = engine.identify_field_finding(cmd)
                print(f"\n{res['analysis']}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{GRAY}Exiting trail companion... Go touch grass!{RESET}")
            break

if __name__ == "__main__":
    main()
