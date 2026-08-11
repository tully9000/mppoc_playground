import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TABLEAU_COLORS


import pywt

import os
from pathlib import Path

import openmdao.api as om

from mppoc_datacenter_measures.loaders.h2i import H2ITopology, load_h2i_case
from mppoc_datacenter_measures.metrics.events import detect_events, voll_weighted_severity
from mppoc_datacenter_measures.metrics.adequacy import lolp, lolh, lole, lolf, eue, neue


# results_root = Path(__file__).parent / "outputs"
results_root = Path("/Users/ztully/Documents/software/MPPOC/data/outputs")

year = 2010


year_root = results_root / f"DOE_{year}"


results = {}

# Get year from results root name
year = int(year_root.parts[-1].split("_")[-1])

cr = om.CaseReader(year_root / "cases.sql")
cases = cr.get_cases()
n_cases = len(cases)

results.update({year: {}})


idxs = [0, 3, 6, 9]

# Extract results
for i in range(n_cases):

    if not i in idxs:
        continue


    ts = load_h2i_case(
        str(year_root / "cases.sql"), case_index=i, topology=H2ITopology.slc()
    )
    events = detect_events(ts)
    results[year][f"ts_{i}"] = ts
    results[year][f"events_{i}"] = events
    results[year][f"case_{i}"] = cases[i]
    results[year][f"measures_{i}"] = dict(
        lolp = lolp(ts),
        lolh = lolh(ts),
        lole = lole(ts),
        lolf = lolf(ts),
        eue=eue(ts),
        neue=neue(ts)
    )


cmap = plt.colormaps["plasma"]



fig, ax = plt.subplots(len(idxs), 2, sharex="all", layout="constrained")



fig_io, ax_io = plt.subplots(len(idxs), 4, sharex="all", sharey="all", layout="constrained")


fill_kw = dict(
    step="post",
    alpha=0.5
)

hline_kw = dict(
    color="black",
    alpha=0.5,
    linewidth=0.5
)


for i in range(len(idxs)):
    ts = results[year][f"ts_{idxs[i]}"]
    events = results[year][f"events_{idxs[i]}"]
    omcase = results[year][f"case_{idxs[i]}"]
    measures = results[year][f"measures_{idxs[i]}"]


    ax_io[i, 0].fill_between(ts.df.index, np.zeros_like(ts.df["demand_kw"]), ts.df["wind_kw"], **fill_kw, label="wind", color=TABLEAU_COLORS["tab:blue"])
    ax_io[i, 1].fill_between(ts.df.index, np.zeros_like(ts.df["demand_kw"]), ts.df["solar_kw"], **fill_kw, label="wind", color=TABLEAU_COLORS["tab:orange"])
    ax_io[i, 2].fill_between(ts.df.index, np.zeros_like(ts.df["demand_kw"]), ts.df["gas_kw"], **fill_kw, label="wind", color=TABLEAU_COLORS["tab:green"])
    ax_io[i, 3].fill_between(ts.df.index, np.zeros_like(ts.df["demand_kw"]), ts.df["battery_kw"], **fill_kw, label="wind", color=TABLEAU_COLORS["tab:red"])

    ax_i3t = ax_io[i, 3].twinx()

    ax_i3t.plot(ts.df["battery_soc"], color="black")
    ax_i3t.set_ylim([0, 1])


    ax_io[i, 0].fill_between(ts.df.index, np.zeros_like(ts.df["shortfall_kw"]), -ts.df["shortfall_kw"], color="black", **fill_kw)


    ax[i, 0].fill_between(ts.df.index, np.zeros_like(ts.df["wind_kw"]), ts.df["wind_kw"], **fill_kw, label="wind")
    ax[i, 0].fill_between(ts.df.index, ts.df["wind_kw"], ts.df["wind_kw"] + ts.df["solar_kw"], **fill_kw, label="solar")
    ax[i, 0].fill_between(ts.df.index, ts.df["wind_kw"] + ts.df["solar_kw"], ts.df["wind_kw"] + ts.df["solar_kw"] + ts.df["gas_kw"], **fill_kw , label="gas")
    ax[i, 0].fill_between(ts.df.index, ts.df["wind_kw"] + ts.df["solar_kw"] + ts.df["gas_kw"], ts.df["wind_kw"] + ts.df["solar_kw"] + ts.df["gas_kw"] + ts.df["battery_kw"], **fill_kw , label="battery")

    ax[i, 0].plot(ts.df.index, ts.df["demand_kw"], color="black")


    # ax[i, 0].plot(ts.df["shortfall_kw"], color="black")
    ax[i, 0].fill_between(ts.df.index, np.zeros_like(ts.df["shortfall_kw"]), -ts.df["shortfall_kw"], color="black", **fill_kw)

    ax[i, 1].plot(ts.df["battery_soc"])

    ax[i, 1].axhline(0.9, **hline_kw)
    ax[i, 1].axhline(0.1, **hline_kw)

ax[0, 0].legend()






[]