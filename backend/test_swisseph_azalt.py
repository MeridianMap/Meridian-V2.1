import swisseph as swe

jd = swe.julday(2025, 5, 5, 12.0)
pid = swe.SUN
ut = 12.0
geopos = [0.0, 0.0, 0.0]
xx, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
print("xx[:3]:", xx[:3], type(xx[:3]))
print("geopos:", geopos, type(geopos))

print("Trying as list...")
try:
    print(swe.azalt(ut, swe.FLG_SWIEPH, geopos, xx[:3]))
except Exception as e:
    print("List error:", e)

print("Trying as tuple...")
try:
    print(swe.azalt(ut, swe.FLG_SWIEPH, tuple(geopos), tuple(xx[:3])))
except Exception as e:
    print("Tuple error:", e)

print("Trying as unpacked...")
try:
    print(swe.azalt(ut, swe.FLG_SWIEPH, tuple(geopos), xx[0], xx[1], xx[2]))
except Exception as e:
    print("Unpacked error:", e)