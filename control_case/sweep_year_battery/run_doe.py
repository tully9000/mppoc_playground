from io import StringIO
import json
from pathlib import Path
from pprint import pprint
import sys
from copy import copy, deepcopy
import yaml

from multiprocessing import Pool

import openmdao.api as om

from h2integrate.core.h2integrate_model import H2IntegrateModel
from h2integrate.core.supported_models import supported_models
from h2integrate.core.dict_utils import update_defaults
from h2integrate.core.file_utils import load_yaml, check_file_format_for_csv_generator
from h2integrate.postprocess.sql_to_csv import convert_sql_to_csv_summary

from mppoc_datacenter_measures.loaders.h2i import H2ITopology, load_h2i_case

import os

# Register the custom system-level controller. H2Integrate's SLC framework
# only looks up `control_strategy` in `supported_models` (there is no
# `model_location` scan for the SLC block), so we inject the class into the
# module-level registry before instantiating `H2IntegrateModel`. The shared
# UCControl lives in the repo-root `uc_control` package (see its docstring for
# why a custom UC-based SLC is needed).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from uc_control import UCControl  # noqa: E402

supported_models["UCControl"] = UCControl

# from dispatchable_first_control import DispatchableFirstControl  # noqa: E402
from uc_control import DispatchableFirstControl

supported_models["DispatchableFirstControl"] = DispatchableFirstControl


def run_year_case(year):
    config_path = os.path.join(
        os.path.dirname(__file__), "configs", f"year_{year}", "config.yaml"
    )

    model = H2IntegrateModel(config_path)
    model.prob.driver.add_recorder(om.SqliteRecorder("doe_driver.sql"))
    model.run()


if __name__ == "__main__":
    # freeze_support()

    run_dir = os.path.dirname(__file__)
    case_to_run = os.path.join(run_dir, "case.yaml")

    # delete previous run

    # For wind toolkit
    # valid_years = [2007, 2008, 2009, 2010, 2011, 2012, 2013]
    valid_years = [
        2007,
        # 2008,
        # 2009,
        2010,
        # 2011,
        # 2012,
        2013,
    ]

    # Load the configurations and run the model
    config = load_yaml(case_to_run)

    driver_config = load_yaml(os.path.join(run_dir, config["driver_config"]))
    tech_config = load_yaml(os.path.join(run_dir, config["technology_config"]))
    plant_config = load_yaml(os.path.join(run_dir, config["plant_config"]))

    case_configs = []

    for year in valid_years:
        # Make new folder
        year_folder = os.path.join(os.path.dirname(__file__), f"configs/year_{year}")
        os.makedirs(year_folder, exist_ok=True)

        # Copy configs
        config_copy = deepcopy(config)
        driver_config_copy = deepcopy(driver_config)
        tech_config_copy = deepcopy(tech_config)
        plant_config_copy = deepcopy(plant_config)

        # Modify where relevant
        config_copy["name"] = f"{config_copy['name']}"
        config_copy["driver_config"] = (
            f"configs/year_{year}/{config_copy['driver_config']}"
        )
        config_copy["technology_config"] = (
            f"configs/year_{year}/{config_copy['technology_config']}"
        )
        config_copy["plant_config"] = (
            f"configs/year_{year}/{config_copy['plant_config']}"
        )

        plant_config_copy["sites"]["site"]["resources"]["wind_resource"][
            "resource_parameters"
        ]["resource_year"] = year
        plant_config_copy["sites"]["site"]["resources"]["solar_resource"][
            "resource_parameters"
        ]["resource_year"] = year

        driver_config_copy["general"]["folder_output"] = os.path.join(
            os.path.dirname(__file__), f"outputs/DOE_{year}"
        )

        # plant_config_copy["system_level_control"]["control_parameters"]["uc_horizon"] = 3

        # plant_config_copy["system_level_control"] = {
        #     "control_strategy": "DemandFollowingControl",
        #     "demand_component": "electrical_load_demand",
        #     "solver_options": {
        #         "solver_name": "gauss_seidel",
        #         "max_iter": 20,
        #         "convergence_tolerance": 1.0e-6,
        #     },
        # }

        # Save in new folder in configs

        case_configs.append(os.path.join(year_folder, f"config_{year}.yaml"))

        with open(os.path.join(year_folder, f"config.yaml"), "w") as file:
            yaml.dump(config_copy, file, default_flow_style=False, sort_keys=False)

        with open(os.path.join(year_folder, f"driver_config.yaml"), "w") as file:
            yaml.dump(
                driver_config_copy, file, default_flow_style=False, sort_keys=False
            )

        with open(os.path.join(year_folder, f"tech_config.yaml"), "w") as file:
            yaml.dump(tech_config_copy, file, default_flow_style=False, sort_keys=False)

        with open(os.path.join(year_folder, f"plant_config.yaml"), "w") as file:
            yaml.dump(
                plant_config_copy, file, default_flow_style=False, sort_keys=False
            )

    for year in valid_years:
        run_year_case(year)

    # with Pool(8) as p:
    #     print(p.map(run_year_case, valid_years))

    # with ProcessPoolExecutor() as executor:
    #     results = list(executor.map(run_year_case, valid_years ))

    # for case_root in os.listdir(os.path.join(os.path.dirname(__file__), "configs")):
    #     year = case_root.split("_")[1]
    #     run_year_case(year)
    # config_path = os.path.join(
    #     os.path.dirname(__file__), "configs", case_root, "config.yaml"
    # )

    # model = H2IntegrateModel(config_path)
    # model.prob.driver.add_recorder(om.SqliteRecorder("doe_driver.sql"))
    # model.run()

    # cr = om.CaseReader("/Users/ztully/Documents/software/MPPOC/mppoc-datacenter-h2i/control_case/sweep_year_battery/outputs/DOE_2007/cases.sql")
    # sources = cr.list_sources()
    # cases = cr.get_cases("driver")

    # ts = load_h2i_case("/Users/ztully/Documents/software/MPPOC/mppoc-datacenter-h2i/control_case/sweep_year_battery/outputs/DOE_2007/cases.sql", case_index=0, )
    # model.post_process()

    []


