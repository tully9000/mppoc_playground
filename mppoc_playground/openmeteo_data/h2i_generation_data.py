from io import StringIO
import json
from pathlib import Path
from pprint import pprint
import sys
import yaml
from copy import deepcopy
import matplotlib.pyplot as plt
import numpy as np

from h2integrate import (
    H2IntegrateModel,
    load_tech_yaml,
    load_plant_yaml,
    load_driver_yaml,
)


import os

# Directory of this script and the default case file path (unused variable kept for context)
run_dir = os.path.dirname(__file__)
case_to_run = os.path.join(run_dir, "case.yaml")


# Load config files into dict
# The repository contains a folder `h2i_configs` with YAML configuration files.
config_root = Path(__file__).parent / "h2i_configs"
config_path = config_root / "case.yaml"

# Load top level config
with Path(config_path).open() as f:
    config = yaml.safe_load(f)

# Populate nested configuration entries by loading referenced YAML files
# These helper functions are provided by the `h2integrate` package.
config["driver_config"] = load_driver_yaml(config_root / config["driver_config"])
config["technology_config"] = load_tech_yaml(config_root / config["technology_config"])
config["plant_config"] = load_plant_yaml(config_root / config["plant_config"])


# Prepare lists to collect per-year generation arrays
wind_list = []
solar_list = []


# Loop over historical years and run the H2Integrate model for each year
# Each iteration sets the resource year in the plant config so the model
# reads different wind/solar inputs for that year.
for i, yr in enumerate(np.arange(1995, 2025, 1)):

    # Copy config so each year's changes do not persist to the next iteration
    config_yr = deepcopy(config)

    # Set the resource year for both wind and solar sites
    config_yr['plant_config']['sites']['site']['resources']['wind_resource']['resource_parameters']['resource_year'] = yr
    config_yr['plant_config']['sites']['site']['resources']['solar_resource']['resource_parameters']['resource_year'] = yr

    # Instantiate and run the H2Integrate model for this configuration
    h2i = H2IntegrateModel(config_yr)
    h2i.run()

    # Extract time-series outputs produced by the model
    wind = h2i.prob.get_val("wind.electricity_out")
    solar = h2i.prob.get_val("solar.electricity_out")

    # Accumulate the per-year arrays
    wind_list.append(wind)
    solar_list.append(solar)

# Concatenate yearly arrays into a single long timeseries for each resource
wind_gen = np.concatenate(wind_list)
solar_gen = np.concatenate(solar_list)
hybrid_gen = wind_gen + solar_gen

# Save the generated arrays for later use by other analysis scripts
np.savez(Path(__file__).parent / "hybrid_gen_data", wind=wind_gen, solar=solar_gen, hybrid=hybrid_gen)

