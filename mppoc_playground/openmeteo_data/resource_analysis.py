import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

data_path = Path(__file__).parent / "openmeteo_data.csv"


data = np.load(Path(__file__).parent / "hybrid_gen_data.npz")

wind_gen = data["wind"]
solar_gen = data["solar"]
hybrid_gen = data["hybrid"]

df_gen = pd.DataFrame(dict(wind=wind_gen, solar=solar_gen, hybrid=hybrid_gen))
date_range = pd.date_range(start="1995-01-01 00:00", end="2024-12-31 23:59", freq="h")
df_gen.index = date_range[~((date_range.month == 2) & (date_range.day == 29))]

rolling_kw = dict(center=True)


fig, ax = plt.subplots(2, 2, sharex="all", sharey="all", layout="constrained")

ax[0, 0].plot(df_gen["hybrid"].to_numpy())

hybrid24 = df_gen["hybrid"].rolling(window=24, **rolling_kw).mean().to_numpy()
ax[1, 0].plot(hybrid24 )

ax[0, 0].set_title(f"No filter, min. gen.: {np.min(df_gen['hybrid']):.2f}")
ax[1, 0].set_title(f"24 hr MA filter, min. gen.: {np.min(hybrid24[24:-24]):.2f}")

ax[0, 1].plot(np.sort(df_gen["hybrid"]))
ax[1, 1].plot(np.sort(hybrid24))




ma_widths = np.array(
    [
        6,
        24,
        5 * 24,
        10 * 24,
        30 * 24,
        3 * 30 * 24,
        8760,
    ]
)

def detect_events(ts, threshold):
    in_event = False
    events = []
    for k in range(len(ts)):
        if ts[k] < threshold:
            if in_event:
                # continuing from a ongoing event
                pass
            else:
                # Start of a new event
                this_event = dict(start=k, stop=-1)
            in_event = True
        else:
            if in_event:
                # End of the event
                this_event["stop"] = k
                events.append(this_event)
            else:
                # wasn't in an event to begin with
                pass
            in_event = False
    return events


def process_events(events, ts, threshold):
    for event in events:
        start_idx = event["start"]
        stop_idx = event["stop"]

        duration = stop_idx - start_idx
        deficit = threshold - ts[start_idx:stop_idx]
        mean_deficit = np.mean(deficit)
        max_deficit = np.max(deficit)
        total_deficit = np.sum(deficit)

        event.update(
            dict(
                duration=duration,
                mean_deficit=mean_deficit,
                total_deficit=total_deficit,
                max_deficit=max_deficit,
            )
        )

    return events


mean_gen = 0.5 * np.mean(hybrid_gen)
ma_gen = df_gen["hybrid"].rolling(window=24, **rolling_kw).mean().to_numpy()
events = detect_events(ma_gen, threshold=mean_gen)
events_processd = process_events(events, ma_gen, mean_gen)


def plot_metrics(events):

    keys = events[0].keys()
    keys = [k for k in keys if not ((k == "start") or (k == "stop"))]

    fig, ax = plt.subplots(len(keys), len(keys), layout="constrained")

    for i, ki in enumerate(keys):

        data_i = np.array([d[ki] for d in events])

        for j, kj in enumerate(keys):

            if j > i:
                ax[i, j].set_visible(False)
                continue

            data_j = np.array([d[kj] for d in events])

            ax[i, j].scatter(data_j, data_i, marker=".", alpha=0.2)

            if i == len(keys) - 1:
                ax[i, j].set_xlabel(kj)

            if j == 0:
                ax[i, j].set_ylabel(ki)


plot_metrics(events_processd)


fig, ax = plt.subplots(4, 1, sharex="all", layout="constrained")


keys = ['duration', 'mean_deficit', 'total_deficit', 'max_deficit']
all_data = {k:[] for k in keys}

for i, maw in enumerate(ma_widths):
    mean_gen = np.mean(hybrid_gen)
    ma_gen = df_gen["hybrid"].rolling(window=maw, **rolling_kw).mean().to_numpy()
    events = detect_events(ma_gen, threshold=mean_gen)
    events_processd = process_events(events, ma_gen, mean_gen)


    keys = events[0].keys()
    keys = [k for k in keys if not ((k == "start") or (k == "stop"))]

    for j, k in enumerate(keys):

        data_k = [d[k] for d in events_processd]
        all_data[k].append(data_k)

        # ax[j].scatter(maw * np.ones(len(worst_10)), worst_10)
        # ax[j].set_ylabel(k)

