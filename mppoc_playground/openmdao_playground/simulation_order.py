import numpy as np
import openmdao.api as om


run_dict = dict(
    # run_tech_group = True,
    # run_flat_org = True,
    run_submodel = True
)


class PerformanceModel(om.ExplicitComponent):
    def setup(self):
        self.add_input('x')
        self.add_output('y')

    def compute(self, inputs, outputs):
        outputs["y"] = inputs["x"]


class CostModel(om.ExplicitComponent):
    def setup(self):
        self.add_input("y")
        self.add_output("z")

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

    p = om.Problem()
    m = p.model

    submodel = om.Group()
    submodel.add_subsystem("performance1", PerformanceModel())#, promotes_inputs=["x"], promotes_outputs=["y"])
    submodel.add_subsystem("performance2", PerformanceModel())#, promotes_inputs=["x"], promotes_outputs=["y"])

    subproblem = om.Problem(model=submodel)

    subcomp = om.SubmodelComp(problem=subproblem, inputs=["performance1.x", "performance2.x"], outputs=["performance1.y", "performance2.y"])

    m.add_subsystem("subcomp", subcomp)
    m.add_subsystem("cost1", CostModel())
    m.add_subsystem("cost2", CostModel())

    m.connect("subcomp.performance1:y", "cost1.y")
    m.connect("subcomp.performance2:y", "cost2.y")


    m.nonlinear_solver = om.NonlinearBlockGS()

    p.setup()

    p.set_val("subcomp.performance1:x", 10)
    p.set_val("subcomp.performance2:x", 5)


    # p.run_model()
    p.run_driver()

    m.list_inputs()
    m.list_outputs()











[]




# class SimpleComp(om.ExplicitComponent):
#     def setup(self):
#         self.add_input('x')
#         self.add_output('y')
#         self.declare_partials('*', '*')

#     def compute(self, inputs, outputs):
#         print(f"running {self.name}")
#         outputs['y'] = 2.0*inputs['x']








# p = om.Problem()
# model = p.model
# G1 = model.add_subsystem('G1', om.Group())

# G1.add_subsystem('C2', SimpleComp())
# G1.add_subsystem('C1', SimpleComp())
# G1.add_subsystem('C3', SimpleComp())



# G1.connect('C1.y', 'C2.x')
# G1.connect('C2.y', 'C3.x')

# G1.set_order(["C1", "C2", "C3"])

# # tell OpenMDAO to auto-order the components in G1
# # G1.options['auto_order'] = True

# p.setup()
# p.run_model()

# []