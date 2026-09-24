from h2integrate import H2IntegrateModel
import matplotlib.pyplot as plt

from pathlib import Path
import yaml


# config_root = Path(__file__).parent / "base_configs"
config_root = Path(__file__).parent / "solar_battery"
with open(config_root / "case.yaml", "r") as f:
    config = yaml.safe_load(f)

with open(config_root / config["plant_config"] , "r") as f:
    config["plant_config"] = yaml.safe_load(f)

with open(config_root / config["technology_config"] , "r") as f:
    config["technology_config"] = yaml.safe_load(f)

with open(config_root / config["driver_config"] , "r") as f:
    config["driver_config"] = yaml.safe_load(f)






# Create an H2I model
h2i = H2IntegrateModel(config)

# Run the model
h2i.run()

# Post-process the results
h2i.post_process()


fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")

ax[1].plot(h2i.model.get_val("solar.electricity_out"))

solar_resource = dict(h2i.model.site.solar_resource.list_outputs(out_stream=None))["solar_resource_data"]["val"]
ax[0].plot(solar_resource["ghi"])
ax[0].plot(solar_resource["dhi"])
ax[0].plot(solar_resource["dni"])


solar_config = config['plant_config']['sites']['site']['resources']['solar_resource']
solar_config.pop("resource_model_location")
solar_config["resource_model"] = "OpenMeteoHistoricalSolarResource"
solar_config = config['plant_config']['sites']['site']['resources']['solar_resource'] = solar_config




h2i = H2IntegrateModel(config)
h2i.run()
h2i.post_process()

ax[1].plot(h2i.model.get_val("solar.electricity_out"))

solar_resource = dict(h2i.model.site.solar_resource.list_outputs(out_stream=None))["solar_resource_data"]["val"]
ax[0].plot(solar_resource["ghi"])
ax[0].plot(solar_resource["dhi"])
ax[0].plot(solar_resource["dni"])

[]