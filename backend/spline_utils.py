"""
Spline utilities for astrocartography and geospatial curves.

Exports:
- parametric_spline: Fit a parametric spline to longitude/latitude arrays, handling dateline crossing, non-uniform sampling, and periodicity.

This is the single canonical implementation; all code should import from backend.spline_utils.
"""
from typing import Tuple
import numpy as np
from scipy.interpolate import splprep, splev
import pyproj

def parametric_spline(lons: np.ndarray, lats: np.ndarray, density: int = 300) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fit a parametric spline to longitude and latitude arrays, handling dateline crossing and non-uniform sampling.

    Parameters
    ----------
    lons : array-like
        Longitudes in degrees (geographic, may cross ±180°; unwrapped internally).
    lats : array-like
        Latitudes in degrees (geographic, may cross ±90°; unwrapped internally).
    density : int, optional
        Number of points in the output spline (default: 300).

    Returns
    -------
    dense_lons : np.ndarray
        Interpolated longitudes (degrees, wrapped to [–180°, 180°] for plotting).
    dense_lats : np.ndarray
        Interpolated latitudes (degrees).
    """
    lons = np.asarray(lons, dtype=float)
    lats = np.asarray(lats, dtype=float)
    if len(lons) > 1:
        geod = pyproj.Geod(ellps="WGS84")
        dists = [0.0]
        for i in range(1, len(lons)):
            _, _, dist = geod.inv(lons[i-1], lats[i-1], lons[i], lats[i])
            dists.append(dists[-1] + dist)
        dists = np.array(dists)
        # Defensive: sort by distance if not monotonic
        if not np.all(np.diff(dists) >= 0):
            idx = np.lexsort((lats, lons, dists))
            lons = lons[idx]
            lats = lats[idx]

    # Early exit for empty or mismatched input
    if len(lons) == 0 or len(lats) == 0 or len(lons) != len(lats):
        return np.array([]), np.array([])
    # Unwrap longitudes in radians to avoid 360° jumps
    lons_rad = np.unwrap(np.radians(lons))
    lons_unwrapped = np.degrees(lons_rad)
    # Unwrap latitudes in radians to avoid 180° jumps
    lats_rad = np.unwrap(np.radians(lats))
    lats_unwrapped = np.degrees(lats_rad)
    # Parameterize by cumulative great-circle distance
    geod = pyproj.Geod(ellps="WGS84")
    dists = [0.0]
    for i in range(1, len(lons_unwrapped)):
        _, _, dist = geod.inv(lons_unwrapped[i-1], lats[i-1], lons_unwrapped[i], lats[i])
        dists.append(dists[-1] + dist)
    dists = np.array(dists)
    if dists[-1] == 0:
        dists = np.linspace(0, 1, len(lons_unwrapped))
    else:
        dists /= dists[-1]
    # Detect if path is periodic (spans >300° in longitude)
    per = np.abs(lons_unwrapped[-1] - lons_unwrapped[0]) > 300
    lons_fit = lons_unwrapped
    lats_fit = lats
    if per:
        lons_fit = np.append(lons_unwrapped, lons_unwrapped[0])
        lats_fit = np.append(lats, lats[0])
        dists = np.append(dists, 1.0)
    # Fallback for short arrays after periodic handling
    k = 3  # cubic spline degree
    if len(lons_fit) < (k + 1):
        if len(lons_fit) == 1:
            return np.array(lons_fit), np.array(lats_fit)
        unew = np.linspace(0, 1, density)
        lons_interp = np.interp(unew, np.linspace(0, 1, len(lons_fit)), lons_fit)
        lats_interp = np.interp(unew, np.linspace(0, 1, len(lats_fit)), lats_fit)
        lons_interp = ((lons_interp + 180) % 360) - 180
        return lons_interp, lats_interp
    try:
        tck, _ = splprep([lons_fit, lats_fit], u=dists, s=0, per=per, k=k)
        unew = np.linspace(0, 1, density)
        dense_lons, dense_lats = splev(unew, tck)
        # Wrap longitudes to [-180, 180] for plotting
        dense_lons = ((dense_lons + 180) % 360) - 180
        return dense_lons, dense_lats
    except Exception:
        # Fallback: linear interpolation
        if len(lons_fit) == 1:
            return np.array(lons_fit), np.array(lats_fit)
        unew = np.linspace(0, 1, density)
        lons_interp = np.interp(unew, np.linspace(0, 1, len(lons_fit)), lons_fit)
        lats_interp = np.interp(unew, np.linspace(0, 1, len(lats_fit)), lats_fit)
        lons_interp = ((lons_interp + 180) % 360) - 180
        return lons_interp, lats_interp
