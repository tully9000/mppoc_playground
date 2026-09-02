from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt


import openmdao.api as om

from h2integrate.core.h2integrate_model import H2IntegrateModel
from h2integrate.core.supported_models import supported_models
from mppoc_datacenter_measures.loaders.h2i import H2ITopology, load_h2i_case
from mppoc_datacenter_measures.metrics.adequacy import lolp, lolh, lole, lolf, eue, neue
import pandas as pd

repo_root = Path(__file__).resolve().parents[3] / "mppoc-datacenter-h2i"
sys.path.insert(0, str(repo_root))

from uc_control import UCControl  # noqa: E402
from uc_control import DispatchableFirstControl

supported_models["UCControl"] = UCControl
supported_models["DispatchableFirstControl"] = DispatchableFirstControl


def run_case(config_path):

    model = H2IntegrateModel(config_path)

    driver_recorder = om.SqliteRecorder("driver_report.sql")
    model.prob.driver.add_recorder(driver_recorder)

    # model.prob.model.nonlinear_solver = om.NonlinearBlockGS()
    # solver = model.prob.model.nonlinear_solver
    # model.prob.model.plant.nonlinear_solver = om.NonlinearBlockJac()
    # model.prob.model.plant.nonlinear_solver = om.NewtonSolver()
    solver = model.prob.model.plant.nonlinear_solver

    solver.options["maxiter"] = 250

    solver_recorder = om.SqliteRecorder("solver_report.sql")
    solver.add_recorder(solver_recorder)
    # solver.options["desc"] = True
    solver.recording_options["record_inputs"] = True
    solver.recording_options["record_outputs"] = True
    solver.recording_options["record_solver_residuals"] = True

    # Try finding the plant group solver

    model.run()

    return model


def plot_battery_agreement(h2i):
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

    # fig.savefig(
    #     Path(__file__).parents[1] / "plots" / "SLC_SOC_discrepancy.pdf", format="pdf"
    # )

    # ts = load_h2i_case(Path(output_dir) / "cases.sql", topology=H2ITopology.slc())

    # events = detect_events(ts)
    # measures = (
    #     dict(
    #         lolp=lolp(ts),
    #         lolh=lolh(ts),
    #         lole=lole(ts),
    #         lolf=lolf(ts),
    #         eue=eue(ts),
    #         neue=neue(ts),
    #     ),
    # )

    # # fig, ax = plt.subplots(1, 1, layout="constrained")

    # start_of_year = events['start'].dt.to_period('Y').dt.to_timestamp()

    # events_hour = (events["start"] - start_of_year) / pd.Timedelta(hours=1)

    # ax[0].scatter(events_hour, events["n_steps"])


def plot_system_graph(h2i):
    import networkx as nx
    nx.draw(h2i.technology_graph, with_labels=True)


if __name__ == "__main__":
    config_root = Path(__file__).parent / "base_configs"

    h2i = run_case(config_path=config_root / "config.yaml")
    # plot_battery_agreement(h2i)

    driver_cr = om.CaseReader(
        "/Users/ztully/Documents/software/MPPOC/mppoc_playground/run_single_case_out/driver_report.sql"
    )
    driver_cases = driver_cr.list_cases("driver", recurse=False)

    solver_cr = om.CaseReader(
        "/Users/ztully/Documents/software/MPPOC/mppoc_playground/run_single_case_out/solver_report.sql"
    )
    solver_cases = solver_cr.list_cases()
    # solver_cases = solver_cr.list_cases("root.nonlinear_solver")

    
    # [k for k,v in solver_cr.get_case(solver_cases[2]).residuals.items() if np.mean(v) > 0.1]




    # fig, ax = plt.subplots(len(solver_cases), 1, sharey="all", sharex="all", layout="constrained")

    # for i, case_id in enumerate(solver_cases):

    #     bes_soc= solver_cr.get_case(case_id).outputs["battery.SOC"] / 100
    #     slc_soc = solver_cr.get_case(case_id).inputs["plant.system_level_controller.battery_SOC"]

    #     ax[i].plot(bes_soc)
    #     ax[i].plot(slc_soc)

    # print(solver_cr.get_case(case_id).abs_err)

    # battery_setpoint_res = solver_cr.get_case(case_id).residuals["system_level_controller.battery_electricity_set_point"]

    # ax.plot(battery_setpoint_res)

    battery_outputs = {
        k: v
        for k, v in solver_cr.get_case(solver_cases[-1]).outputs.items()
        if "battery" in k
    }
    battery_inputs = {
        k: v
        for k, v in solver_cr.get_case(solver_cases[-1]).inputs.items()
        if "battery" in k
    }

    slc_outputs = {
        k: v
        for k, v in solver_cr.get_case(solver_cases[-1]).outputs.items()
        if "system_level_controller" in k
    }
    slc_inputs = {
        k: v
        for k, v in solver_cr.get_case(solver_cases[-1]).inputs.items()
        if "system_level_controll" in k
    }

    fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")

    ax[0].plot(battery_outputs["battery.SOC"] / 100)
    ax[0].plot(slc_inputs["plant.system_level_controller.battery_SOC"])

    """
    Possible inputs

    - plant.system_level_controller.battery_SOC

    Possible outputs

    - battery.SOC
    
    """

    # solver_cr.get_case(solver_cases[0]).inputs['plant.system_level_controller.battery_electricity_out'] - solver_cr.get_case(solver_cases[0]).inputs["plant.battery.StoragePerformanceModel.electricity_in"]

    # solver_cr.get_case(solver_cases[0]).residuals

    pass
