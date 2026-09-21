import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

from typing import Sequence

from pyomo.environ import (
    ConcreteModel,
    Constraint,
    NonNegativeReals,
    Objective,
    Param,
    RangeSet,
    SolverFactory,
    Var,
    value,
)


def build_model(
    generation: Sequence[float],
    demand: float = 0.0,
    initial_soc: float = 0.5,
    min_soc: float = 0.0,
    charge_efficiency: float = 1,
    discharge_efficiency: float = 1,
):

    n_steps = len(generation)

    model = ConcreteModel()
    model.T = RangeSet(0, n_steps - 1)

    model.generation = Param(
        model.T, initialize={t: float(generation[t]) for t in model.T}
    )
    model.demand = Param(initialize=demand)

    model.charge = Var(model.T, domain=NonNegativeReals, initialize=0.0)
    model.discharge = Var(model.T, domain=NonNegativeReals, initialize=0.0)
    model.soc = Var(model.T, domain=NonNegativeReals, initialize=0.0)
    model.curtail = Var(model.T, domain=NonNegativeReals, initialize=0.0)

    model.energy_capacity = Var(domain=NonNegativeReals, initialize=0.0)
    model.power_capacity = Var(domain=NonNegativeReals, initialize=0.0)

    model.charge_limit = Constraint(
        model.T,
        rule=lambda m, t: m.charge[t] <= model.power_capacity,
    )
    model.discharge_limit = Constraint(
        model.T,
        rule=lambda m, t: m.discharge[t] <= model.power_capacity,
    )

    model.soc_min = Constraint(
        model.T,
        rule=lambda m, t: m.soc[t] >= min_soc,
    )
    model.soc_max = Constraint(
        model.T,
        rule=lambda m, t: m.soc[t] <= model.energy_capacity,
    )

    def soc_balance_rule(m, t):
        # if t == 0:
        #     return (
        #         m.soc[t]
        #         == initial_soc
        #         + charge_efficiency * m.charge[t]
        #         - m.discharge[t] / discharge_efficiency
        #     )
        if t == 0:
            return Constraint.Feasible
        return (
            m.soc[t]
            == m.soc[t - 1]
            + charge_efficiency * m.charge[t]
            - m.discharge[t] / discharge_efficiency
        )

    model.soc_balance = Constraint(model.T, rule=soc_balance_rule)

    model.power_balance = Constraint(
        model.T,
        rule=lambda m, t: m.demand
        == m.generation[t] - m.charge[t] + m.discharge[t] - m.curtail[t],
    )

    model.continuity = Constraint(rule=lambda m: m.soc[0] == m.soc[len(m.T)-1])

    model.obj = Objective(expr=469 * model.energy_capacity + 1876 * model.power_capacity, sense="minimize")

    return model

def solve_model(**kwargs):

    model = build_model(**kwargs)

    solver_name = None
    for candidate in ("highs", "cbc", "glpk"):
        solver = SolverFactory(candidate)
        if solver.available():
            solver_name = candidate
            break

    if solver_name is None:
        raise RuntimeError(
            "No usable Pyomo solver was found. Install one such as highs, cbc, or glpk."
        )

    solver = SolverFactory(solver_name)
    results = solver.solve(model)
    return model, results


