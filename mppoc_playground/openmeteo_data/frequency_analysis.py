import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from matplotlib.widgets import Slider
from scipy.fft import ifft




if __name__ == "__main__":

    data = np.load(Path(__file__).parent / "hybrid_gen_data.npz")

    wind_gen = data["wind"]
    solar_gen = data["solar"]
    hybrid_gen = data["hybrid"]

    df_gen = pd.DataFrame(dict(wind=wind_gen, solar=solar_gen, hybrid=hybrid_gen))
    date_range = pd.date_range(start="1995-01-01 00:00", end="2024-12-31 23:59", freq="h")
    df_gen.index = date_range[~((date_range.month == 2) & (date_range.day == 29))]

    rolling_kw = dict(center=True)


    # 1. Generate a synthetic signal
    sampling_rate = 1/3600 # Hz (Number of samples per second)
    # t = np.arange(0, duration, 1 / sampling_rate)
    t = np.arange(0, df_gen.shape[0] * 3600, 1/sampling_rate)

    # Mix two sine waves: 50 Hz and 120 Hz
    # signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)
    signal = df_gen["solar"].to_numpy()

    # 2. Compute the Fourier Transform
    n = len(signal)
    fft_output = np.fft.fft(signal)
    frequencies = np.fft.fftfreq(n, 1 / sampling_rate)

    # 3. Take the absolute value to get the magnitude spectrum
    # Scale by 'n' to normalize amplitudes
    magnitude = np.abs(fft_output) / n

    # 4. Filter for positive frequencies (FFT outputs symmetric negative frequencies)
    positive_frequencies = frequencies[:n // 2]
    positive_magnitude = magnitude[:n // 2] * 2  # Multiply by 2 to account for energy split


    # Now try reconstructing everywhere the magnitude of the spectrum is greater than 1000 units
    trunc_threshold = 1e4

    trunc_bool = np.zeros(len(fft_output))

    for i in range(len(fft_output)):

        if np.abs(fft_output[i])/n >= trunc_threshold:
            trunc_bool[i] =  1
        elif np.abs(frequencies[i]) <= ((1 / (8760)) / 3600):
            trunc_bool[i] = 1
        elif np.abs(frequencies[i]) >= ((1 / (12)) / 3600):
            trunc_bool[i] = 1


    # Default truncation parameters
    low_freq_cutoff = (1 / (8760)) / 3600
    high_freq_cutoff = (1 / (12)) / 3600

    def make_trunc(fft_out, freqs, thresh, low_cut, high_cut):
        trunc_bool = np.zeros(len(fft_out))
        for i in range(len(fft_out)):
            if np.abs(fft_out[i]) / n >= thresh:
                trunc_bool[i] = 1
            elif np.abs(freqs[i]) <= low_cut:
                trunc_bool[i] = 1
            elif np.abs(freqs[i]) >= high_cut:
                trunc_bool[i] = 1
        return np.where(trunc_bool == 1, fft_out, 0)

    fft_trunc = make_trunc(fft_output, frequencies, trunc_threshold, low_freq_cutoff, high_freq_cutoff)
    # fft_trunc = np.where(np.abs(fft_output)/n >= trunc_threshold, fft_output, 0)




    # 5. Plot the results
    fig, ax = plt.subplots(1, 1, figsize=(10, 4), layout="constrained")
    ax.plot(positive_frequencies, positive_magnitude)
    ax.set_title("Frequency Spectrum")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude")
    ax.grid(True)

    ax.plot(positive_frequencies, (np.abs(fft_trunc)/n)[:n//2]*2 )


    ax.set_xscale("log")

    # In hours
    periods = np.flip(np.array([2, 6, 12, 24, 7*24, 30*24, 8760]))
    xt_labels = ["1 yr", "1 mn", "1 wk", "1 day", "12 hr", "6 hr", "2 hr"]
    xt_freqs = (1 / periods) / 3600


    ax.set_xticks(xt_freqs, xt_labels)

    positive_magnitude_db = 20 * np.log10(positive_magnitude)

    fig, ax = plt.subplots(1, 1, figsize=(10, 4), layout="constrained")
    ax.plot(positive_frequencies, positive_magnitude_db)
    ax.set_title("Frequency Spectrum")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude")
    ax.grid(True)

    # old_xticks = ax.get_xticks()

    # new_xticks = list(3600 / ax.get_xticks())
    # new_xticklabels = [f"{xt:.1f}" for xt in new_xticks]
    # ax.set_xticks(old_xticks, new_xticklabels)

    ax.set_xscale("log")

    # In hours
    periods = np.flip(np.array([2, 6, 12, 24, 7*24, 30*24, 8760]))
    xt_labels = ["1 yr", "1 mn", "1 wk", "1 day", "12 hr", "6 hr", "2 hr"]
    xt_freqs = (1 / periods) / 3600


    ax.set_xticks(xt_freqs, xt_labels)

    ax.plot(positive_frequencies, 20 * np.log10((np.abs(fft_trunc)/n)[:n // 2] * 2))


    fft_recon = np.fft.ifft(fft_output).real
    fft_recon_trunc = np.fft.ifft(fft_trunc).real

    fig, ax = plt.subplots(1, 1, layout="constrained")

    plt_range = range(0, 8760)
    time = t[plt_range]

    ax.plot(time, df_gen["solar"].to_numpy()[plt_range], color="gray", alpha=0.5)
    ax.plot(time, fft_recon[plt_range])
    ax.plot(time, fft_recon_trunc[plt_range])




    
    # Set up figure with sliders and reconstruction plot
    fig, ax = plt.subplots(3, 1, figsize=(10, 6), gridspec_kw={"height_ratios": [2, 2, 1]}, layout="constrained")

    ax[2].set_visible(False)

    orig_line, = ax[0].plot(time, df_gen["solar"].to_numpy()[plt_range], color="gray", alpha=0.5, label="original")
    recon_line, = ax[0].plot(time, fft_recon[plt_range], label="full ifft")
    recon_trunc_line, = ax[0].plot(time, fft_recon_trunc[plt_range], label="trunc ifft")
    ax[0].legend()
    ax[0].set_ylabel("Power")

    # Show the (positive) magnitude spectrum on the lower axis for reference
    ax[1].plot(positive_frequencies, positive_magnitude_db)

    spec_line, = ax[1].plot(positive_frequencies, 20 * np.log10((np.abs(fft_trunc)/n)[:n//2]*2), color="C1")

    ax[1].set_xscale("log")
    ax[1].set_xlabel("Frequency (Hz)")
    ax[1].set_ylabel("Amplitude")

    # In hours
    periods = np.flip(np.array([2, 6, 12, 24, 7*24, 30*24, 8760]))
    xt_labels = ["1 yr", "1 mn", "1 wk", "1 day", "12 hr", "6 hr", "2 hr"]
    xt_freqs = (1 / periods) / 3600
    ax[1].set_xticks(xt_freqs, xt_labels)

    # Slider axes
    axcolor = "lightgoldenrodyellow"
    ax_thresh = fig.add_axes([0.15, 0.03, 0.7, 0.03], facecolor=axcolor)
    ax_low = fig.add_axes([0.15, 0.07, 0.7, 0.03], facecolor=axcolor)
    ax_high = fig.add_axes([0.15, 0.11, 0.7, 0.03], facecolor=axcolor)

    # Slider ranges: threshold log-scale, frequency cutoffs between min and max
    thresh_slider = Slider(ax_thresh, "trunc_threshold", 1e2, 1e5, valinit=trunc_threshold, valfmt="%1.0f")
    low_slider = Slider(ax_low, "low_freq_cutoff", 0.0, 1/(24*7*3600), valinit=low_freq_cutoff, valfmt="%1.6f")
    high_slider = Slider(ax_high, "high_freq_cutoff", 0.0, np.max(np.abs(frequencies)), valinit=high_freq_cutoff, valfmt="%1.6f")

    def update(val):
        th = thresh_slider.val
        lowc = low_slider.val
        highc = high_slider.val

        new_fft_trunc = make_trunc(fft_output, frequencies, th, lowc, highc)
        # recompute truncated ifft using scipy.fft.ifft for user's request
        new_recon_trunc = ifft(new_fft_trunc).real

        # update time-domain plot
        recon_trunc_line.set_ydata(new_recon_trunc[plt_range])

        # update spectrum lower plot (positive half)
        new_mag = (np.abs(new_fft_trunc)/n)[:n//2]*2
        new_mag = np.where(new_mag == 0, 0.01, new_mag)
        new_spec = 20 * np.log10(new_mag)
        # new_spec = np.where(np.isnan(new_spec), 0, new_spec)

        spec_line.set_ydata(new_spec)

        fig.canvas.draw_idle()

    thresh_slider.on_changed(update)
    low_slider.on_changed(update)
    high_slider.on_changed(update)

    plt.show()