# model = H2IntegrateModel(config)
# model.run()
# model.post_process()

[]


# ====================================================

# from io import StringIO
# import json
# from pathlib import Path
# from pprint import pprint
# import sys

# from h2integrate.core.h2integrate_model import H2IntegrateModel
# from h2integrate.core.supported_models import supported_models
# from h2integrate.core.dict_utils import update_defaults
# from h2integrate.core.file_utils import load_yaml, check_file_format_for_csv_generator

# import os
# run_dir = os.path.dirname(__file__)
# case_to_run = os.path.join(run_dir, "case.yaml")

# # Register the custom system-level controller. H2Integrate's SLC framework
# # only looks up `control_strategy` in `supported_models` (there is no
# # `model_location` scan for the SLC block), so we inject the class into the
# # module-level registry before instantiating `H2IntegrateModel`. The shared
# # UCControl lives in the repo-root `uc_control` package (see its docstring for
# # why a custom UC-based SLC is needed).
# sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
# from uc_control import UCControl  # noqa: E402

# supported_models["UCControl"] = UCControl


# ##################################
# # Create an H2I model with a fixed electricity load demand
# h2i = H2IntegrateModel(case_to_run)

# # Run the model
# h2i.run()

# if True:
#     old_stdout = sys.stdout
#     sys.stdout = StringIO()
#     try:
#         prdict = h2i.print_results(h2i.prob.model, excludes=["*resource_data"])
#         with open(Path.cwd().parent / f"{Path(__file__).parent.name}.json", "w") as f:
#             json.dump(prdict, f, indent=2, default=str)
#         captured_output = sys.stdout.getvalue()
#     finally:
#         sys.stdout = old_stdout

#     print(captured_output)
#     filename_output = Path.cwd().parent / f"{Path(__file__).parent.name}.txt"
#     with open(filename_output, "w") as f:
#         f.write(captured_output)

# print("\n\n\n\n")

# print("LCOE Electricity: ", h2i.prob.get_val("finance_subgroup_electricity.LCOE")[0])
# print("NPV Electricity: ", h2i.prob.get_val("finance_subgroup_natural_gas.NPV_electricity__profast_npv")[0]+h2i.prob.get_val("finance_subgroup_renewable_generation.NPV_electricity__profast_npv")[0])
