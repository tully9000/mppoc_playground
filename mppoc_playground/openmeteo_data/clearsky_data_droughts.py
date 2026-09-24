import pandas as pd
import pvlib
from pvlib.location import Location
import numpy as np
import pandas as pd


import yaml
from pathlib import Path

import matplotlib.pyplot as plt

config_path = Path(__file__).parent / "h2i_configs" 
with open(config_path / "plant_config.yaml", "r") as f:
    plant_config = yaml.safe_load(f)

with open(config_path / "tech_config.yaml", "r") as f:
    tech_config = yaml.safe_load(f)


# 1. Define location
lat = plant_config["sites"]["site"]["latitude"]
lon = plant_config["sites"]["site"]["longitude"]

pv_capacity = tech_config["technologies"]["solar"]["model_inputs"]["performance_parameters"]["pv_capacity_kWdc"]



# tz = 'America/Denver'
# tz = "Etc/GMT-5"
tz = "UTC"
site = Location(lat, lon, tz, name='Texas')
# site = Location(lat, lon, tz, name='Texas')

# 2. Define time range for one day
times = pd.date_range('1995-01-01 00:00:00', '1995-12-31 23:59:00', freq='1h', tz=tz)

# 3. Calculate clear sky data using the Ineichen model (default)
clearsky = site.get_clearsky(times, model='ineichen')


# fig, ax = plt.subplots(3, 1, sharex="all", layout="constrained")
# ax[0].plot(clearsky["ghi"].to_numpy())
# ax[1].plot(clearsky["dni"].to_numpy())
# ax[2].plot(clearsky["dhi"].to_numpy())





data = np.load(Path(__file__).parent / "hybrid_gen_data.npz")

wind_gen = data["wind"]
solar_gen = data["solar"]
hybrid_gen = data["hybrid"]

df_gen = pd.DataFrame(dict(wind=wind_gen, solar=solar_gen, hybrid=hybrid_gen))
date_range = pd.date_range(start="1995-01-01 00:00", end="2024-12-31 23:59", freq="h")
df_gen.index = date_range[~((date_range.month == 2) & (date_range.day == 29))]

df_gen_1995 = df_gen.loc["1995-01-01 00:00:00" : "1995-12-31 23:00:00"]


# pv_capacity = np.max(df_gen["solar"])

factor = 1/ tech_config['technologies']['solar']['model_inputs']['performance_parameters']['dc_ac_ratio']


fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")



ax[0].plot(np.clip(clearsky["ghi"].to_numpy() * factor* pv_capacity,a_min = 0, a_max = np.max(df_gen["solar"])))
ax[0].plot(df_gen_1995["solar"].to_numpy() )


print(clearsky.head())