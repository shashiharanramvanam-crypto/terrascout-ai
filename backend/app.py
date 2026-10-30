"""
Main HTTP Server & REST API for TerraScout AI
Backcountry trail dispatcher, offline naturalist engine, and field log.
Runs completely offline with standard Python 3 library.
"""

import os
import sys
import json
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

from naturalist_engine import NaturalistEngine
from field_store import FieldStore

BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

engine = NaturalistEngine()
store = FieldStore()

class TerraScoutHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def send_json(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def send_error_json(self, message: str, status: int = 400):
        self.send_json({"error": message}, status=status)

    def read_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/status":
            return self.send_json(engine.get_status())

        elif path == "/api/compendium":
            return self.send_json(store.get_compendium())

        elif path == "/api/stats":
            return self.send_json(store.get_stats())

        elif path == "/api/expeditions":
            return self.send_json(store.load_expeditions())

        elif path.startswith("/api/expeditions/") and not path.endswith("/export"):
            exp_id = path.replace("/api/expeditions/", "").strip()
            exp = store.get_expedition(exp_id)
            if exp:
                return self.send_json(exp)
            return self.send_error_json("Expedition not found", 404)

        elif path.startswith("/api/expeditions/") and path.endswith("/export"):
            parts = path.split("/")
            exp_id = parts[3]
            exp = store.get_expedition(exp_id)
            if not exp:
                return self.send_error_json("Expedition not found", 404)
            
            archive_html = self.generate_archival_html(exp)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="terrascout_{exp_id}_field_guide.html"')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(archive_html.encode("utf-8"))
            return

        if path == "" or path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self.read_body()

        if path == "/api/dispatch":
            activity = body.get("activity", "hiking")
            biome = body.get("biome", "temperate_forest")
            season = body.get("season", "autumn")
            minutes = int(body.get("target_minutes", 45))
            dispatch = engine.generate_trail_dispatch(activity, biome, season, minutes)
            return self.send_json(dispatch)

        elif path == "/api/identify":
            description = body.get("description", "")
            category = body.get("category", "flora")
            terrain = body.get("terrain", "forest")
            result = engine.identify_field_finding(description, category, terrain)
            return self.send_json(result)

        elif path == "/api/expeditions":
            created = store.create_expedition(body)
            return self.send_json(created, status=201)

        elif path.startswith("/api/expeditions/") and path.endswith("/sightings"):
            parts = path.split("/")
            exp_id = parts[3]
            sighting = store.add_sighting(exp_id, body)
            if sighting:
                return self.send_json(sighting, status=201)
            return self.send_error_json("Expedition not found", 404)

        elif path.startswith("/api/expeditions/") and path.endswith("/journal"):
            parts = path.split("/")
            exp_id = parts[3]
            exp = store.get_expedition(exp_id)
            if not exp:
                return self.send_error_json("Expedition not found", 404)

            sightings = [s.get("common_name", "wild specimen") for s in exp.get("sightings", [])]
            reflection = engine.generate_trail_reflection(
                sightings=sightings,
                duration_minutes=exp.get("elapsed_minutes", 30),
                steps=exp.get("steps", 3000)
            )
            store.update_expedition(exp_id, {
                "journal_entry": reflection.get("journal_entry", ""),
                "completed": True
            })
            return self.send_json(reflection)

        return self.send_error_json("Endpoint not found", 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self.read_body()

        if path.startswith("/api/expeditions/"):
            exp_id = path.replace("/api/expeditions/", "").strip()
            updated = store.update_expedition(exp_id, body)
            if updated:
                return self.send_json(updated)
            return self.send_error_json("Expedition not found", 404)

        return self.send_error_json("Endpoint not found", 404)

    def generate_archival_html(self, exp: Dict[str, Any]) -> str:
        """Create a 100% self-contained offline field guide archive."""
        title = exp.get("title", "Trail Expedition")
        activity = exp.get("activity", "hiking").replace("_", " ").title()
        biome = exp.get("biome", "forest").replace("_", " ").title()
        season = exp.get("season", "autumn").title()
        elapsed = exp.get("elapsed_minutes", 0)
        steps = exp.get("steps", 0)
        sightings = exp.get("sightings", [])
        journal = exp.get("journal_entry", "No journal recorded.")

        sightings_html = "".join([
            f"""<div class="sighting-card">
                <div class="sighting-header">
                  <span class="cat-badge">{s.get('category', 'specimen').upper()}</span>
                  <span class="timestamp">{s.get('spotted_at', '')}</span>
                </div>
                <h3>{s.get('common_name', 'Wild Specimen')} <em>({s.get('scientific_name', '')})</em></h3>
                <p><strong>Field Notes:</strong> {s.get('notes', '')}</p>
                <div class="edibility-tag">Status: {s.get('edibility', 'Observed')}</div>
            </div>"""
            for s in sightings
        ])

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Field Guide & Journal &mdash; {title}</title>
<style>
  body {{
    background: #0f1715;
    color: #e5ece9;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 40px 20px;
    display: flex;
    justify-content: center;
  }}
  .container {{
    max-width: 780px;
    width: 100%;
    background: #172421;
    border: 2px solid #52b788;
    box-shadow: 0 0 35px rgba(82, 183, 136, 0.25);
    border-radius: 12px;
    padding: 35px;
  }}
  h1 {{ color: #74c69d; margin: 0 0 8px 0; text-align: center; }}
  .meta-bar {{ text-align: center; color: #b7e4c7; font-size: 0.95rem; margin-bottom: 25px; }}
  .archival-badge {{
    background: #1b2e2a;
    border: 1px dashed #52b788;
    padding: 12px;
    border-radius: 6px;
    font-size: 0.85rem;
    color: #d8f3dc;
    margin-bottom: 30px;
    text-align: center;
  }}
  .stat-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 30px;
  }}
  .stat-box {{
    background: #213530;
    border: 1px solid rgba(82, 183, 136, 0.3);
    border-radius: 8px;
    padding: 12px;
    text-align: center;
  }}
  .stat-num {{ font-size: 1.6rem; color: #95d5b2; font-weight: bold; }}
  .stat-lbl {{ font-size: 0.75rem; color: #b7e4c7; text-transform: uppercase; }}
  .section-title {{
    color: #95d5b2;
    border-bottom: 1px solid rgba(82, 183, 136, 0.3);
    padding-bottom: 6px;
    margin-top: 25px;
    font-size: 1.2rem;
  }}
  .journal-box {{
    background: #1e302b;
    border-left: 4px solid #52b788;
    padding: 16px 20px;
    line-height: 1.6;
    border-radius: 4px;
    font-size: 1rem;
    color: #e2ece9;
    font-style: italic;
  }}
  .sighting-card {{
    background: #1b2e2a;
    border: 1px solid rgba(82, 183, 136, 0.2);
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 14px;
  }}
  .sighting-header {{ display: flex; justify-content: space-between; font-size: 0.75rem; }}
  .cat-badge {{ color: #74c69d; font-weight: bold; }}
  .timestamp {{ color: #95d5b2; }}
  .edibility-tag {{ font-size: 0.8rem; color: #d8f3dc; font-weight: 500; margin-top: 6px; }}
  footer {{
    margin-top: 40px;
    text-align: center;
    font-size: 0.8rem;
    color: #8da399;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="archival-badge">
    🌲 <strong>Offline Backcountry Field Record &mdash; TerraScout AI</strong><br>
    Logged without cellular reception or cloud tracking. 100% data sovereignty.
  </div>
  <h1>{title}</h1>
  <div class="meta-bar">
    {activity} &bull; {biome} &bull; {season} Season
  </div>

  <div class="stat-grid">
    <div class="stat-box">
      <div class="stat-num">{elapsed}m</div>
      <div class="stat-lbl">Time Off-Screen</div>
    </div>
    <div class="stat-box">
      <div class="stat-num">{steps}</div>
      <div class="stat-lbl">Trail Steps</div>
    </div>
    <div class="stat-box">
      <div class="stat-num">{len(sightings)}</div>
      <div class="stat-lbl">Specimens Logged</div>
    </div>
  </div>

  <div class="section-title">Naturalist Reflection</div>
  <div class="journal-box">
    {journal}
  </div>

  <div class="section-title">Field Observations ({len(sightings)})</div>
  {sightings_html if sightings else "<p style='color:#8da399;font-style:italic;'>No specimens logged during this walk.</p>"}

  <footer>
    TerraScout AI &bull; Built with Google Gemma 2 2B open weights &bull; Hacktoberfest 2026: Touch Grass
  </footer>
</div>
</body>
</html>"""


def run_server(port: int = 8081):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, TerraScoutHandler)
    print(f"\n=======================================================")
    print(f"🌲  TERRASCOUT AI — TOUCH GRASS (LOCAL FIELD SERVER) 🌲")
    print(f"=======================================================")
    print(f"✦ Active URL:       http://localhost:{port}")
    print(f"✦ Gemma Engine:     {engine.active_model or 'Offline Native Rulebook'}")
    print(f"✦ Backcountry Mode: 100% Offline (Zero Signal Required)")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping field server. Farewell!")
        httpd.server_close()


if __name__ == "__main__":
    port = 8081
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
