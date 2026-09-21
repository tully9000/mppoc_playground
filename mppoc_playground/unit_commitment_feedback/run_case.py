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
from h2integrate.core.dict_utils import percent_diff_dicts, find_nonzero_percent_diffs
from h2integrate.core.concurrent_nl_solver import ConcurrentPlantNLBGSSolver
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
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mppoc-datacenter-h2i"))
from uc_control import UCControl  # noqa: E402

supported_models["UCControl"] = UCControl


# Run one of both simulation paradigms by changing the flags in this dict
run_dict = {
    "run_sequential": True,
    # "run_concurrent": True,
    # "run_sequential_opt": True,
    # "run_concurrent_opt": True,
}


# Load config files into dict
config_root = Path(__file__).parent
config_path = config_root / "case.yaml"

# Load top level config
with Path(config_path).open() as f:
    config = yaml.safe_load(f)

config["driver_config"] = load_driver_yaml(config_root / config["driver_config"])
config["technology_config"] = load_tech_yaml(config_root / config["technology_config"])
config["plant_config"] = load_plant_yaml(config_root / config["plant_config"])


# Run simulation sequentially one subsystem at a time
if run_dict.get("run_sequential", False):
    config_seq = deepcopy(config)
    config_seq["plant_config"]["plant"]["simulation"]["n_timesteps"] = 8760
    config_seq["plant_config"]["plant"]["simulation"]["n_steps_per_compute"] = 8760

    # Create an H2I model for standard year-long simulation
    h2i_seq = H2IntegrateModel(config_seq)

    # Run the model
    h2i_seq.run()

    inputs_seq = dict(h2i_seq.model.list_inputs(out_stream=None))
    outputs_seq = dict(h2i_seq.model.list_outputs(out_stream=None))

    fig, ax = plt.subplots(2, 1, sharey="all", layout="constrained")    
    ax[0].plot(h2i_seq.model.get_val("plant.system_level_controller.battery_electricity_set_point"))
    ax[0].plot(h2i_seq.model.get_val("plant.battery.SimpleStorageOpenLoopController.electricity_set_point"))
    ax[1].plot(h2i_seq.model.get_val("plant.battery.StoragePerformanceModel.electricity_command_value"))
    ax[1].plot(h2i_seq.plant.system_level_controller._batt_schedule)


    fig, ax = plt.subplots(2,1, layout="constrained")

    ax[0].plot(h2i_seq.plant.system_level_controller.soc_store, label="UC saved SOC")
    ax[0].plot(h2i_seq.model.get_val("plant.battery.StoragePerformanceModel.SOC")/100 *  h2i_seq.plant.system_level_controller._battery_template["E_capacity"], label="Storage model SOC")

    ax[1].plot(h2i_seq.model.get_val("plant.battery.StoragePerformanceModel.SOC")/100 *  h2i_seq.plant.system_level_controller._battery_template["E_capacity"] - h2i_seq.plant.system_level_controller.soc_store, label="difference")



    # ax.set_title("Sequential")

    ax[0].legend()
    ax[1].legend()





    inputs_seq['plant.system_level_controller.solar_electricity_out']["val"][0:100]
    inputs_seq['plant.system_level_controller.wind_electricity_out']["val"][0:100]

    solar_100 = np.array([      0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,  773546.23489593,
        320456.16513803,  873163.29707553, 1451022.50159414,
       1451022.50159414, 1451022.50159414, 1451022.50159414,
       1451022.50159414,  894170.29107938,  450695.22153374,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,  848353.93538213,
        454536.32201524, 1451022.50159414, 1451022.50159414,
       1451022.50159414, 1451022.50159414, 1451022.50159414,
       1451022.50159414, 1241485.86895383,  449242.32286106,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,  859670.65398704,
        464299.033229  , 1451022.50159414, 1055892.55263528,
        991758.91989589, 1451022.50159414, 1451022.50159414,
       1434063.00144512, 1229767.93661291,  482737.40020985,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,   20864.85167508,
         72122.0239497 ,  118872.69949667,  149697.03233052,
        335676.77495377,  193521.11579109,  117905.82795802,
         85392.43328884,   50110.85438426,    2368.32887805,
             0.        ,       0.        ,       0.        ,
             0.        ])


    wind_100 = np.array([ 708417.634337  ,  589039.84645298,  636644.22376682,
        720194.70376098,  284590.91800397,  322254.08364748,
        255845.0491436 ,  235597.13103236,  190900.8222463 ,
        285422.78443104,  263199.72276743,  271654.08538859,
        249783.3331392 ,  408327.18972253,  157536.66690254,
        194422.86609995,  229307.06100473,  311095.53808225,
        188226.00746861,  191383.59383232,  150983.5245824 ,
         97571.82447343,   41167.2412124 ,  139723.82483706,
        149967.52491578,  183922.48379677,  139562.32252691,
        116618.10994432,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,   97856.24801463,  148855.70009158,
        337258.84949668,  402787.61179791,  416482.8928344 ,
        249450.02699127,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,    4411.71514603,  550239.43746939,
        612333.71857005,  804717.07691512,  565068.77559182,
        392162.90275661,  343551.58079721,  404157.44183248,
        541061.02481811,  602546.35853731,  529775.9660362 ,
        571753.97959386,  444781.68672395,  486945.31325598,
        489740.37043609,  459025.05895479,  364174.68255345,
        133153.50266035,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
        111913.01461453,  238908.36776306,  252653.39395097,
        319457.34943478,  286886.51533083,  443594.15356224,
        531200.177451  ,  613887.49535064,  707023.86629119,
        718476.62349772,  696814.69966083,  605795.71372682,
        577703.05883432,  629627.12686772,  663219.04768219,
        209083.40608797,  239367.12820491,  252797.10592432,
        227715.51592422,  221241.03560902,  267610.68419421,
        326871.68014954,  382140.25630824,  720298.99887027,
       1000597.30996149,  999462.42103466, 1000000.        ,
       1000000.        ])

    solar_sp_100 = np.array([      0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,  773546.23489593,
        320456.16513803,  873163.29707553, 1451022.50159414,
       1451022.50159414, 1451022.50159414, 1451022.50159414,
       1451022.50159414,  894170.29107938,  450695.22153374,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,  848353.93538213,
        454536.32201524, 1451022.50159414, 1451022.50159414,
       1451022.50159414, 1451022.50159414, 1451022.50159414,
       1451022.50159414, 1241485.86895383,  449242.32286106,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,  859670.65398704,
        464299.033229  , 1451022.50159414, 1055892.55263528,
        991758.91989589, 1451022.50159414, 1451022.50159414,
       1434063.00144512, 1229767.93661291,  482737.40020985,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,   20864.85167509,
         72122.0239497 ,  118872.69949667,  149697.03233052,
        335676.77495377,  193521.11579109,  117905.82795802,
         85392.43328884,   50110.85438426,    2368.32887805,
             0.        ,       0.        ,       0.        ,
             0.        ])

    wind_sp_100 = np.array([ 708417.634337  ,  589039.84645298,  636644.22376682,
        720194.70376098,  284590.91800397,  322254.08364748,
        255845.0491436 ,  235597.13103236,  190900.8222463 ,
        285422.78443104,  263199.72276743,  271654.08538859,
        249783.3331392 ,  408327.18972253,  157536.66690254,
        194422.86609995,  229307.06100473,  311095.53808225,
        188226.00746861,  191383.59383232,  150983.5245824 ,
         97571.82447343,   41167.2412124 ,  139723.82483706,
        149967.52491578,  183922.48379677,  139562.32252691,
        116618.10994432,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,   97856.24801463,  148855.70009158,
        337258.84949668,  402787.61179791,  416482.8928344 ,
        249450.02699127,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,    4411.71514603,  550239.43746939,
        612333.71857005,  804717.07691512,  565068.77559182,
        392162.90275661,  343551.58079721,  404157.44183248,
        541061.02481811,  602546.35853731,  529775.9660362 ,
        571753.97959386,  444781.68672395,  486945.31325598,
        489740.37043609,  459025.05895479,  364174.68255345,
        133153.50266035,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
             0.        ,       0.        ,       0.        ,
        111913.01461453,  238908.36776306,  252653.39395097,
        319457.34943478,  286886.51533083,  443594.15356224,
        531200.177451  ,  613887.49535064,  707023.86629119,
        718476.62349772,  696814.69966083,  605795.71372682,
        577703.05883432,  629627.12686772,  663219.04768219,
        209083.40608797,  239367.12820491,  252797.10592432,
        227715.51592422,  221241.03560902,  267610.68419421,
        326871.68014954,  382140.25630824,  720298.99887027,
       1000597.30996149,  999462.42103466, 1000000.        ,
       1000000.        ])


    # fig, ax = plt.subplots(2, 1, sharex="all", sharey="all", layout="constrained")
    # ax[0].plot(wind_100, label="wind")
    # ax[0].text(0.2, 0.5, np.linalg.norm(wind_100[0:100]), transform = ax[0].transAxes)

    # ax[1].plot(solar_100, label="solar")
    # ax[1].text(0.2, 0.5, np.linalg.norm(solar_100[0:100]), transform = ax[1].transAxes)


    # ax[0].legend()
    # ax[1].legend()
    # fig.suptitle("Sequential baseline")

    # ax[1].set_xlim([0, 100])
    

