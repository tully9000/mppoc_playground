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

run_dir = os.path.dirname(__file__)
case_to_run = os.path.join(run_dir, "case.yaml")



# Load config files into dict
config_root = Path(__file__).parent / "h2i_configs"
config_path = config_root / "case.yaml"

# Load top level config
with Path(config_path).open() as f:
    config = yaml.safe_load(f)

config["driver_config"] = load_driver_yaml(config_root / config["driver_config"])
config["technology_config"] = load_tech_yaml(config_root / config["technology_config"])
config["plant_config"] = load_plant_yaml(config_root / config["plant_config"])


wind_list = []
solar_list = []


for i, yr in enumerate(np.arange(1995, 2025, 1)):

    config_yr = deepcopy(config)

    config_yr['plant_config']['sites']['site']['resources']['wind_resource']['resource_parameters']['resource_year'] = yr
    config_yr['plant_config']['sites']['site']['resources']['solar_resource']['resource_parameters']['resource_year'] = yr


    h2i = H2IntegrateModel(config_yr)

    h2i.run()

    wind = h2i.prob.get_val("wind.electricity_out")
    solar = h2i.prob.get_val("solar.electricity_out")

    wind_list.append(wind)
    solar_list.append(solar)

wind_gen = np.concatenate(wind_list)
solar_gen = np.concatenate(solar_list)
hybrid_gen = wind_gen + solar_gen


np.savez(Path(__file__).parent / "hybrid_gen_data", wind=wind_gen, solar=solar_gen, hybrid=hybrid_gen)

[]