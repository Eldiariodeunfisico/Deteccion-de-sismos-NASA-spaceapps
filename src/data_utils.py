import pandas as pd
import numpy as np
import os
import glob
import obspy as obspy
import matplotlib.pyplot as plt
from obspy.signal.invsim import cosine_taper
from scipy.signal import find_peaks
from obspy.signal.filter import highpass
from obspy.signal.trigger import classic_sta_lta, plot_trigger, trigger_onset
from scipy.signal import hilbert
from typing import List
from scipy import signal
from matplotlib import cm

BASE_PATH: str = "data"

def load_data(file_path: str):
    try:
        df = pd.read_csv(file_path)
        return df
    except:
        print("error")

def load_special_file(file_path: str):
    try:
        st_values = obspy.read(file_path)
        return st_values
    except:
        print("error")

def plot_values_from_special_content(st_values, test_filename, arrival_time=None, title="",  plot_real=False, plot_spectogram=False):
    # This is how you get the data and the time, which is in seconds
    tr = st_values.traces[0].copy()
    tr_times = tr.times()
    tr_data = tr.data


    # Initialize figure
    if plot_spectogram:
        # To better see the patterns, we will create a spectrogram using the scipy function
        # It requires the sampling rate, which we can get from the miniseed header as shown a few cells above
        f, t, sxx = signal.spectrogram(tr_data, tr.stats.sampling_rate)
        fig = plt.figure(figsize=(10, 10))
        ax = plt.subplot(2, 1, 1)
        ax2 = plt.subplot(2, 1, 2)
        vals = ax2.pcolormesh(t, f, sxx, cmap=cm.jet, vmax=5e-17)
        ax2.set_xlim([min(tr_times),max(tr_times)])
        ax2.set_xlabel(f'Time (Day Hour:Minute)', fontweight='bold')
        ax2.set_ylabel('Frequency (Hz)', fontweight='bold')
        if plot_real and arrival_time is not None:
            starttime = tr.stats.starttime.datetime
            arrival = (arrival_time - starttime).total_seconds()
            ax2.axvline(x=arrival, c='red')
        cbar = plt.colorbar(vals, orientation='horizontal')
        cbar.set_label('Power ((m/s)^2/sqrt(Hz))', fontweight='bold')
    else:
        fig,ax = plt.subplots(1,1,figsize=(10,3))

    # Plot trace
    ax.plot(tr_times,tr_data)

    if plot_real and arrival_time is not None:
        starttime = tr.stats.starttime.datetime
        arrival = (arrival_time - starttime).total_seconds()
        # Plot where the arrival time is
        # Mark detection
        ax.axvline(x = arrival, color='red',label='Rel. Arrival')
        ax.legend(loc='upper left')

    # Make the plot pretty
    ax.set_xlim([min(tr_times),max(tr_times)])
    ax.set_ylabel('Velocity (m/s)')
    ax.set_xlabel('Time (s)')
    ax.set_title(f'{title} {test_filename}', fontweight='bold') 
    return fig, ax


def search_in_list(data: str, list_: List[str]):
    for i, value in enumerate(list_):
        if data in value:
            return i

def get_match_filename_training(filenames: List[str], asteroid_path: str, extension: str | None = None):
    path = os.path.join(BASE_PATH, asteroid_path)
    if extension is None:
        extension = "csv"
    result = [y for x in os.walk(path) for y in glob.glob(os.path.join(x[0], f'*.{extension}'))]
    result_filter = [r for r in result if "training" in r  and "data" in r]
    results_mapping = {}
    for filename in filenames:
        index = search_in_list(filename, result_filter)
        if index is not None:
            results_mapping[filename] = result_filter[index]
    return results_mapping

def get_list_of_data_training(asteroid_path: str, extension: str | None = None):
    path = os.path.join(BASE_PATH, asteroid_path)
    if extension is None:
        extension = "csv"
    result = [y for x in os.walk(path) for y in glob.glob(os.path.join(x[0], f'*.{extension}'))]
    result_filter = [r for r in result if "training" in r  and "catalogs" in r]
    data_df = pd.DataFrame(result_filter, columns=["path"])
    return data_df

def get_list_of_data_testing(asteroid_path: str, extension: str | None = None):
    path = os.path.join(BASE_PATH, asteroid_path)
    if extension is None:
        extension = "csv"
    result = [y for x in os.walk(path) for y in glob.glob(os.path.join(x[0], f'*.{extension}'))]
    result_filter = [r for r in result if "test" in r  and "data" in r]
    data_df = pd.DataFrame(result_filter, columns=["path"])
    return data_df

def apply_bandpass_filter(st, minfreq=0.5, maxfreq=1.0):
    # Going to create a separate trace for the filter data
    st_filt = st.copy()
    st_filt.filter('bandpass',freqmin=minfreq,freqmax=maxfreq)
    return st_filt


def apply_highpass_filter(st, freq=3, corners=4):
    # Going to create a separate trace for the filter data
    st_filt = st.copy()
    st_filt.filter('highpass',freq=freq,corners=corners)
    return st_filt

def apply_lst_sta_algo_and_plot_char_func(st_values, sta_len=120, lta_len=600):
    # Sampling frequency of our trace
    tr = st_values.traces[0].copy()
    df = tr.stats.sampling_rate
    tr_times = tr.times()
    tr_data = tr.data

    # Run Obspy's STA/LTA to obtain a characteristic function
    # This function basically calculates the ratio of amplitude between the short-term 
    # and long-term windows, moving consecutively in time across the data
    cft = classic_sta_lta(tr_data, int(sta_len * df), int(lta_len * df))

    # Plot characteristic function
    fig, ax = plt.subplots(1,1,figsize=(12,3))
    ax.plot(tr_times,cft)
    ax.set_xlim([min(tr_times),max(tr_times)])
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Characteristic function')

    return cft, fig, ax

