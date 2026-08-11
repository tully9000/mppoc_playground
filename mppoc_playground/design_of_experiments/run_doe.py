# """Minimal working example from the parameter sweep user guide docs."""

# from h2integrate import H2IntegrateModel
# from h2integrate.core.dict_utils import update_defaults
# from h2integrate.core.file_utils import load_yaml, check_file_format_for_csv_generator


# # Load the configurations and run the model
# config = load_yaml("config.yaml")
# driver_config = load_yaml(config["driver_config"])
# csv_config_fn = driver_config["driver"]["parameter_sweep"]["filename"]

# try:
#     model = H2IntegrateModel(config)
#     model.run()
# except UserWarning as e:
#     print(f"Caught UserWarning: {e}")

# """
# To fix the issue with the UserWarning, we'll take the following steps to try and fix
# the bug in our CSV file:
# 1. Run the `check_file_format_for_csv_generator` method mentioned in the UserWarning
#   and create a new csv file that is hopefully free of errors
# 2. Make a new driver config file that has "filename" point to the new csv file created
#   in Step 1.
# 3. Make a new top-level config file that points to the updated driver config file
#   created in Step 2.
# """

# # Step 1
# new_csv_filename = check_file_format_for_csv_generator(
#     csv_config_fn,
#     driver_config,
#     check_only=False,
#     overwrite_file=False,
# )

# # Step 2
# updated_driver = update_defaults(
#     driver_config["driver"],
#     "filename",
#     new_csv_filename.name,
# )
# driver_config["driver"].update(updated_driver)
# print(f"New parameter sweep driver CSV file: {new_csv_filename}")

# # Step 3
# config["driver_config"] = driver_config

# # Rerun the model
# model = H2IntegrateModel(config)
# model.run()



# ====================================================

from io import StringIO
import json
from pathlib import Path
from pprint import pprint
import sys

from h2integrate.core.h2integrate_model import H2IntegrateModel
from h2integrate.core.supported_models import supported_models

import os
run_dir = os.path.dirname(__file__)
case_to_run = os.path.join(run_dir, "case.yaml")

# Register the custom system-level controller. H2Integrate's SLC framework
# only looks up `control_strategy` in `supported_models` (there is no
# `model_location` scan for the SLC block), so we inject the class into the
# module-level registry before instantiating `H2IntegrateModel`. The shared
# UCControl lives in the repo-root `uc_control` package (see its docstring for
# why a custom UC-based SLC is needed).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from uc_control import UCControl  # noqa: E402

supported_models["UCControl"] = UCControl


##################################
# Create an H2I model with a fixed electricity load demand
h2i = H2IntegrateModel(case_to_run)

# Run the model
h2i.run()

if True:
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        prdict = h2i.print_results(h2i.prob.model, excludes=["*resource_data"])
        with open(Path.cwd().parent / f"{Path(__file__).parent.name}.json", "w") as f:
            json.dump(prdict, f, indent=2, default=str)
        captured_output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    print(captured_output)
    filename_output = Path.cwd().parent / f"{Path(__file__).parent.name}.txt"
    with open(filename_output, "w") as f:
        f.write(captured_output)

print("\n\n\n\n")

print("LCOE Electricity: ", h2i.prob.get_val("finance_subgroup_electricity.LCOE")[0])
print("NPV Electricity: ", h2i.prob.get_val("finance_subgroup_natural_gas.NPV_electricity__profast_npv")[0]+h2i.prob.get_val("finance_subgroup_renewable_generation.NPV_electricity__profast_npv")[0])
