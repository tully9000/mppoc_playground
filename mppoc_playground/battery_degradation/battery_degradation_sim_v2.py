import numpy as np
import matplotlib.pyplot as plt


class Battery:
    def __init__(self, n_sim, e_max0, e_min0, pin_max0, pout_max0, rte0, eta_sd0):

        self.n_sim = n_sim

        self.e_max0 = e_max0
        self.e_min0 = e_min0
        self.pin_max0 = pin_max0
        self.pout_max0 = pout_max0
        self.rte0 = rte0
        self.eta_sd0 = eta_sd0

        self.e_store = np.zeros(self.n_sim)
        self.pin_store = np.zeros(self.n_sim)
        self.pout_store = np.zeros(self.n_sim)

        self.e_min = np.zeros(self.n_sim)
        self.e_max = np.zeros(self.n_sim)

        self.pin_max = np.zeros(self.n_sim)
        self.pout_max = np.zeros(self.n_sim)

        self.rte = np.zeros(self.n_sim)
        self.eta_sd = np.zeros(self.n_sim)
        self.eta_in = np.zeros(self.n_sim)
        self.eta_out = np.zeros(self.n_sim)

    def _degradation_series(self, initial_value, rate):

        final_value = initial_value * (1 - rate * self.n_sim)

        return np.linspace(initial_value, final_value, self.n_sim)

    def set_degradation_series(self, e_max_rate, pin_max_rate, pout_max_rate, rte_rate):

        self.e_max = self._degradation_series(self.e_max0, e_max_rate)
        self.pin_max = self._degradation_series(self.pin_max0, pin_max_rate)
        self.pout_max = self._degradation_series(self.pout_max0, pout_max_rate)
        self.rte = self._degradation_series(self.rte0, rte_rate)

        pass


    def plot_parameters(self):


        fig, ax = plt.subplots(4, 1, sharex="all", layout="constrained")


        pass


    def step(self):
        pass

    def _llc(self):
        pass

    def _step_storage(self):
        pass


bes = Battery(
    n_sim=100, e_max0=10, e_min0=1, pin_max0=1, pout_max0=1, rte0=0.9, eta_sd0=1
)

rate = (1 - 0.9) / bes.n_sim

bes.set_degradation_series(
    e_max_rate=rate, pin_max_rate=rate, pout_max_rate=rate, rte_rate=rate
)


[]
