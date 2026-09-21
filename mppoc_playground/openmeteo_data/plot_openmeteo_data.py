import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

data_path = Path(__file__).parent / "openmeteo_data.csv"


df = pd.read_csv(data_path, index_col=0)


fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")

ax[0].plot(df["wind_speed_100m"].to_numpy())
ax[1].plot(df["global_tilted_irradiance_instant"].to_numpy())

rolling_kw = dict(
    center=True
)

ax[0].plot(df["wind_speed_100m"].rolling(window = 4380, **rolling_kw).mean().to_numpy())
ax[1].plot(df["global_tilted_irradiance_instant"].rolling(window = 4380, **rolling_kw).mean().to_numpy())

ax[0].plot(df["wind_speed_100m"].rolling(window = 720, **rolling_kw).mean().to_numpy())
ax[1].plot(df["global_tilted_irradiance_instant"].rolling(window = 720, **rolling_kw).mean().to_numpy())


ax[0].plot(df["wind_speed_100m"].rolling(window = 24, **rolling_kw).mean().to_numpy())
ax[1].plot(df["global_tilted_irradiance_instant"].rolling(window = 24, **rolling_kw).mean().to_numpy())


# ax[0].plot(np.sort(df["wind_speed_100m"].to_numpy()))
# ax[1].plot(np.sort(df["global_tilted_irradiance_instant"].to_numpy()))

# plt.show()

[]
