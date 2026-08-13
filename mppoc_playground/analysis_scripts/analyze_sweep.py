import numpy as np
import matplotlib.pyplot as plt
import yaml


from pathlib import Path

import openmdao.api as om

from mppoc_datacenter_measures.loaders.h2i import H2ITopology, load_h2i_case
from mppoc_datacenter_measures.metrics.events import (
    detect_events,
    voll_weighted_severity,
)
from mppoc_datacenter_measures.metrics.adequacy import lolp, lolh, lole, lolf, eue, neue

data_root = Path(__file__).parents[1] / "run_data"

runs = sorted(list(data_root.iterdir()))


case_root = runs[-1]
# case_root = data_root / "run_20260812_184632"

case_fname = case_root / "output" / "cases.sql"

# Check configs

config_root = case_root / "config"
with open(config_root / "config.yaml", "r") as f:
    top_config = yaml.safe_load(f)

with open(top_config["driver_config"], "r") as f:
    driver_config = yaml.safe_load(f)

parameter_sweep = "parameter_sweep" in driver_config["driver"]
parameters = [
    f"{k}.{list(v.keys())[0]}" for k, v in driver_config["design_variables"].items()
]
n_levels = driver_config["driver"]["parameter_sweep"]["levels"]


cr = om.CaseReader(case_fname)
cases = cr.get_cases()

timeseries = []
events = []
measures = []

for i in range(len(cases)):
    # ts = load_h2i_case(case_fname, case_index=i, topology=H2ITopology.slc())
    ts = load_h2i_case(cases, case_index=i, topology=H2ITopology.slc(), scenario_name="temp")
    timeseries.append(ts)
    events.append(detect_events(ts))
    measures.append(
        dict(
            lolp=lolp(ts),
            lolh=lolh(ts),
            lole=lole(ts),
            lolf=lolf(ts),
            eue=eue(ts),
            neue=neue(ts),
        )
    )


assert len(cases) == n_levels ** len(parameters)

param_vals = np.array([[case.get_val(param) for case in cases] for param in parameters])


fig, ax = plt.subplots(
    2, 2, sharex="all", sharey="all", layout="constrained", figsize=(6, 5)
)


def plot_surface(ax, x, y, z, metric=""):

    X, Y = np.meshgrid(x, y)
    Z = np.reshape(z, (len(x), len(y)))

    CSF = ax.contourf(X, Y, Z)
    CS = ax.contour(X, Y, Z)
    ax.clabel(CS, fontsize=10, colors="black")

    ax.set_title(metric)


plot_surface(
    ax[0, 0],
    np.unique(param_vals[0, :]),
    np.unique(param_vals[1, :]),
    np.array([len(ev) for ev in events]),
    "Num. events",
)
plot_surface(
    ax[0, 1],
    np.unique(param_vals[0, :]),
    np.unique(param_vals[1, :]),
    np.array([ms["neue"] for ms in measures]),
    "NEUE",
)
plot_surface(
    ax[1, 0],
    np.unique(param_vals[0, :]),
    np.unique(param_vals[1, :]),
    np.array(
        [
            cs.get_val(
                "plant.finance_subgroup_electricity.electricity_finance_profast_lco.LCOE"
            )
            for cs in cases
        ]
    ),
    "LCOE",
)


ax[0, 0].set_xticks(np.unique(param_vals[0, :]))
ax[0, 0].set_yticks(np.unique(param_vals[1, :]))


for i in range(ax.shape[0]):
    ax[i, 0].set_ylabel(parameters[1])

for j in range(ax.shape[1]):
    ax[-1, j].set_xlabel(parameters[0])


fig.savefig(
    Path(__file__).parents[1] / "plots" / "sensitivity_surface.pdf", format="pdf"
)


[]
