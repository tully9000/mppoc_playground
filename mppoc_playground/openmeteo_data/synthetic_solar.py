from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def solar_declination_deg(day_of_year: np.ndarray) -> np.ndarray:
    """Return solar declination in degrees for each day of the year."""
    return 23.45 * np.sin(np.deg2rad(360.0 * (day_of_year - 81.0) / 365.25))
    # return 0 * np.sin(np.deg2rad(360.0 * (day_of_year - 81.0) / 365.25))


def compute_clear_sky_ghi(
    timestamps: pd.DatetimeIndex,
    latitude_deg: float = 40.0,
    max_ghi_wm2: float = 1000.0,
) -> np.ndarray:
    """Build a deterministic clear-sky GHI signal with daily and seasonal variation.

    This is a smooth geometry-driven profile only. It intentionally excludes cloud
    variability, weather anomalies, and solar resource droughts.
    """
    lat_rad = np.radians(latitude_deg)
    day_of_year = timestamps.dayofyear.to_numpy(dtype=float)
    hour_of_day = timestamps.hour.to_numpy(dtype=float)

    dec_deg = solar_declination_deg(day_of_year)
    dec_rad = np.radians(dec_deg)

    # Solar hour angle: 15° per hour relative to local solar noon.
    hour_angle_deg = (hour_of_day - 12.0) * 15.0
    hour_angle_rad = np.radians(hour_angle_deg)

    elevation = np.arcsin(
        np.sin(lat_rad) * np.sin(dec_rad)
        + np.cos(lat_rad) * np.cos(dec_rad) * np.cos(hour_angle_rad)
    )

    # Convert the solar elevation to a smooth, daytime-only clear-sky profile.
    # This gives a realistic daily cycle and seasonal modulation without weather noise.
    solar_factor = np.maximum(0.0, np.sin(elevation))
    # seasonal_factor = 0.75 + 0.25 * np.sin(np.deg2rad(360.0 * (day_of_year - 81.0) / 365.25))
    seasonal_factor = 0.9 + 0.05 * np.sin(np.deg2rad(360.0 * (day_of_year - 81.0) / 365.25))
    atmospheric_factor = 0.85 + 0.15 * np.cos(np.deg2rad(360.0 * (day_of_year - 172.0) / 365.25))

    ghi = max_ghi_wm2 * solar_factor * seasonal_factor * atmospheric_factor
    return np.clip(ghi, 0.0, max_ghi_wm2)


def generate_solar_profile(
    start: str | pd.Timestamp = "2024-01-01",
    latitude_deg: float = 40.0,
    capacity_mw: float = 100.0,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Return a one-year hourly solar generation profile.

    The profile is deterministic and smooth: daylight is modulated by solar geometry,
    while cloud cover and drought periods are intentionally omitted.
    """
    start_ts = pd.Timestamp(start)
    end_ts = start_ts + pd.DateOffset(years=1) - pd.Timedelta(hours=1)
    timestamps = pd.date_range(start=start_ts, end=end_ts, freq="h")

    ghi = compute_clear_sky_ghi(timestamps, latitude_deg=latitude_deg)
    profile_mw = capacity_mw * (ghi / 1000.0)

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "solar_ghi_wm2": ghi,
            "solar_generation_mw": profile_mw,
        }
    ).set_index("timestamp")

    if output_path is not None:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path)

    return df


if __name__ == "__main__":
    output_file = Path(__file__).with_name("synthetic_solar_profile.csv")
    profile = generate_solar_profile(
        start="2024-01-01",
        latitude_deg=5.0,
        capacity_mw=100.0,
        # output_path=output_file,
    )

    fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")
    ax[0].plot(profile["solar_ghi_wm2"].to_numpy())
    ax[1].plot(profile["solar_generation_mw"].to_numpy())

    print(f"Saved synthetic solar profile to: {output_file}")
    print(f"Rows: {len(profile)}")
    print(f"Peak hourly generation: {profile['solar_generation_mw'].max():.3f} MW")
    print(f"Annual energy: {profile['solar_generation_mw'].sum() * 1.0:.3f} MWh")
