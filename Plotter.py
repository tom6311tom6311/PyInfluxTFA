from scipy import signal
import matplotlib.pyplot as plt
import numpy as np

def plot_stft(t, f, mag, params):
  plt.pcolormesh(t, f, mag, vmin=0, vmax=2*np.sqrt(2))
  params_txt = [f"{k}={params[k]}" for k in params]
  plt.title(f"STFT Magnitude ({', '.join(params_txt)})")
  plt.ylabel('Frequency [Hz]')
  plt.xlabel('Time [sec]')

  plt.tight_layout()
  plt.show()

def plot_hht(t, data, amplitude_envelope, instantaneous_frequency, params):
  fig = plt.figure()
  params_txt = [f"{k}={params[k]}" for k in params]
  ax0 = fig.add_subplot(211)
  ax0.plot(t, data, label='signal')
  ax0.plot(t, amplitude_envelope, label='envelope')
  ax0.set_xlabel('Time [sec]')
  ax0.legend()

  ax1 = fig.add_subplot(212)
  ax1.plot(t, instantaneous_frequency)
  ax1.set_xlabel('Time [sec]')
  plt.ylabel('Instantaneous Frequency [Hz]')
  plt.ylim((0,80))

  plt.title(f"HHT Result ({', '.join(params_txt)})")
  plt.tight_layout()
  plt.show()