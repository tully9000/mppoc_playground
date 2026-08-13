from datetime import datetime
from pathlib import Path
import yaml

from mppoc_playground.run_scripts.run_single_case import run_case


from h2integrate.core.file_utils import load_yaml


def setup_config():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create output paths
    data_root = Path(__file__).parents[1] / "run_data" / f"run_{timestamp}"
    config_root = data_root / "config"
    outputs_root = data_root / "output"

    data_root.mkdir(parents=True, exist_ok=True)
    config_root.mkdir(parents=True, exist_ok=True)
    outputs_root.mkdir(parents=True, exist_ok=True)

    base_config_root = Path(__file__).parent / "base_configs"

    # Load base configs for modification
    base_config = load_yaml(base_config_root / "config.yaml")
    base_driver_config = load_yaml(base_config_root / "driver_config.yaml")
    base_plant_config = load_yaml(base_config_root / "plant_config.yaml")
    base_tech_config = load_yaml(base_config_root / "tech_config.yaml")

    # Modify base configs

    # Set file paths in base config
    base_config["driver_config"] = str(config_root / "driver_config.yaml")
    base_config["technology_config"] = str(config_root / "tech_config.yaml")
    base_config["plant_config"] = str(config_root / "plant_config.yaml")

    # Set output path in driver config
    base_driver_config["general"]["folder_output"] = str(outputs_root)

    # TODO set UCControl params in plant_config

    base_plant_config["system_level_control"] = {
        "control_strategy": "UCControl",
        "control_parameters": {
            # UC gas-unit parameters (single aggregate NGCC, n_units = 1). Values are
            # read here so the UC MILP stays consistent with the tech_config plant.
            "gas_price": 6.09,  # $/MMBtu  (matches ng_feedstock price)
            "heat_rate_mmbtu_per_mwh": 6.3,  # MMBtu/MWh (matches natural_gas_plant)
            "gas_capacity_mw": 500.0,  # MW rated (matches natural_gas_plant)
            "gas_min_load_fraction": 0.2,  # min stable load as fraction of rated
            "gas_ramp_fraction": 1.0,  # per-hour ramp as fraction of rated (1.0 = unconstrained)
            "gas_startup_cost": 5000.0,  # $/start
            "gas_min_up_time_h": 1,  # hours
            "gas_min_down_time_h": 1,  # hours
            # Receding-horizon (MPC) settings: solve a `uc_horizon`-hour lookahead,
            # implement only the first `uc_control_step` hours, then roll forward.
            # uc_control_step: 1 => a true hourly controller, so the end-of-window
            # terminal SOC handling stays ~24 h from every applied decision.
            "uc_horizon": 48,
            "uc_control_step": 24,
            # Battery end-of-day SOC handling in the 24 h UC window:
            #   fixed_<NN>  -> force ~NN% at end of each day (±5% band, prevents
            #                  ratcheting). fixed_50 = 50%, fixed_80 = 80%, etc.
            #                  Higher targets keep more overnight reserve at the cost
            #                  of holding energy that could have served daytime load.
            #   track_init  -> end near the day's starting SOC (caps net daily
            #                  discharge, sidelines the battery -> most unmet load)
            #   charge_bias -> soft reward biases end-of-day SOC toward fully charged
            #                  (tops up from surplus renewables, keeps reserve for
            #                  overnight; still discharges deeply to serve load)
            "soc_terminal_strategy": "fixed_80",
            # Optional: $/kWh reward on terminal SOC for charge_bias. Defaults to just
            # below gas marginal cost so gas is never burned to charge the battery.
            # soc_terminal_value: 0.03
        },
        "solver_options": {
            "solver_name": "gauss_seidel",
            "max_iter": 20,
            "convergence_tolerance": 1.0e-6,
        },
    }

    # Set sweep parameters

    base_driver_config["driver"] = dict(
        parameter_sweep=dict(
            flag=True,
            debug_print=True,
            generator="fullfact",
            levels=7,
            run_parallel=True,
        )
    )
    base_driver_config["design_variables"] = dict(
        battery=dict(
            storage_capacity=dict(
                flag=True,
                lower=11000000.0,
                upper=16000000.0,
                units="kW*h",
            )
        ),
        natural_gas_plant=dict(
            system_capacity=dict(
                flag=True,
                lower=300,
                upper=700,
                units="MW",
            )
        ),
    )
    base_driver_config["recorder"] = dict(
        flag=True,
        file="cases.sql",
        overwrite_recorder=True,
        includes=["*"],
        record_desvars=True,
    )

    # Save modified configs
    def save_yaml(config, fname):
        with open(config_root / fname, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    save_yaml(base_config, "config.yaml")
    save_yaml(base_driver_config, "driver_config.yaml")
    save_yaml(base_plant_config, "plant_config.yaml")
    save_yaml(base_tech_config, "tech_config.yaml")

    run_case(config_root / "config.yaml")
    pass


def run_sweep():
    pass


if __name__ == "__main__":
    setup_config()
