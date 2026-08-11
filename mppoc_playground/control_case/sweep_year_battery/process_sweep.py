import numpy as np
import matplotlib.pyplot as plt

import pywt

import os
from pathlib import Path

import openmdao.api as om

from mppoc_datacenter_measures.loaders.h2i import H2ITopology, load_h2i_case
from mppoc_datacenter_measures.metrics.events import (
    detect_events,
    voll_weighted_severity,
)
from mppoc_datacenter_measures.metrics.adequacy import lolp, lolh, lole, lolf, eue, neue

results_root = Path(__file__).parent / "outputs"


results = {}

for year_root in results_root.iterdir():
    if year_root.name.startswith("."):
        continue

    # Get year from results root name
    year = int(year_root.parts[-1].split("_")[-1])

    cr = om.CaseReader(year_root / "cases.sql")
    cases = cr.get_cases()
    n_cases = len(cases)

    results.update({year: {}})

    # Extract results
    for i in range(n_cases):
        ts = load_h2i_case(
            str(year_root / "cases.sql"), case_index=i, topology=H2ITopology.slc()
        )
        events = detect_events(ts)
        # results[year][f"ts_{i}"] = ts
        # results[year][f"events_{i}"] = events
        # results[year][f"case_{i}"] = cases[i]
        # results[year][f"measures_{i}"] = dict(
        #     lolp = lolp(ts),
        #     lolh = lolh(ts),
        #     lole = lole(ts),
        #     lolf = lolf(ts),
        #     eue=eue(ts),
        #     neue=neue(ts)
        # )

        results[year].update(
            {
                i: {
                    "ts": ts,
                    "events": events,
                    "case": cases[i],
                    "measures": dict(
                        lolp=lolp(ts),
                        lolh=lolh(ts),
                        lole=lole(ts),
                        lolf=lolf(ts),
                        eue=eue(ts),
                        neue=neue(ts),
                    ),
                }
            }
        )

results = dict(sorted(results.items()))


fig, ax = plt.subplots(2, 2, sharex="all", layout="constrained", figsize=(8, 4))
ax = np.atleast_2d(ax)

ax[0, 0].axhline(0, color="black", linewidth=0.5, alpha=0.5)

for k, v in results.items():

    # events_keys = [k for k in v.keys() if k.startswith("events")] 
    # n_events = [v[ek].shape[0] for ek in events_keys]
    n_events = [vv["events"].shape[0] for k, vv in v.items()]

    # case_keys = [k for k in v.keys() if k.startswith("case")]
    # lcoe = [v[ck].outputs["finance_subgroup_electricity.LCOE"] for ck in case_keys]
    lcoe = [vv["case"].outputs["finance_subgroup_electricity.LCOE"] for k, vv in v.items()]

    # duration = [v[ek]["duration_hours"].sum() for ek in events_keys]
    # total_energy = [v[ek]["energy_mwh"].sum() for ek in events_keys]
    duration = [vv["events"]["duration_hours"].sum() for k, vv in v.items()]
    total_energy = [vv["events"]["energy_mwh"].sum() for k, vv in v.items()]

    x = np.array([vv['case'].inputs["battery.storage_capacity"] for k, vv in v.items()])
    offset = np.array([vv['case'].inputs["plant.natural_gas_plant.NaturalGasPerformanceModel.system_capacity"] for k, vv in v.items()]) 

    offset = offset / (np.max(offset)) * 0.1 * np.max(x)



    # x = np.arange(len(n_events))

    # ax[0, 0].plot(x, n_events)
    ax[0, 0].scatter(x+offset, n_events, label=k)

    # ax[1, 0].plot(x, lcoe)
    ax[1, 0].scatter(x+offset, lcoe, label=k)

    # ax[0, 1].plot(x, duration)
    ax[0, 1].scatter(x+offset, duration, label="k")

    # ax[1, 1].plot(x, total_energy)
    ax[1, 1].scatter(x+offset, total_energy, label="k")


ax[0, 0].legend(ncols=2, loc="upper right", bbox_to_anchor=(1.05, 1.1))
ax[1, 0].set_xlabel("Battery capacity [kWh]")
ax[1, 1].set_xlabel("Battery capacity [kWh]")

ax[0, 0].set_ylabel("Num. events")
ax[1, 0].set_ylabel("LCOE [$/kWh]")

ax[0, 1].set_ylabel("Total duration [hr]")
ax[1, 1].set_ylabel("Total energy [MWh]")

for i in range(ax.shape[0]):
    for j in range(ax.shape[1]):
        ax[i, j].spines[["top", "right"]].set_visible(False)

fig.align_labels()

fig.savefig(Path(__file__).parent / "plots" / "sweep_results.pdf", format="pdf")


fig, ax = plt.subplots(
    len(results), 3, sharex="all", sharey="col", layout="constrained"
)
ax = np.atleast_2d(ax)