# Run the simulation concurrently for all subsystems one step at a time
if run_dict.get("run_concurrent", False):
    config_con = deepcopy(config)

    config_con["plant_config"]["plant"]["simulation"]["n_timesteps"] = 8760
    # config_con["plant_config"]["plant"]["simulation"]["n_steps_per_compute"] = 24
    config_con["plant_config"]["plant"]["simulation"]["n_steps_per_compute"] = (
        config_con["plant_config"]["system_level_control"]["control_parameters"][
            "uc_control_step"
        ]
    )

    # Create an H2I model for steppable simulation
    h2i_con = H2IntegrateModel(config_con)

    h2i_con.plant.nonlinear_solver = ConcurrentPlantNLBGSSolver(h2i_con.plant_config)
    h2i_con.plant.nonlinear_solver.options["iprint"] = 0

    # Run the model
    h2i_con.run()

    inputs_con = dict(h2i_con.model.list_inputs(out_stream=None))
    outputs_con = dict(h2i_con.model.list_outputs(out_stream=None))

if run_dict.get("run_sequential", False) and run_dict.get("run_concurrent", False):

    """
    Seq. norms should be: 
    	- norm of wind = 86765385.3281787
        - norm of solar = 74658675.1915049
    """

    # print(f'Seq. solar norm: {np.linalg.norm(h2i_seq.plant.system_level_controller._avail_by_tech["solar"])}')
    # print(f'Seq. wind norm: {np.linalg.norm(h2i_seq.plant.system_level_controller._avail_by_tech["wind"])}')

    # print(f'Con. solar norm: {np.linalg.norm(h2i_con.plant.system_level_controller._avail_by_tech["solar"])}')
    # print(f'Con. wind norm: {np.linalg.norm(h2i_con.plant.system_level_controller._avail_by_tech["wind"])}')

    fig, ax = plt.subplots(2, 2, layout="constrained")
    ax[0,0].plot(h2i_seq.plant.system_level_controller.soc_store, label="seq.")
    ax[0,0].plot(h2i_con.plant.system_level_controller.soc_store, label="con.")
    ax[0, 0].set_title("SLC SOC")

    ax[0, 1].plot(h2i_seq.model.get_val("plant.battery.StoragePerformanceModel.SOC")/100 *  h2i_con.plant.system_level_controller._battery_template["E_capacity"], label="seq.")
    ax[0, 1].plot(h2i_con.model.get_val("plant.battery.StoragePerformanceModel.SOC")/100 *  h2i_con.plant.system_level_controller._battery_template["E_capacity"], label="con.")
    ax[0, 1].set_title("Model SOC")


    ax[1, 0].plot(h2i_seq.plant.system_level_controller.soc_store, label="SLC")
    ax[1, 0].plot(h2i_seq.model.get_val("plant.battery.StoragePerformanceModel.SOC")/100 *  h2i_con.plant.system_level_controller._battery_template["E_capacity"], label="SOC")
    ax[1, 0].set_title("Sequential")


    ax[1, 1].plot(h2i_con.plant.system_level_controller.soc_store, label="SLC")
    ax[1, 1].plot(h2i_con.model.get_val("plant.battery.StoragePerformanceModel.SOC")/100 *  h2i_con.plant.system_level_controller._battery_template["E_capacity"], label="SOC")
    ax[1, 1].set_title("Concurrent")

    
    for i in range(ax.shape[0]):
        for j in range(ax.shape[1]):
            ax[i, j].legend()




    inputs_pd_dict = percent_diff_dicts(inputs_seq, inputs_con)
    outputs_pd_dict = percent_diff_dicts(outputs_seq, outputs_con)

    in_abs, in_rel = find_nonzero_percent_diffs(inputs_pd_dict, dict(inputs_seq))
    out_abs, out_rel = find_nonzero_percent_diffs(outputs_pd_dict, dict(outputs_seq))

    print(len(in_abs))
    print(len(out_abs))

    def plot_comparison(keys_list, with_diff = False, sharey=True):
        fig_kw = dict(
            sharex="all",
            layout="constrained"
        )
        if sharey:
            fig_kw.update(dict(sharey="col"))


        if with_diff:
            fig, ax = plt.subplots(len(keys_list), 2, **fig_kw)
        else:
            fig, ax = plt.subplots(len(keys_list), 1, **fig_kw)

            ax = np.atleast_2d(ax).T

        for i in range(len(keys_list)):
            k, io = keys_list[i]

            # if io == "i":
            #     ts_seq = inputs_seq[k]["val"]
            #     ts_con = inputs_con[k]["val"]
            # elif io == "o":
            #     ts_seq = outputs_seq[k]["val"]
            #     ts_con = outputs_con[k]["val"]

            if k.endswith("electricity_out"):

                ts_seq = h2i_seq.model.get_val(k, units="MW")
                ts_con = h2i_con.model.get_val(k, units="MW")
            else:
                ts_seq = h2i_seq.model.get_val(k)
                ts_con = h2i_con.model.get_val(k)



            ax[i, 0].plot(ts_seq, label="seq.")
            ax[i, 0].plot(ts_con, label="con")
            ax[i, 0].legend()

            k_parts = k.split(".")
            ylabel_start = ".".join([s[0] for s in k_parts[:-1]])
            ylabel = f"{ylabel_start}: {k_parts[-1]}"
            # ax[i].set_title(ylabel)
            ax[i, 0].set_title(k)

            if with_diff:
                ax[i, 1].plot(np.abs(ts_seq - ts_con))



    plot_comparison([
        ("plant.solar.PYSAMSolarPlantPerformanceModel.electricity_out", "o"),
        ("plant.wind.PYSAMWindPlantPerformanceModel.electricity_out", "o"),
        ("plant.natural_gas_plant.NaturalGasPerformanceModel.electricity_out", "o"),
        ("plant.battery.StoragePerformanceModel.electricity_out", "o"),
        ("plant.electrical_load_demand.GenericDemandComponent.electricity_out", "o"),
    ], with_diff=True)


    plot_comparison(
        [
            ("plant.battery.StoragePerformanceModel.SOC", "o"),
            ("plant.battery.StoragePerformanceModel.electricity_command_value", "i"),
        ],
        sharey=False
    )

    # to_plot1 = [
    #     ("plant.solar.PYSAMSolarPlantPerformanceModel.electricity_command_value", "i"),
    #     ("plant.solar.controller.electricity_set_point", "i"),
    #     ("plant.wind.PYSAMWindPlantPerformanceModel.electricity_command_value", "i"),
    #     ("plant.wind.controller.electricity_set_point", "i"),
    # ]
    # plot_comparison(to_plot1)

    # to_plot2 = [
    #     ("plant.solar.PYSAMSolarPlantPerformanceModel.electricity_out", "o"),
    #     (
    #             "plant.solar.PYSAMSolarPlantPerformanceModel.uncurtailed_electricity_out",
    #         "o",
    #     ),
    #     ("plant.wind.PYSAMWindPlantPerformanceModel.electricity_out", "o"),
    #     ("plant.wind.PYSAMWindPlantPerformanceModel.uncurtailed_electricity_out", "o"),
    # ]
    # plot_comparison(to_plot2)

    []


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
print(
    "NPV Electricity: ",
    h2i.prob.get_val("finance_subgroup_natural_gas.NPV_electricity__profast_npv")[0]
    + h2i.prob.get_val(
        "finance_subgroup_renewable_generation.NPV_electricity__profast_npv"
    )[0],
)
