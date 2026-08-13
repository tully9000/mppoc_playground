import openmdao.api as om

import numpy as np

class Subsystem1(om.ExplicitComponent):

    def setup(self):
        self.add_input("x1")
        self.add_input("x3")

        self.add_output("x2")

    def compute(self, inputs, outputs):
        a1 = 1
        a2 = 2

        outputs["x2"] = a1 * inputs["x1"] + a2 * inputs["x3"]

class Subsystem2(om.ExplicitComponent):


    def setup(self):
        self.add_input("x1")
        self.add_input("x2")

        self.add_output("x3")
        self.add_output("x4")

    def compute(self, inputs, outputs):

        b1 = 0.2
        b2 = 0.9
        outputs["x3"] = b1 * inputs["x1"] + b2 * inputs["x2"]
        outputs["x4"] = inputs["x2"] 


class System(om.Group):

    def setup(self):

        self.add_subsystem("f1", Subsystem1(), promotes_inputs=["x1", "x1"])
        self.add_subsystem("f2", Subsystem2(), promotes_inputs=["x1", "x1"]) #, promotes_outputs=["x4", "x4"])


        self.connect("f1.x2", "f2.x2")
        self.connect("f2.x3", "f1.x3")

        self.nonlinear_solver = om.NonlinearBlockGS()



p = om.Problem()
model = p.model

model.add_subsystem("sys", System())




p.setup()

p.set_val("sys.f1.x1", 1)




p.run_model()

model.list_inputs()
model.list_outputs()

[]


