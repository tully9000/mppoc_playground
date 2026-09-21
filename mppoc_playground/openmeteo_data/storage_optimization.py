import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt


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


def build_storage_dispatch_model(
    # prices: Sequence[float],
    variable_gen: Sequence[float],
    *,
    storage_capacity: float = 50.0,
    charge_power_limit: float = 20.0,
    discharge_power_limit: float = 20.0,
    initial_soc: float = 0.0,
    min_soc: float = 0.0,
    charge_efficiency: float = 0.95,
    discharge_efficiency: float = 0.95,
    final_soc: float | None = None,
):
    """Build a simple arbitrage/dispatch model for a battery connected to the grid."""
    # if len(prices) != len(demand):
    #     raise ValueError("prices and demand must have the same length")

    n_steps = len(variable_gen)
    if n_steps == 0:
        raise ValueError("At least one time step is required")

    if final_soc is None:
        final_soc = initial_soc

    model = ConcreteModel()
    model.T = RangeSet(0, n_steps - 1)

    # model.price = Param(model.T, initialize={t: float(prices[t]) for t in model.T})
    # model.demand = Param(model.T, initialize={t: float(demand[t]) for t in model.T})
    model.vargen = Param(
        model.T, initialize={t: float(variable_gen[t]) for t in model.T}
    )

    model.demand = Var(domain=NonNegativeReals, initialize=0.0)

    model.charge = Var(model.T, domain=NonNegativeReals, initialize=0.0)
    model.discharge = Var(model.T, domain=NonNegativeReals, initialize=0.0)
    # model.grid_import = Var(model.T, domain=NonNegativeReals, initialize=0.0)
    model.soc = Var(model.T, domain=NonNegativeReals, initialize=initial_soc)
    model.curtail = Var(model.T, domain=NonNegativeReals, initialize=0.0)

    model.charge_limit = Constraint(
        model.T,
        rule=lambda m, t: m.charge[t] <= charge_power_limit,
    )
    model.discharge_limit = Constraint(
        model.T,
        rule=lambda m, t: m.discharge[t] <= discharge_power_limit,
    )

    model.soc_min = Constraint(
        model.T,
        rule=lambda m, t: m.soc[t] >= min_soc,
    )
    model.soc_max = Constraint(
        model.T,
        rule=lambda m, t: m.soc[t] <= storage_capacity,
    )

    def soc_balance_rule(m, t):
        if t == 0:
            return (
                m.soc[t]
                == initial_soc
                + charge_efficiency * m.charge[t]
                - m.discharge[t] / discharge_efficiency
            )
        return (
            m.soc[t]
            == m.soc[t - 1]
            + charge_efficiency * m.charge[t]
            - m.discharge[t] / discharge_efficiency
        )

    model.soc_balance = Constraint(model.T, rule=soc_balance_rule)

    model.power_balance = Constraint(
        model.T,
        # rule=lambda m, t: m.grid_import[t] + m.discharge[t] == m.demand[t] + m.charge[t],
        rule=lambda m, t: m.demand
        == m.vargen[t] - m.charge[t] + m.discharge[t] - m.curtail[t],
    )
    # model.power_balance = Constraint(
    #     model.T,
    #     rule=lambda m, t: m.grid_import[t] + m.discharge[t] == m.demand[t] + m.charge[t],
    # )

    model.final_soc_constraint = Constraint(
        expr=model.soc[n_steps - 1] == initial_soc,
    )

    # model.initial_soc_constraint = Constraint(
    #     expr=model.soc[0] == initial_soc,
    # )

    model.obj = Objective(
        expr=-model.demand,
        sense="minimize",
    )
    # model.obj = Objective(
    #     expr=sum(model.price[t] * model.grid_import[t] for t in model.T),
    #     sense="minimize",
    # )

    return model


def solve_storage_dispatch(
    prices: Sequence[float],
    **kwargs,
):
    model = build_storage_dispatch_model(prices, **kwargs)

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
    # model.solutions.store(results)
    return model


if __name__ == "__main__":

    data = np.load(Path(__file__).parent / "hybrid_gen_data.npz")

    wind_gen = data["wind"]
    solar_gen = data["solar"]
    hybrid_gen = data["hybrid"]



    # Example: a simple time-varying price profile with a fixed demand profile.
    prices = [40, 30, 25, 80, 90, 45]
    demand = [20, 18, 22, 30, 40, 25]
    variable_gen = [15, 30, 25, 28, 22, 18]
    variable_gen = [25, 20, 20, 20, 15, 20]
    variable_gen = hybrid_gen[0:int(5*8760)]
    demand = np.ones(len(variable_gen)) * np.mean(variable_gen)

    storage_capacity = 1e8

    model = solve_storage_dispatch(
        variable_gen,
        storage_capacity=storage_capacity,
        charge_power_limit=1e6,
        discharge_power_limit=1e6,
        initial_soc=0.5 * storage_capacity,
        min_soc=0,
        final_soc=0.5 * storage_capacity,
    )

    print("Time step | Var. gen.    | Charge    | Discharge    | Curtail    | SOC")
    for t in range(len(variable_gen)):
        if t > 15:
            break
        print(
            f"{t:>9} | {value(model.vargen[t]):>12.2f} |"
            f"{value(model.charge[t]):>10.2f} | {value(model.discharge[t]):>12.2f} | "
            f"{value(model.curtail[t]):>10.2f} | {value(model.soc[t]):>5.2f}"
        )

    # print(f"Objective value: {value(model.obj):.2f}")
    print(f"Highest demand: {value(model.demand):.2f}")
    print(f"Mean gen. {np.mean(variable_gen):.2f}")



    fig, ax = plt.subplots(3, 1, sharex="all", layout="constrained")

    ax[0].plot(variable_gen)
    ax[1].plot(np.array(value(model.charge[:])) - np.array(value(model.discharge[:])))
    ax[2].plot(np.array(value(model.soc[:])))



    []
    # print("Time step | Price | demand | Charge | Discharge | Grid Import | SOC")
    # for t in range(len(prices)):
    #     print(
    #         f"{t:>9} | {prices[t]:>5.1f} | {demand[t]:>4.1f} | "
    #         f"{value(model.charge[t]):>6.2f} | {value(model.discharge[t]):>9.2f} | "
    #         f"{value(model.grid_import[t]):>10.2f} | {value(model.soc[t]):>5.2f}"
    #     )

    # print(f"Objective value: {value(model.obj):.2f}")
