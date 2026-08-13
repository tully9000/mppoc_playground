from pathlib import Path
import sys
import yaml
import pandas as pd

from mppoc_datacenter_measures.loaders.h2i import H2ITopology, load_h2i_case
from mppoc_datacenter_measures.metrics.events import (
    detect_events,
    voll_weighted_severity,
)
from mppoc_datacenter_measures.metrics.adequacy import lolp, lolh, lole, lolf, eue, neue

if __name__ == "__main__":

    # ── Register custom UC controller (shared uc_control package) ────────
    repo_root = Path(__file__).resolve().parents[3] / "mppoc-datacenter-h2i"
    sys.path.insert(0, str(repo_root))
    from h2integrate.core.h2integrate_model import H2IntegrateModel
    from h2integrate.core.supported_models import supported_models

    from uc_control import UCControl  # noqa: E402

    supported_models["UCControl"] = UCControl

    config = Path(__file__).parent / "case.yaml"

    with open(config) as f:
        config_dict = yaml.safe_load(f)

    driver_config_path = config_dict["driver_config"]
    with open(driver_config_path) as f:
        driver_config_dict = yaml.safe_load(f)

    output_dir = driver_config_dict["general"]["folder_output"]

    h2i = H2IntegrateModel(config)
    h2i.run()

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(
        2, 1, sharex="all", sharey="all", layout="constrained", figsize=(8, 4)
    )

    soc_batt = (
        h2i.prob.get_val("battery.SOC")
        / 100
        * h2i.prob.get_val("battery.storage_capacity")
    )
    soc_slc = h2i.plant.system_level_controller.soc_store

    ax[0].plot(soc_slc, label="UC Control")
    ax[0].plot(soc_batt, label="Batt.")

    ax[0].set_ylabel("Charge state [kWh]")

    ax[1].plot(soc_batt - soc_slc, label="difference")
    ax[1].set_ylabel("Difference [kWh]")

    ax[1].set_xlabel("Time [h]")

    ax[0].legend()

    ax[1].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

    fig.align_labels()

    for i in range(ax.shape[0]):
        ax[i].axhline(0, color="black", linewidth=0.5)
        ax[i].spines[["top", "right"]].set_visible(False)

    fig.savefig(
        Path(__file__).parents[1] / "plots" / "SLC_SOC_discrepancy.pdf", format="pdf"
    )

    ts = load_h2i_case(Path(output_dir) / "cases.sql", topology=H2ITopology.slc())

    events = detect_events(ts)
    measures = (
        dict(
            lolp=lolp(ts),
            lolh=lolh(ts),
            lole=lole(ts),
            lolf=lolf(ts),
            eue=eue(ts),
            neue=neue(ts),
        ),
    )

    # fig, ax = plt.subplots(1, 1, layout="constrained")


    start_of_year = events['start'].dt.to_period('Y').dt.to_timestamp()

    events_hour = (events["start"] - start_of_year) / pd.Timedelta(hours=1)


    ax[0].scatter(events_hour, events["n_steps"])

[]
