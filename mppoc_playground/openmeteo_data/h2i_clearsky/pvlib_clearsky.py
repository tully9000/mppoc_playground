from datetime import datetime
from attrs import field, define
import numpy as np
from pathlib import Path
import pandas as pd

try:
    import pvlib
except Exception:  # pragma: no cover - pvlib optional
    pvlib = None

from openmdao.utils import units

from h2integrate.core.validators import range_val
from h2integrate.resource.solar.solar_resource_base import SolarResourceBaseAPIModel
from h2integrate.resource.resource_base import ResourceBaseAPIConfig

class PVLibClearSkyResourceAPIConfig(ResourceBaseAPIConfig):
    resource_year: int = field(converter=int, validator=range_val(1940, datetime.now().year - 1))
    resource_dir: Path | str | None = field(default=None)



class PVLibClearSkyResource(SolarResourceBaseAPIModel):
    """Calculate clear-sky solar irradiance using pvlib.

    This class reads site information from the model config (latitude, longitude,
    timezone, elevation) and produces time series for `ghi`, `dni`, `dhi`, and
    related variables expected by `SolarResourceBaseAPIModel`.

    pvlib is an optional dependency; if it's not available an ImportError will
    be raised when `compute_clearsky` is called.
    """

    def setup(self):
        resource_specs = self.helper_setup_method()
        self.config = PVLibClearSkyResourceAPIConfig.from_dict(resource_specs,            additional_cls_name=self.__class__.__name__, strict=False)

        super().setup()

        yr = resource_specs["resource_year"]
        times = pd.date_range(f'{yr}-01-01 00:00:00', f'{yr}-12-31 23:59:00', freq='1h')
        # data = self.get_data()
        data = self.compute_clearsky(times = times, site_info=resource_specs)



        self.resource_data = data

        # add resource data dictionary as an out
        self.add_discrete_output(
            "solar_resource_data", val=data, desc="Dict of solar resource data"
        )

    def compute_clearsky(self, times, site_info, model="ineichen", **kwargs):
        """Compute clear-sky irradiance for given times and site.

        Args:
            times (pandas.DatetimeIndex): timezone-aware times for the site.
            site_info (dict): must contain `latitude`, `longitude`, `tz`, and `elevation`.
            model (str): pvlib clearsky model name (ineichen, haurwitz, simplified_solis, ineichen_perez)
            **kwargs: passed to pvlib.location.Location.get_clearsky

        Returns:
            dict: keys include `ghi`, `dni`, `dhi`, and `solar_zenith_angle` as numpy arrays.
        """
        if pvlib is None:
            raise ImportError("pvlib is required for PVLibClearSkyResource but is not installed")

        # lazy import of pandas to avoid hard dependency when not used
        import pandas as pd

        lat = site_info.get("latitude")
        lon = site_info.get("longitude")
        tz = site_info.get("tz") or site_info.get("timezone")
        elev = site_info.get("elevation", 0.0)

        if lat is None or lon is None or tz is None:
            raise ValueError("site_info must include 'latitude', 'longitude', and 'tz'/'timezone'")

        location = pvlib.location.Location(latitude=lat, longitude=lon, tz=tz, altitude=elev)

        # ensure times are a timezone-aware DatetimeIndex
        if not isinstance(times, pd.DatetimeIndex):
            times = pd.DatetimeIndex(times)
        if times.tz is None:
            times = times.tz_localize(tz)
        else:
            times = times.tz_convert(tz)

        clearsky = location.get_clearsky(times, model=model, **kwargs)

        # solar position for zenith angle
        solpos = location.get_solarposition(times)

        out = {
            "ghi": np.asarray(clearsky["ghi"]),
            "dni": np.asarray(clearsky.get("dni", np.zeros(len(times)))),
            "dhi": np.asarray(clearsky.get("dhi", np.zeros(len(times)))),
            "wind_speed": np.ones(len(times)) * 4,
            "temperature": np.ones(len(times)) * 6,
            # "pressure": np.ones(len(times)) * 945,
            # "dew_point": np.ones(len(times)) * -4.5,
            "solar_zenith_angle": np.asarray(solpos["zenith"]),
            "site_tz": tz,
            "data_tz": tz,
            "site_lat": self.config.latitude,
            "site_lon": self.config.longitude,
            "elevation":644.0,
            "year": times.year.to_numpy(),
            "month": times.month.to_numpy(),
            "day": times.day.to_numpy(),       # Day of month
            "hour": times.hour.to_numpy(),    # hour of day
            "minute": times.minute.to_numpy() + 30
        }

        return out

    def get_resource(self, config, times):
        """High-level API to produce resource dict compatible with H2Integrate.

        Args:
            config (dict): configuration mapping containing site metadata under
                keys like `site.latitude`, `site.longitude`, `site.tz`, `site.elevation`.
            times (pandas.DatetimeIndex): timezone-aware index for which to compute resource.

        Returns:
            tuple: `(data, data_units)` where `data` is a dict of arrays and
            `data_units` maps variable names to units strings compatible with
            `SolarResourceBaseAPIModel.compare_units_and_correct`.
        """
        # extract site info from config (support dotted and nested dicts)
        def _get(cfg, *keys):
            for k in keys:
                if k in cfg:
                    return cfg[k]
            # support nested dict: cfg.get('site', {}).get('latitude')
            site = cfg.get("site", {})
            for k in keys:
                if k in site:
                    return site[k]
            return None

        site_info = {
            "latitude": _get(config, "latitude", "site.latitude", "lat"),
            "longitude": _get(config, "longitude", "site.longitude", "lon"),
            "tz": _get(config, "tz", "timezone", "site.tz"),
            "elevation": _get(config, "elevation", "site.elevation", "altitude") or 0.0,
        }

        clearsky = self.compute_clearsky(times, site_info)

        data = {
            "ghi": clearsky["ghi"],
            "dni": clearsky["dni"],
            "dhi": clearsky["dhi"],
            "solar_zenith_angle": clearsky["solar_zenith_angle"],
        }

        data_units = {k: self.output_vars_to_units.get(k, "") for k in data.keys()}

        # ensure units are correct (convert if necessary)
        data, data_units = self.compare_units_and_correct(data, data_units)

        return data, data_units