full_re_gen = []


annual_stats = {}


cmap = plt.colormaps["plasma"]


for i, k in enumerate(sorted(results.keys())):
    res = results[k]["ts_0"]
    re_gen = res.df["solar_kw"] + res.df["wind_kw"]

    full_re_gen.append(re_gen)

    annual_stats[k] = dict(AEP=np.sum(re_gen), mean=np.mean(re_gen), std=np.std(re_gen))

    print(
        f"year: {k}, AEP: {np.sum(re_gen)/1e6:.2f}, mean: {np.mean(re_gen):.2f}, std: {np.std(re_gen):.2f}"
    )

    ax[i, 0].plot(re_gen)

    ax[i, 0].set_ylabel(k)

    for j in range(n_cases):

        shortfall_j = results[k][f"ts_{j}"].df["shortfall_kw"]
        ax[i, 1].plot(shortfall_j, color=cmap(j / 10))

        soc_j = results[k][f"ts_{j}"].df["battery_soc"]
        ax[i, 2].plot(soc_j, color=cmap(j / 10))

    # ax[i, 1].plot(res.df["headroom_kw"])

ax[0, 0].set_title("Generation")
ax[0, 1].set_title("Shortfall")
ax[0, 2].set_title("Battery SOC")


fig, ax = plt.subplots(1, 3, sharex="all", layout="constrained", figsize=(8, 2))
ax = np.atleast_2d(ax)

res_keys = sorted(results.keys())
AEP = [annual_stats[k]["AEP"] for k in res_keys]
mean = [annual_stats[k]["mean"] for k in res_keys]
std = [annual_stats[k]["std"] for k in res_keys]


def calc_ylim(data):
    ymin = min(data)
    ymax = max(data)

    data_range = ymax - ymin

    return [ymin - 0.1 * data_range, ymax + 0.1 * data_range]


ax[0, 0].bar(res_keys, AEP, zorder=3)
ax[0, 1].bar(res_keys, mean, zorder=3)
ax[0, 2].bar(res_keys, std, zorder=3)


ax[0, 0].set_ylim(calc_ylim(AEP))
ax[0, 1].set_ylim(calc_ylim(mean))
ax[0, 2].set_ylim(calc_ylim(std))


for i in range(ax.shape[0]):
    for j in range(ax.shape[1]):
        ax[i, j].grid(axis="y", zorder=0)
        ax[i, j].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
        ax[i, j].set_xticks(res_keys, res_keys, rotation=45)
        ax[i, j].spines[["top", "right"]].set_visible(False)


ax[0, 0].set_title("AEP [kWh]")
ax[0, 1].set_title("Hourly Mean [kWh]")
ax[0, 2].set_title("Std. Dev. [kWh]")

fig.savefig(Path(__file__).parent / "plots" / "annual_stats.pdf", format="pdf")


full_re_gen = np.concatenate(full_re_gen)


if True:

    def MA_filter(data, width):
        ma_data = np.convolve(data, np.ones(width) / width, mode="same")
        return ma_data

    p = full_re_gen
    t = np.arange(len(full_re_gen))

    # wavelet = "cmor1.5-1.0"
    # wavelet = "mexh"
    wavelet = "gaus1"
    # widths = np.geomspace(1, 1024, num=100)
    # widths = np.geomspace(1, 4096, num=100)
    widths = np.geomspace(1, 24 * 30, num=50)  # 1 hour to 24 hours
    # sampling_period = np.diff(t).mean()
    sampling_period = 3600
    # cwtmatr, freqs = pywt.cwt(p, widths, wavelet, sampling_period=sampling_period)
    cwtmatr, freqs = pywt.cwt(
        np.concatenate([np.flip(p), p, np.flip(p)]),
        widths,
        wavelet,
        sampling_period=sampling_period,
    )

    cwtmatr = cwtmatr[:, len(p) : 2 * len(p)]
    cwtmatr = np.abs(cwtmatr[:-1, :-1])

    # plot result using matplotlib's pcolormesh (image with annoted axes)
    fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")

    ax[1].plot(t, p)
    ax[1].plot(t, MA_filter(p, 1 * 24))
    ax[1].plot(t, MA_filter(p, 7 * 24))

    pcm = ax[0].pcolormesh(t, freqs, cwtmatr)
    ax[0].set_yscale("log")
    ax[0].set_xlabel("Time (s)")
    ax[0].set_ylabel("Frequency (Hz)")
    ax[0].set_title("Continuous Wavelet Transform (Scaleogram)")
    fig.colorbar(pcm, ax=ax[0])

    ax[1].set_xticks(np.arange(0, len(t), 8760))

    ax[0].axhline(1 / (24 * 3600), color="orange")
    ax[0].axhline(1 / (7 * 24 * 3600), color="orange")


[]
