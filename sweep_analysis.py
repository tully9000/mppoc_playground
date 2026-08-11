import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from pathlib import Path

from mppoc_datacenter_measures.loaders.h2i import H2ITopology, load_h2i_case
from mppoc_datacenter_measures.metrics.events import detect_events

sweeps_root = Path(__file__).parents[1] / "mppoc-datacenter-h2i/control_case/runs"
# sweep_root = sweeps_root / "sweep_20260727_173759"
sweep_root = sweeps_root / "sweep_20260728_141735"


# Find cases.sql file for each case in the sweep
sweep_dirs = []
sweep_files = []
for path in sweep_root.iterdir():
    if path.is_dir():
        sweep_dirs.append(path)
    elif path.is_file():
        sweep_files.append(path)


sweep_dirs.sort()
sweep_files.sort()


def parse_case_name(name: str):
    parts = name.split("_")

    return dict(
        horizon=int(parts[0].lstrip("h")),
        soc_target=int(parts[2]),
        battery_capacity=float(parts[3]),
    )


sweep_cases = dict()
for sd in sweep_dirs:
    ts = load_h2i_case(str(sd / "cases.sql"), topology=H2ITopology.slc())
    case_name = sd.parts[-1]

    case_params = parse_case_name(case_name)
    sweep_cases.update({case_name: {"ts": ts}})  # , "params": case_params}})

    sweep_cases[case_name].update({"events": detect_events(ts)})
    sweep_cases[case_name].update(case_params)

    []


class Results:
    def __init__(self, sweep_cases: dict):
        self.sweep_cases = sweep_cases

    def sort_by(self, param_list: list = []):

        unique_params = dict()
        for param in param_list:

            unique_list = []

            for k, v in self.sweep_cases.items():
                unique_list.append(v[param])

            unique_list = list(set(unique_list))
            unique_list.sort()

            unique_params.update({param: unique_list})

        sorted_dict = dict()

        sorted_params = self.recursive_params(unique_params, sorted_dict)

        sorted_cases = self.recursive_sort(sorted_params, self.sweep_cases)

        return sorted_cases, unique_params

    def recursive_sort(self, rec_params, sweep_dict, level=0):

        key = list(rec_params.keys())[0]
        return_dict = {key: {}}

        for k, v in rec_params[key].items():

            k_dict = {}

            for ks, vs in sweep_dict.items():
                if vs[key] == k:
                    k_dict.update({ks: vs})

            if rec_params[key][k]:
                deeper_dict = self.recursive_sort(
                    rec_params[key][k], k_dict, level=level + 1
                )
            else:
                deeper_dict = k_dict

            return_dict[key].update({k: deeper_dict})

        return return_dict

    def recursive_params(self, params, sorted_dict, level=0):

        if level == len(params) - 1:

            key = list(params.keys())[level]
            vals = params[key]

            deeper_dict = {key: {val: {} for val in params[key]}}

            return deeper_dict

        deeper_dict = self.recursive_params(params, sorted_dict, level=level + 1)

        #     self.recursive_sort(params, sorted_dict, level=level+1)

        key = list(params.keys())[level]

        sorted_dict = {key: {val: deeper_dict for val in params[key]}}
        # sorted_dict.update({key: { val:deeper_dict for val in params[key]}})

        return sorted_dict


def compare_xy(x_var, y_vars, sorted_cases):
    pass


res = Results(sweep_cases)

sorted_cases, unique_params = res.sort_by(param_list=["horizon", "soc_target", "battery_capacity"])


fig, ax = plt.subplots(1, 1, layout="constrained")

for k, sc in sweep_cases.items():
    ax.plot(sc["ts"].df["shortfall_kw"], label=k)


ax.legend()


fig, ax = plt.subplots(4, 1, sharex="all", layout="constrained", figsize=(8,4))
ax = np.atleast_2d(ax).T


ax[0, 0].set_ylabel("Event\ncount")
ax[1, 0].set_ylabel("Total\nduration")
ax[2, 0].set_ylabel("Max\ndepth")
ax[3, 0].set_ylabel("Total\nenergy")

ax[-1, 0].set_xlabel("Battery capacity")


marker_dict = {24: "o", 48:"^"}
color_dict = {30: "blue", 50: "orange", 80: "green"}



for horizon, hor_dict in sorted_cases["horizon"].items():

    marker = marker_dict[horizon]

    for soc_target, soc_dict in hor_dict["soc_target"].items():
        color=color_dict[soc_target]

        for cap, cap_dict in soc_dict["battery_capacity"].items():

            for k, v in cap_dict.items():
                ax[0, 0].scatter(cap, len(v["events"]), marker=marker, color=color)
                ax[1, 0].scatter(cap, v["events"]["duration_hours"].sum(), marker=marker, color=color)
                ax[2, 0].scatter(cap, v["events"]["max_depth_kw"].max(), marker=marker, color=color)
                ax[3, 0].scatter(cap, v["events"]["energy_mwh"].sum(), marker=marker, color=color)


for i in range(ax.shape[0]):
    for j in range(ax.shape[1]):
        ax[i, j].spines[["top", "right"]].set_visible(False)
        ax[i, j].grid(axis="y")

leg1_handles = [
    Line2D([0], [0], marker=marker_dict[24], linewidth=0, color=color_dict[30]),
    Line2D([0], [0], marker=marker_dict[48], linewidth=0, color=color_dict[30]),
]
leg1_labels = [
    "Horizon 24",
    "Horizon 48",
]
leg1 = ax[0, 0].legend(handles=leg1_handles, labels=leg1_labels)


leg2_handles = [
    Line2D([0], [0], marker=marker_dict[24], linewidth=0, color=color_dict[30]),
    Line2D([0], [0], marker=marker_dict[24], linewidth=0, color=color_dict[50]),
    Line2D([0], [0], marker=marker_dict[24], linewidth=0, color=color_dict[80]),
]
leg2_labels = [
    "SOC Target 30",
    "SOC Target 50",
    "SOC Target 80",
]
leg2 = ax[3, 0].legend(handles=leg2_handles, labels=leg2_labels, loc="center", bbox_to_anchor=(0.75, 0.6))

fig.align_labels()

fig.savefig("/Users/ztully/Documents/software/MPPOC/mppoc_playground/plots/sweep_results.pdf", format="pdf")

[]
