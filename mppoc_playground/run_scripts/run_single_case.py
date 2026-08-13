from pathlib import Path
import sys


from h2integrate.core.h2integrate_model import H2IntegrateModel
from h2integrate.core.supported_models import supported_models

repo_root = Path(__file__).resolve().parents[3] / "mppoc-datacenter-h2i"
sys.path.insert(0, str(repo_root))

from uc_control import UCControl  # noqa: E402
from uc_control import DispatchableFirstControl

supported_models["UCControl"] = UCControl
supported_models["DispatchableFirstControl"] = DispatchableFirstControl



def run_case(config_path):


    model = H2IntegrateModel(config_path)
    # model.prob.driver.add_recorder(om.SqliteRecorder("doe_driver.sql"))
    model.run()




if __name__ == "__main__":
    config_root = Path(__file__).parent / "base_configs"

    run_case(config_path=config_root / "config.yaml")


    pass