def calculate_on_off_cft_and_plot(st_values, cft, thr_on=4, thr_off=1.5):
    # Play around with the on and off triggers, based on values in the characteristic function
    tr = st_values.traces[0].copy()
    df = tr.stats.sampling_rate
    tr_times = tr.times()
    tr_data = tr.data

    on_off = np.array(trigger_onset(cft, thr_on, thr_off))
    triggers_list = []
    # The first column contains the indices where the trigger is turned "on". 
    # The second column contains the indices where the trigger is turned "off".

    # Plot on and off triggers
    fig, ax = plt.subplots(1,1,figsize=(12,3))
    for i in np.arange(0,len(on_off)):
        triggers = on_off[i]
        ax.axvline(x = tr_times[triggers[0]], color='red', label='Trig. On')
        ax.axvline(x = tr_times[triggers[1]], color='purple', label='Trig. Off')
        triggers_list.append(triggers)

    # Plot seismogram
    ax.plot(tr_times,tr_data)
    ax.set_xlim([min(tr_times),max(tr_times)])
    ax.legend()
    return triggers_list, fig, ax

def plot_real_trigger_axvline(st_values, arrival_time, ax, fig):
    # This is how you get the data and the time, which is in seconds
    tr = st_values.traces[0].copy()
    tr_times = tr.times()
    tr_data = tr.data
    starttime = tr.stats.starttime.datetime
    arrival = (arrival_time - starttime).total_seconds()
    # Plot where the arrival time is
    # Mark detection
    ax.axvline(x = arrival, color='green',label='Real Arrival')
    ax.legend()
    return fig, ax

def calculate_arrival_time(st_values, arrival_time):
    # This is how you get the data and the time, which is in seconds
    tr = st_values.traces[0].copy()
    tr_times = tr.times()
    tr_data = tr.data
    starttime = tr.stats.starttime.datetime
    arrival = (arrival_time - starttime).total_seconds()
    return arrival

def calculate_predicted_arrival_time(st_values, triggers):
    # This is how you get the data and the time, which is in seconds
    tr = st_values.traces[0].copy()
    df = tr.stats.sampling_rate
    tr_times = tr.times()
    tr_data = tr.data
    triggers_ = triggers[0]
    try:
        return tr_times[triggers_[0]]
    except:
        return tr_times[triggers_]

def calculate_root_mean_square_error(expected, actual):
    if (isinstance(expected, float) and isinstance(actual, float)):
        return np.sqrt((expected - actual)**2)
    else:
        return np.sqrt((expected - actual) ** 2/len(expected))

def apply_hilbert_and_plot_char(st_values, file_name_to_analyze, arrival_time=None, plot_real=False):
    # Sampling frequency of our trace
    tr = st_values.traces[0].copy()
    df = tr.stats.sampling_rate
    tr_times = tr.times()
    tr_data = tr.data
    # Calcular el envolvente de la señal usando la transformada de Hilbert
    analytical_signal = hilbert(tr_data)
    amplitude_envelope = np.abs(analytical_signal)

    fig,ax = plt.subplots(1,1,figsize=(10,3))
    if plot_real and arrival_time is not None:
        starttime = tr.stats.starttime.datetime
        arrival = (arrival_time - starttime).total_seconds()
        # Plot where the arrival time is
        # Mark detection
        ax.axvline(x = arrival, color='red',label='Rel. Arrival')
        ax.legend(loc='upper left')

   # Graficar la envolvente de la señal (energía)
    ax.plot(tr_times, amplitude_envelope, color='green', label='Envolvente de Amplitud (Energía)')
    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Energía')
    ax.set_title(f'Energía en la Señal {file_name_to_analyze}')

    return amplitude_envelope, fig, ax

def apply_find_peaks_of_energy_amplitude_function(st_values, amplitude_envelope, min_distance=40000, percentile_value=99.5,
                                                  arrival_time=None, plot_real=False, file_name_to_analyze=""):
    # Sampling frequency of our trace
    tr = st_values.traces[0].copy()
    df = tr.stats.sampling_rate
    tr_times = tr.times()
    tr_data = tr.data
    
    # Calcular el envolvente de la señal usando la transformada de Hilbert
    threshold = np.percentile(amplitude_envelope, percentile_value)  # Cambia el percentil si es necesario
    peaks, properties = find_peaks(amplitude_envelope, height=threshold, distance=min_distance)

    fig,ax = plt.subplots(1,1,figsize=(10,3))
    if plot_real and arrival_time is not None:
        starttime = tr.stats.starttime.datetime
        arrival = (arrival_time - starttime).total_seconds()
        # Plot where the arrival time is
        # Mark detection
        ax.axvline(x = arrival, color='red',label='Rel. Arrival')
        ax.legend(loc='upper left')

    # Graficar resultados
    ax.plot(tr_times, amplitude_envelope, color='green', label='Energía')
    ax.scatter(tr_times[peaks], amplitude_envelope[peaks], color='red', label='Picos detectados')
    ax.axhline(y=threshold, color='orange', linestyle='--', label='Umbral de Energía')
    ax.set_title(f'Detected peaks {file_name_to_analyze.split("/")[-1]}')
    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Energía')
    ax.legend()

    # Agregar el número de sismos en la gráfica
    num_peaks = len(peaks)
    ax.text(x=0.0, y=-0.07, s=f'Number of peaks: {num_peaks}', 
             transform=fig.gca().transAxes, fontsize=12, color='blue', 
             verticalalignment='top')
    
    return peaks, fig, ax