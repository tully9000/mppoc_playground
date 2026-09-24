from h2integrate import H2IntegrateModel
import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy
import openmdao.api as om


from pathlib import Path
import yaml

# config_root = Path(__file__).parent / "base_configs"
config_root = Path(__file__).parent / "solar_battery"
with open(config_root / "case.yaml", "r") as f:
    config = yaml.safe_load(f)

with open(config_root / config["plant_config"], "r") as f:
    config["plant_config"] = yaml.safe_load(f)

with open(config_root / config["technology_config"], "r") as f:
    config["technology_config"] = yaml.safe_load(f)

with open(config_root / config["driver_config"], "r") as f:
    config["driver_config"] = yaml.safe_load(f)


make_plot = True
plot_optimization_evolution = True

drought_durations = [
    0,
    24,
    # 48,
    # 72,
    # 96,
    # 120,
    # 144,
]


solar_caps = []
battery_energy_caps = []
battery_power_caps = []
LCOEs = []
curtailments = []

for i, dd in enumerate(drought_durations):

    # Create an H2I model
    h2i = H2IntegrateModel(deepcopy(config))

    # h2i.model.site.solar_resource.drought_duration = 24
    h2i.model.site.solar_resource.drought_duration = dd
    h2i.model.site.solar_resource.drought_fraction = 0.125

    # Run the model
    h2i.run()

    # Post-process the results
    h2i.post_process(print_results=False)

    inputs = dict(h2i.model.list_inputs(out_stream=None))
    outputs = dict(h2i.model.list_outputs(out_stream=None))

    inputs = {k: v["val"] for k, v in inputs.items()}
    outputs = {k: v["val"] for k, v in outputs.items()}

    solar_capacity_AC = inputs["plant.solar.ATBUtilityPVCostModel.system_capacity_AC"]
    solar_capacity_DC = inputs[
        "plant.solar.PYSAMSolarPlantPerformanceModel.system_capacity_DC"
    ]
    battery_storage_capacity = inputs[
        "plant.battery.StoragePerformanceModel.storage_capacity"
    ]
    battery_charge_rate = inputs[
        "plant.battery.StoragePerformanceModel.max_charge_rate"
    ]
    LCOE = outputs[
        "plant.finance_subgroup_electricity.electricity_finance_default.LCOE"
    ]
    curtailment = outputs[
        "plant.electrical_load_demand.GenericDemandComponent.unused_electricity_out"
    ]

    solar_caps.append(solar_capacity_DC)
    battery_energy_caps.append(battery_storage_capacity)
    battery_power_caps.append(battery_charge_rate)
    LCOEs.append(LCOE)
    curtailments.append(np.sum(curtailment))

    if plot_optimization_evolution:

        rec_fpath = Path(__file__).parent / h2i.prob.driver._rec_mgr._recorders[0]._filepath
        cr = om.CaseReader(rec_fpath)

        driver_cases = cr.get_cases("driver")
        iterations = []
        
        # 3. Extract the history arrays
        iterations = []
        obj_history = []
        x_history = []

        for j, case in enumerate(driver_cases):
            iterations.append(j)

            # Get unscaled values using the promoted variable names
            # Swap 'objective_name' and 'design_var_name' with your actual variable strings
            obj_history.append(case.get_objectives()["finance_subgroup_electricity.LCOE"])
            x_history.append(case.get_design_vars()["solar.system_capacity_DC"])

        # 4. Create the convergence plot
        fig, ax = plt.subplots(2, 1, sharex=True, figsize=(8, 6), layout="constrained")

        ax[0].plot(iterations, obj_history, "b-o", label="Objective")
        ax[0].set_ylabel("Objective Value")
        ax[0].legend()
        ax[0].grid(True)

        ax[1].plot(iterations, x_history, "r-s", label="Design Variable (x)")
        ax[1].set_ylabel("Variable Value")
        ax[1].set_xlabel("COBYLA Iteration / Evaluation Index")
        ax[1].legend()
        ax[1].grid(True)




        pass


    if make_plot:
        time = np.arange(
            0,
            len(
                inputs[
                    "plant.electrical_load_demand.GenericDemandComponent.electricity_demand"
                ]
            ),
            1,
        )

        def fb(ax, x, top, bottom=None, kw={}):
            if bottom is None:
                bottom = np.zeros(len(x))

            ax.fill_between(x, bottom, bottom + top, **kw)

        solar_output = outputs[
            "plant.solar.PYSAMSolarPlantPerformanceModel.electricity_out"
        ]
        battery_output = outputs[
            "plant.battery.StoragePerformanceModel.electricity_out"
        ]
        battery_soc = outputs["plant.battery.StoragePerformanceModel.SOC"]

        curtailment = outputs[
            "plant.electrical_load_demand.GenericDemandComponent.unused_electricity_out"
        ]

        kw = dict(alpha=0.5)

        fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")

        fb(ax[0], time, solar_output, kw=kw | {"label": "Solar gen."})
        fb(ax[0], time, -curtailment, solar_output, kw=kw | {"label": "Curtailment"})
        fb(
            ax[0],
            time,
            battery_output,
            solar_output - curtailment,
            kw=kw | {"label": "Battery"},
        )

        # ax[1].plot(time, outputs["plant.electrical_load_demand.GenericDemandComponent.unused_electricity_out"])

        ax[0].set_ylim([0, 1.25e6])

        ax[1].plot(time, battery_soc, label="SOC")

        ax[0].legend(loc="upper right")
        # ax[1].legend()
        ax[1].legend(loc="upper right")

        ax[0].set_ylabel("Energy [kWh]")
        # ax[1].set_ylabel("Energy [kWh]")
        ax[1].set_ylabel("Percent")

        ax[1].set_xlabel("Time [h]")

        ax[1].set_xlim(
            [
                h2i.model.site.solar_resource.drought_start - 24,
                h2i.model.site.solar_resource.drought_start + 200,
            ]
        )

        fig.savefig(
            f"/Users/ztully/Documents/software/MPPOC/mppoc_playground/mppoc_playground/openmeteo_data/h2i_clearsky/plots/clear_sky_{dd}_drought.pdf",
            format="pdf",
        )

    []


