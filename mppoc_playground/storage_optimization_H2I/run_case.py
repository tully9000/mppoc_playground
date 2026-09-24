from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt


import openmdao.api as om

from openmdao.visualization.opt_report import opt_report

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

    model.run()

    return model





def plot_system_graph(h2i):
    import networkx as nx
    nx.draw(h2i.technology_graph, with_labels=True)


if __name__ == "__main__":
    config_root = Path(__file__).parent / "base_configs"

    h2i = run_case(config_path=config_root / "config.yaml")
    opt_report.opt_report(h2i.prob)

    inputs = dict(h2i.model.list_inputs(print_arrays=False, out_stream=None))
    outputs = dict(h2i.model.list_outputs(print_arrays=False, out_stream=None))
    lcoe = h2i.prob.get_val('plant.finance_subgroup_electricity.electricity_finance_profast_lco.LCOE')


    fig, ax = plt.subplots(4, 1, sharex="all", layout="constrained")
    ax[0].plot(h2i.prob.get_val("plant.electrical_load_demand.GenericDemandComponent.electricity_out"))
    ax[0].plot(h2i.prob.get_val("plant.electrical_load_demand.GenericDemandComponent.unmet_electricity_demand_out"))









    driver_cr = om.CaseReader(
        "/Users/ztully/Documents/software/MPPOC/mppoc_playground/run_single_case_out/driver_report.sql"
    )
    driver_cases = driver_cr.list_cases("driver", recurse=False)

    solver_cr = om.CaseReader(
        "/Users/ztully/Documents/software/MPPOC/mppoc_playground/run_single_case_out/solver_report.sql"
    )
    solver_cases = solver_cr.list_cases()

