import numpy as np
import openmdao.api as om


run_dict = dict(
    # run_tech_group = True,
    # run_flat_org = True,
    run_submodel = True
)


class ModelBaseClass(om.ExplicitComponent):
    def initialize(self):

        # Number of steps in overall simulation, often 8760.
        self.options.declare(
            "N_sim", default=1, types=int, desc="number of steps in simulation"
        )

        # Number of steps to simulate for each compute call. This will be 8760 if running an annual
        # simulation and 1 if running a feedback steppable simulation.
        self.options.declare(
            "N_step", default=1, types=int, desc="number of steps per compute call"
        )

    def setup(self):

        # Add time step index as an input to all models
        self.add_discrete_input("k", val=0, desc="Time step index")


class PerformanceModel(ModelBaseClass):
    def setup(self):
        super().setup()

        self.add_input('x', shape=(self.options["N_sim"], ))
        self.add_output('y', shape=(self.options["N_sim"], ))

    def compute(self, inputs, outputs, discrete_inputs, discrete_outputs):

        k = discrete_inputs["k"]


        outputs["y"] = inputs["x"]

        []


class CostModel(ModelBaseClass):
    def setup(self):
        self.add_input("y", shape=(self.options["N_sim"], ))
        self.add_output("z", shape=(1))

    def compute(self, inputs, outputs):
        outputs["z"] = 2 * np.sum(inputs[("y")])



class Technology(om.Group):
    def setup(self):

        pm = PerformanceModel()
        cm = CostModel()

        self.add_subsystem("performance", pm)
        self.add_subsystem("cost", cm)

        self.connect("performance.y", "cost.y")

class TechnologyGroup(om.Group):
    def setup(self):
        pass

class CostGroup(om.Group):
    def setup(self):
        pass




if run_dict.get("run_tech_group", False):

    p = om.Problem()
    m = p.model

    m.add_subsystem("tech1", Technology())
    m.add_subsystem("tech2", Technology())

    # m.linear_solver = om.LinearBlockGS()
    m.nonlinear_solver = om.NonlinearBlockGS()

    p.setup()

    p.set_val("tech1.performance.x", 10)
    p.set_val("tech2.performance.x", 5)


    # p.run_model()
    p.run_driver()

    m.list_inputs()
    m.list_outputs()

if run_dict.get("run_flat_org", False):

    p = om.Problem()
    m = p.model

    m.add_subsystem("cost1", CostModel())
    m.add_subsystem("cost2", CostModel())

    m.add_subsystem("performance1", PerformanceModel())
    m.add_subsystem("performance2", PerformanceModel())


    m.connect("performance1.y", "cost1.y")
    m.connect("performance2.y", "cost2.y")

    # m.linear_solver = om.LinearBlockGS()
    m.nonlinear_solver = om.NonlinearBlockGS()

    p.setup()

    p.set_val("performance1.x", 10)
    p.set_val("performance2.x", 5)


    # p.run_model()
    p.run_driver()

    m.list_inputs()
    m.list_outputs()


if run_dict.get("run_submodel", False):

    N_sim = 10
    N_step = 1

    p = om.Problem()
    m = p.model

    submodel = om.Group()
    submodel.add_subsystem("performance1", PerformanceModel(N_sim=N_sim, N_step=N_step))
    submodel.add_subsystem("performance2", PerformanceModel(N_sim=N_sim, N_step=N_step))

    subproblem = om.Problem(model=submodel)

    subcomp = om.SubmodelComp(problem=subproblem, inputs=["performance1.x", "performance2.x"], outputs=["performance1.y", "performance2.y"])

    m.add_subsystem("subcomp", subcomp)
    m.add_subsystem("cost1", CostModel(N_sim=N_sim, N_step=N_step))
    m.add_subsystem("cost2", CostModel(N_sim=N_sim, N_step=N_step))

    m.connect("subcomp.performance1:y", "cost1.y")
    m.connect("subcomp.performance2:y", "cost2.y")



    m.nonlinear_solver = om.NonlinearBlockGS()

    p.setup()

    p.set_val("subcomp.performance1:x", 10*np.ones(N_sim))
    p.set_val("subcomp.performance2:x", 5*np.ones(N_sim))


    # p.run_model()
    p.run_driver()

    inputs = m.list_inputs(print_arrays=True)
    outputs = m.list_outputs(print_arrays=True)











[]




