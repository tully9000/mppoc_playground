import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
from pathlib import Path
from scipy.ndimage import uniform_filter1d
import scipy.stats
import scipy.optimize

from mppoc_datacenter_measures.loaders.h2i import H2ITopology, load_h2i_case

cases_root = Path(__file__).parents[1] / "mppoc-datacenter-h2i/control_case"
case_path = cases_root / "single_case_uc/outputs/cases.sql"

ts = load_h2i_case(str(case_path), topology=H2ITopology.slc())

residual = ts.df["demand_kw"] - ts.df["solar_kw"] - ts.df["wind_kw"]


smoothed = uniform_filter1d(residual, size=24, mode="nearest")


fig, ax = plt.subplots(2, 1, layout="constrained")
ax = np.atleast_2d(ax).T

ax[0, 0].plot(ts.df.index, residual)

ax[1, 0].axhline(500e3)

start_end_offset = 4 * 7 * 24
# for width in np.arange(6, 4 * 7 * 24, 12):
for width in np.arange(6, 1 * 7 * 24, 24):
    smoothed = uniform_filter1d(residual, size=width, mode="nearest")
    ax[0, 0].plot(ts.df.index, smoothed)
    ax[1, 0].scatter(width, np.max(smoothed[start_end_offset:-start_end_offset]))
    ax[1, 0].scatter(width, np.min(smoothed[start_end_offset:-start_end_offset]))


ax[0, 0].plot(ts.df.index, ts.df["demand_kw"] - ts.df["wind_kw"] - ts.df["solar_kw"])
ax[0, 0].plot(ts.df.index, ts.df["battery_kw"])

ax[0, 0].fill_between(ts.df.index, ts.df["battery_kw"], ts.df["battery_kw"] + ts.df["gas_kw"])


# Try out Allen et al. indicators

# df_resample = ts.df.resample("24h").mean()
df_resample = ts.df


power = (df_resample["solar_kw"] + df_resample["wind_kw"]).to_numpy()
residual = df_resample["demand_kw"] - df_resample["solar_kw"] - df_resample["wind_kw"]
res = residual.to_numpy()

soc = df_resample["battery_soc"].to_numpy()
headroom = df_resample["headroom_kw"].to_numpy()

# load_deficit = df_resample["demand_kw"] - (df_resample["solar_kw"] + df_resample["wind_kw"] + df_resample["gas_kw"] + df_resample["battery_kw"])
shortfall = df_resample["shortfall_kw"].to_numpy()


# power = np.concatenate([power, np.random.rand(1000)])



n = power.shape[0]


cdf_power = scipy.stats.ecdf(power)
cdf_residual = scipy.stats.ecdf(res)

def find_threshold(cdf_func, threshold):
    def func(x):
        return cdf_func(x) - threshold
    return     scipy.optimize.fsolve(func, 2e4)

find_threshold(cdf_power.cdf.evaluate, 0.1)
find_threshold(cdf_power.cdf.evaluate, 0.05)
find_threshold(cdf_power.cdf.evaluate, 0.025)

find_threshold(cdf_residual.cdf.evaluate, 0.9)

def SREPI(p_t):
    return scipy.stats.norm.ppf(cdf_power.cdf.evaluate(p_t))


def SRLI(l_t):
    return scipy.stats.norm.ppf(cdf_residual.cdf.evaluate(l_t))


def prob2probit(prob):
    return scipy.stats.norm.ppf(prob)
    

powers = np.linspace(np.min(power), np.max(power), 1000)







# plt.plot(powers, cdf.cdf.evaluate(powers))
# plt.scatter(powers, cdf.cdf.evaluate(powers))

fig, ax = plt.subplots(1, 2, sharey="all", layout="constrained")
ax = np.atleast_2d(ax)

trans_00 = transforms.blended_transform_factory(ax[0, 0].transAxes, ax[0, 0].transData)
trans_01 = transforms.blended_transform_factory(ax[0, 1].transAxes, ax[0, 1].transData)
level_labels = ["extreme", "severe", "moderate"]


# for percent in np.array([0.025, 0.05, 0.1, 0.9, 0.95, 0.975]):
for i, percent in enumerate(np.array([0.025, 0.05, 0.1])):
    ax[0, 0].axhline(scipy.stats.norm.ppf(percent), color="black", linewidth=0.5)
    ax[0, 0].text(
        0.1, scipy.stats.norm.ppf(percent), level_labels[i], transform=trans_00
    )

    ax[0, 1].axhline(scipy.stats.norm.ppf(1 - percent), color="black", linewidth=0.5)
    ax[0, 1].text(
        0.1, scipy.stats.norm.ppf(1 - percent), level_labels[i], transform=trans_01
    )



srepi = SREPI(power)
srli = SRLI(res)



power_categories = np.zeros_like(power)
power_categories[np.where(srepi < prob2probit(0.1))[0]] = 1
power_categories[np.where(srepi < prob2probit(0.05))[0]] = 2
power_categories[np.where(srepi < prob2probit(0.025))[0]] = 3
n_power_droughts = len(np.where(srepi < prob2probit(0.1))[0])



residual_categories = np.zeros_like(res)
residual_categories[np.where(srli > prob2probit(0.9))[0]] = 1
residual_categories[np.where(srli > prob2probit(0.95))[0]] = 2
residual_categories[np.where(srli > prob2probit(0.975))[0]] = 3
n_residual_droughts = len(np.where(srli > prob2probit(0.9))[0])

print(n_power_droughts / len(power))
print(n_residual_droughts / len(res))



ax[0, 0].scatter(power, srepi)
ax[0, 0].set_ylabel("SREPI")
ax[0, 0].set_xlabel("RE power")

ax[0, 1].scatter(res, srli)
ax[0, 1].set_ylabel("SRLI")
ax[0, 1].set_xlabel("Load residual")




fig, ax = plt.subplots(5, 1, sharex="all", layout="constrained")
ax = np.atleast_2d(ax).T


ax[0, 0].plot(power)
ax[1, 0].plot(power_categories)


ax[0, 0].plot(res)
ax[1, 0].plot(residual_categories)


ax[2, 0].plot(soc)
ax[2, 0].set_ylabel("SOC")

ax[3, 0].plot(headroom)
ax[3, 0].set_ylabel("Headroom")

ax[4, 0].plot(shortfall)
ax[4, 0].set_ylabel("Shortfall")


fig.align_labels()

[]
