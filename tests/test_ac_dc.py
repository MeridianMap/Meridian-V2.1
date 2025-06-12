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
assert any(abs(lon) < 2 and lat > 60 for lon,lat in pluto_horizon["geometry"]["coordinates"])
# 3️⃣ segment_break property exists and splits the curve
assert "segment_break" in pluto_horizon["properties"]
seg = pluto_horizon["properties"]["segment_break"]
coords = pluto_horizon["geometry"]["coordinates"]
assert 0 < seg < len(coords)
