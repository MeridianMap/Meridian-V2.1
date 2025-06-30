import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
import json, pathlib, numpy as np
import importlib.util

spec = importlib.util.spec_from_file_location("line_ac_dc", os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend/line_ac_dc.py')))
line_ac_dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(line_ac_dc)
generate_horizon_lines = line_ac_dc.generate_horizon_lines

sample = json.loads(pathlib.Path(os.path.join(os.path.dirname(__file__), '..', 'backend', 'debug_chart.json')).read_text())
feats = generate_horizon_lines(sample, settings={"lat_steps": np.arange(-80, 81, 1)})
# 1️⃣ at least one HORIZON feature per classical planet
names = {f["properties"]["planet"] for f in feats}
for p in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn"]:
    assert p in names
# 2️⃣ Pluto HORIZON curve should cross 0° lon at high latitude (empirical sanity check)
pluto_horizon = next(f for f in feats
                 if f["properties"]["planet"]=="Pluto"
                 and f["properties"]["line_type"]=="HORIZON")
# Fix: Ensure coordinates are pairs before unpacking
coords = pluto_horizon["geometry"]["coordinates"]
if pluto_horizon["geometry"]["type"] == "LineString":
    coord_iter = coords
elif pluto_horizon["geometry"]["type"] == "MultiLineString":
    coord_iter = [pt for seg in coords for pt in seg]
else:
    coord_iter = []
assert any(abs(lon) < 2 and lat > 60 for lon,lat in coord_iter)
# 3️⃣ segments property exists and splits the curve
segments = pluto_horizon["properties"].get("segments")
assert segments is not None and isinstance(segments, list) and len(segments) >= 2
ac_end = segments[0]["end"]
dc_start = segments[1]["start"]
assert isinstance(ac_end, int) and isinstance(dc_start, int) and 0 < ac_end < len(coord_iter)
