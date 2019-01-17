from scipy import signal
import numpy as np

def stft(data, fs):
  f, t, Zxx = signal.stft(data, fs, nperseg=1000)
  return t, f, np.abs(Zxx)

def hht(data, fs):
  t = np.arange(data.shape[0]) / fs
  analytic_signal = signal.hilbert(data)
  amplitude_envelope = np.abs(analytic_signal)
  instantaneous_phase = np.unwrap(np.angle(analytic_signal))
  instantaneous_frequency = (np.diff(instantaneous_phase) / (2.0*np.pi) * fs)

  return t, data, amplitude_envelope, instantaneous_frequency