if __name__ == "__main__":


    data = np.load(Path(__file__).parent / "hybrid_gen_data.npz")

    wind_gen = data["wind"]
    solar_gen = data["solar"]
    hybrid_gen = data["hybrid"]

    df_gen = pd.DataFrame(dict(wind=wind_gen, solar=solar_gen, hybrid=hybrid_gen))
    date_range = pd.date_range(start="1995-01-01 00:00", end="2024-12-31 23:59", freq="h")
    df_gen.index = date_range[~((date_range.month == 2) & (date_range.day == 29))]

    rolling_kw = dict(center=True)



    # generation = hybrid_gen[0:8760]
    # generation = hybrid_gen[0:4380]
    # generation = solar_gen[0:600]
    generation = solar_gen[0:8760]
    # generation = wind_gen[0:8760]

    # generation = df_gen["solar"].rolling(window=24, **rolling_kw).mean().to_numpy()[24:8760]
    demand = 0.75 * np.mean(generation)

    model, results = solve_model(
        generation=generation,
        demand=demand,
        initial_soc = np.mean(generation)
    )



    def plot_case(model, title=""):

        fig, ax = plt.subplots(3, 1, sharex="all", layout="constrained", figsize=(8, 6))


        time = np.array(model.T)
        generation = np.array([value(model.generation[t]) for t in time])
        charge = np.array([value(model.charge[t]) for t in time])
        discharge = np.array([value(model.discharge[t]) for t in time])
        curtail = np.array([value(model.curtail[t]) for t in time])
        soc = np.array([value(model.soc[t]) for t in time])

        e_cap = value(model.energy_capacity)
        p_cap = value(model.power_capacity)


        fill_kw = dict(
            alpha=0.5,
            step="post"
        )


        ax[0].fill_between(time, np.zeros_like(generation), generation, **fill_kw, label="generation")


        ax[0].plot(generation - charge - curtail + discharge, label="demand")
        ax[0].legend()

        ax[1].step(time, generation, where="post", color="blue", label="generation")

        ax[1].fill_between(time, generation, generation - curtail, **fill_kw, label="curtail")
        ax[1].fill_between(time, generation - curtail, generation -curtail - charge, **fill_kw, label="charging")
        ax[1].fill_between(time, generation, generation + discharge, **fill_kw, label="discharging")

        ax[1].step(time, value(model.demand) * np.ones_like(time), where="post", color="black")

        ax[1].legend(ncols=1, loc="upper right")

        ax[2].plot(time, soc)
        # ax[2].set_ylim([0, 6e7])
        ax[2].set_ylim([0, 1e8])

        

        ax[0].set_ylabel("Energy [kWh]")
        ax[1].set_ylabel("Energy [kWh]")
        ax[2].set_ylabel("Charge state [kWh]")
        ax[2].set_xlabel("Time [hr]")


        fig.suptitle(f"Fraction of mean gen. {float(title):.1f}")

        fig.align_labels()

        return fig, ax


    n_cases = 20


    demands = []
    curtails = []
    e_caps = []
    p_caps = []
    socs = []



    fractions = np.linspace(0.01, 0.99, n_cases)
    fractions = np.arange(0.1, 1, 0.1)

    case_figax = []

    # for i in range(n_cases):
    for i in range(len(fractions)):

        print(f"\r{i:>4}/{n_cases}\t\t", end="")


        demand_i = fractions[i] * np.mean(generation)



        model, results = solve_model(
            generation=generation,
            demand=demand_i,
        )
        time = np.array(model.T)

        curtail = np.array([value(model.curtail[t]) for t in time])

        e_cap = value(model.energy_capacity)
        p_cap = value(model.power_capacity)

        demands.append(np.mean(demand_i))
        curtails.append(np.mean(curtail))
        e_caps.append(e_cap)
        p_caps.append(p_cap)
        socs.append(np.array([value(model.soc[t]) for t in time]))


        if np.isclose(fractions[i], 0.3) or (np.isclose(fractions[i], 0.6)) or np.isclose(fractions[i], 0.9):
            fig, ax = plot_case(model, f"{fractions[i]}")
            case_figax.append((fig, ax))
            []


    if True:

        for f, a in case_figax:
            title = f.get_suptitle()
            f.savefig(f"/Users/ztully/Documents/software/MPPOC/mppoc_playground/mppoc_playground/openmeteo_data/plots/{title.replace(' ', '_')}_full.pdf", format="pdf")


        for f,a in case_figax:
            title = f.get_suptitle()

            zoom_xlim = [4900, 5250]

            rect_height = a[2].get_ylim()[1] - a[2].get_ylim()[0]
            rect = mpatches.Rectangle((zoom_xlim[0], 0), width=(zoom_xlim[1] - zoom_xlim[0]), height=rect_height, facecolor="yellow", alpha=0.25)

            a[2].add_patch(rect)

            f.savefig(f"/Users/ztully/Documents/software/MPPOC/mppoc_playground/mppoc_playground/openmeteo_data/plots/{title.replace(' ', '_')}_zoom_rect.pdf", format="pdf")

            rect.set_visible(False)

            a[2].set_ylim([0,4e7])

            a[0].set_xlim(zoom_xlim)
            f.savefig(f"/Users/ztully/Documents/software/MPPOC/mppoc_playground/mppoc_playground/openmeteo_data/plots/{title.replace(' ', '_')}_zoom.pdf", format="pdf")



    demands = np.array(demands) / np.mean(generation)
    e_caps = np.array(e_caps)
    p_caps = np.array(p_caps)
    durations = e_caps / p_caps
    curtails = np.array(curtails)


    fig, ax = plt.subplots(3, 2, layout="constrained", figsize=(10, 6))


    ax[0, 0].plot(demands, curtails)
    ax[1, 0].plot(demands, e_caps)
    ax[2, 0].plot(demands, p_caps)

    ax[0, 1].plot(demands, 1876 * np.array(p_caps) + 469 * np.array(e_caps))
    # ax[0, 1].plot(demands, 0.07 * curtails)
    # ax[0, 1].plot(demands, 0.07 * demands * np.mean(generation) * len(generation))
    ax[1, 1].plot(demands, durations)

    ax[0, 0].set_title("Total curtailment")
    ax[1, 0].set_title("Energy capacity")
    ax[2, 0].set_title("Power capacity")

    ax[0, 1].set_title("Total cost")
    ax[1, 1].set_title("Duration")

    ax[-1, 0].set_xlabel("Fraction of mean gen.")
    # ax[-1, 1].set_xlabel("Fraction of mean gen.")


    fractions_to_plot  = [0.1, 0.3, 0.6, 0.9]

    for i in range(len(fractions)):
        plot_i = np.any([np.isclose(fractions[i], ftp) for ftp in fractions_to_plot])
        if plot_i:
            ax[2, 1].plot(time, socs[i], color=plt.colormaps["plasma"](i/len(fractions)), zorder=1 - i/len(fractions), label=f"Fraction: {fractions[i]:.2f}")

    ax[2, 1].legend()
    ax[2, 1].set_title("SOC")

    fig.savefig(f"/Users/ztully/Documents/software/MPPOC/mppoc_playground/mppoc_playground/openmeteo_data/plots/sweep.pdf", format="pdf")


    []


