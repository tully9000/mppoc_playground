from io import StringIO
import json
from pathlib import Path
from pprint import pprint
import sys
from copy import copy, deepcopy
import yaml


from h2integrate.core.h2integrate_model import H2IntegrateModel
from h2integrate.core.supported_models import supported_models


import os
import openmdao.api as om

# Register the custom system-level controller. H2Integrate's SLC framework
# only looks up `control_strategy` in `supported_models` (there is no
# `model_location` scan for the SLC block), so we inject the class into the
# module-level registry before instantiating `H2IntegrateModel`. The shared
# UCControl lives in the repo-root `uc_control` package (see its docstring for
# why a custom UC-based SLC is needed).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from uc_control import UCControl  # noqa: E402

supported_models["UCControl"] = UCControl


config_path = os.path.join(
    os.path.dirname(__file__), "configs", f"year_{2010}", "config.yaml"
)

model = H2IntegrateModel(config_path)
model.prob.driver.add_recorder(om.SqliteRecorder("doe_driver.sql"))
model.run()

[]