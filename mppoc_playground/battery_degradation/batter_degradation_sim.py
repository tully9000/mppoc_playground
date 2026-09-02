import numpy as np
import matplotlib.pyplot as plt

np.random.seed(1005)

RTE = 0.95
eta = np.sqrt(RTE)

E_capacity = 10


P_capacity = 1

x_max = E_capacity
x_min = 0

u_max = P_capacity
u_min = -P_capacity


def llc(xk, uk_planned):
    charge_headroom = x_max - xk

    discharge_headroom = x_min - xk


    uk_llc = np.min([charge_headroom, u_max, uk_planned])
    uk_llc = np.max([discharge_headroom, u_min, uk_llc])


    return uk_llc



def battery_step(xk, uk) -> tuple[float, float, float]:





    uk_llc = llc(xk, uk)

    uk = uk_llc

    if uk >= 0:

        xkp1 = xk + eta * uk
        yik = uk
        yok = 0

    elif uk < 0:

        xkp1 = xk + 1 / eta * uk
        yik = 0
        yok = -uk

    return xkp1, yik, yok


t = np.arange(0, 100, 1)


# Generate samples from random weibull distribution
rng = np.random.default_rng(seed=1001)
shape = 2.0
scale = 10
samples = scale * rng.weibull(shape, size=len(t))

# Generate samples from sine wave
amp = 3
mean = 4
per = 2 * np.pi / 24
theta = 0


samples = amp * np.sin(per * t + theta) + mean



fig, ax = plt.subplots(2, 1, layout="constrained")

ax[0].plot(samples)


def power_curve(ws):
    ws_cutin = 2
    ws_rated = 10
    ws_cutout = 25

    p_rated = 5

    cp = p_rated / ws_rated**3

    power = cp * ws**3
    power = np.where(ws < ws_cutin, 0, power)
    power = np.where(ws > ws_rated, p_rated, power)
    power = np.where(ws > ws_cutout, 0, power)

    return power


power = power_curve(samples)
ax[1].plot(power)


power_target = np.mean(power)
chg_planned =  -(power_target - power)


x_store = np.zeros(len(t))
yi_store = np.zeros(len(t))
yo_store = np.zeros(len(t))


xk = 0

for k in range(len(t)):

    xkp1, yi, yo = battery_step(xk, chg_planned[k])

    x_store[k] = xk
    yi_store[k] = yi
    yo_store[k] = yo

    xk = xkp1


fig, ax = plt.subplots(5, 1, sharex="all", sharey="all", layout="constrained")

ax[0].plot(t, power, label="power")
ax[0].axhline(power_target, color="black", linewidth=0.5)
ax[1].plot(t, chg_planned, label="charging")
ax[2].plot(t, yi_store, label="energy in")
ax[3].plot(t, yo_store, label="energy out")

# ax[4].plot(t, x_store, label="energy stored")

ax[4].axhline(power_target, color="black", linewidth=0.5)
ax[4].plot(t, power - yi_store + yo_store, label="system energy out")


for i in range(ax.shape[0]):
    ax[i].legend(loc="upper right")

ax[-1].set_xlabel("time [h]")

fig, ax = plt.subplots(1,1, layout="constrained")
ax.plot(t, x_store)


[]