fig, ax = plt.subplots(2, 3, sharex="all", layout="constrained")

kw = dict()

ax[0, 0].scatter(drought_durations, solar_caps, **kw)
ax[1, 0].scatter(drought_durations, LCOEs, **kw)
ax[0, 1].scatter(drought_durations, battery_energy_caps, **kw)
ax[1, 1].scatter(drought_durations, battery_power_caps, **kw)

ax[0, 2].scatter(drought_durations, curtailments, **kw)


ax[1, 0].set_xlabel("Drought duration")
ax[1, 1].set_xlabel("Drought duration")
ax[1, 2].set_xlabel("Drought duration")

ax[0, 0].set_title("Solar capacity [kW]")
ax[1, 0].set_title("LCOE [$/kWh]")
ax[0, 1].set_title("Battery energy [kWh]")
ax[1, 1].set_title("Battery power [kw]")
ax[0, 2].set_title("Curtailment [kWh]")

fig.savefig(
    "/Users/ztully/Documents/software/MPPOC/mppoc_playground/mppoc_playground/openmeteo_data/h2i_clearsky/plots/drought_duration_sweep.pdf",
    format="pdf",
)


# fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")
# ax[1].plot(h2i.model.get_val("solar.electricity_out"))

# solar_resource = dict(h2i.model.site.solar_resource.list_outputs(out_stream=None))["solar_resource_data"]["val"]
# ax[0].plot(solar_resource["ghi"])
# ax[0].plot(solar_resource["dhi"])
# ax[0].plot(solar_resource["dni"])


solar_config = config["plant_config"]["sites"]["site"]["resources"]["solar_resource"]
solar_config.pop("resource_model_location")
solar_config["resource_model"] = "OpenMeteoHistoricalSolarResource"
solar_config = config["plant_config"]["sites"]["site"]["resources"][
    "solar_resource"
] = solar_config


h2i = H2IntegrateModel(config)
h2i.run()
h2i.post_process()

ax[1].plot(h2i.model.get_val("solar.electricity_out"))

solar_resource = dict(h2i.model.site.solar_resource.list_outputs(out_stream=None))[
    "solar_resource_data"
]["val"]
ax[0].plot(solar_resource["ghi"])
ax[0].plot(solar_resource["dhi"])
ax[0].plot(solar_resource["dni"])

[]