for i, k in enumerate(keys):
    ax[i].violinplot(all_data[k], showmeans=True, showmedians=False)
    ax[i].set_ylabel(k)
    ax[i].yaxis.grid(True, alpha=0.5)


# ax[0].set_xscale("log")
ax[-1].set_xticks(np.arange(1, len(ma_widths)+1), ma_widths)
ax[-1].set_xlabel("Moving average filter width")

fig.align_labels()



fig, ax = plt.subplots(4, 1, sharex="all", layout="constrained")



for i, maw in enumerate(ma_widths):
    mean_gen = np.mean(hybrid_gen)
    ma_gen = df_gen["hybrid"].rolling(window=maw, **rolling_kw).mean().to_numpy()
    events = detect_events(ma_gen, threshold=mean_gen)
    events_processd = process_events(events, ma_gen, mean_gen)


    keys = events[0].keys()
    keys = [k for k in keys if not ((k == "start") or (k == "stop"))]

    for j, k in enumerate(keys):

        worst_10 = np.sort([d[k] for d in events_processd])[-10:]

        ax[j].scatter(maw * np.ones(len(worst_10)), worst_10)
        ax[j].set_ylabel(k)

ax[0].set_xscale("log")
ax[-1].set_xticks(ma_widths)
ax[-1].set_xlabel("Moving average filter width")

fig.align_labels()










df = pd.read_csv(data_path, index_col=0)


mean_ws = df["wind_speed_100m"].mean()
ma_ws = df["wind_speed_100m"].rolling(window=int(24), **rolling_kw).mean().to_numpy()

events_24 = detect_events(ma_ws, mean_ws)
events_24_processed = process_events(events_24, ma_ws, mean_ws)


fig, ax = plt.subplots(4, 4, layout="constrained")

keys = events_24_processed[0].keys()
keys = [k for k in keys if not ((k == "start") or (k == "stop"))]


for i, ki in enumerate(keys):

    data_i = np.array([d[ki] for d in events_24_processed])

    for j, kj in enumerate(keys):

        if j > i:
            ax[i, j].set_visible(False)
            continue

        data_j = np.array([d[kj] for d in events_24_processed])

        ax[i, j].scatter(data_j, data_i, marker=".", alpha=0.2)

        if i == len(keys) - 1:
            ax[i, j].set_xlabel(kj)

        if j == 0:
            ax[i, j].set_ylabel(ki)


fig, ax = plt.subplots(5, 1, sharex="all", layout="constrained")


def plot_sorted_metric(ax, key, data):
    ax.plot(np.sort([d[key] for d in data]))
    ax.set_title(key)


plot_sorted_metric(ax[0], "duration", events_24_processed)
plot_sorted_metric(ax[1], "mean_deficit", events_24_processed)
plot_sorted_metric(ax[2], "total_deficit", events_24_processed)
plot_sorted_metric(ax[3], "max_deficit", events_24_processed)


ma_10day = df["wind_speed_100m"].rolling(window=int(10 * 24), **rolling_kw).mean()
ma_10_min_idx = ma_10day.argmin()


ma_widths = np.array(
    [
        # 6,
        24,
        5 * 24,
        10 * 24,
        30 * 24,
        3 * 30 * 24,
        # 8760,
    ]
)
min_idx = np.zeros_like(ma_widths)

fig, ax = plt.subplots(
    len(ma_widths), 1, sharex="all", sharey="all", layout="constrained"
)


for i, maw in enumerate(ma_widths):
    ma = df["wind_speed_100m"].rolling(window=maw, **rolling_kw).mean()
    ma_idx = ma.argmin()
    min_idx[i] = ma_idx

    ax[i].plot(ma.to_numpy())
    ax[i].scatter(ma_idx, ma.iloc[ma_idx], color="orange")


fig, ax = plt.subplots(2, 1, sharex="all", layout="constrained")

ax[0].plot(df["wind_speed_100m"].to_numpy(), alpha=0.25, linewidth=0.5, color="gray")
ax[0].plot(ma_10day.to_numpy())
ax[0].scatter(ma_10_min_idx, ma_10day.iloc[ma_10_min_idx], color="orange")


[]
