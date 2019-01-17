from scipy.io import wavfile
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
from scipy import signal
import numpy as np
from Plotter import plot_stft, plot_hht
from Transformer import stft, hht

DATA_DIR_PATH = 'data'
AUDIO_SUFFIX = 'wav'
STFT_DB_NAME = 'stft'
HHT_DB_NAME = 'hht'
HHT_SIGNAL_NAME = 'chirp'

# Configurable Parameters
MODE = 'hht'
INPUT_AUDIO_NAME = 'piano1'
SAMPLE_RATIO = 1
COMPUTE_PERIOD = 1


if MODE == 'stft':
  # read audio
  fs, data = wavfile.read(f"{DATA_DIR_PATH}/{INPUT_AUDIO_NAME}.{AUDIO_SUFFIX}")
  # prepare data to be inserted
  start_time = datetime.utcnow()
  curr_time = start_time
  time_delta = timedelta(seconds=1/fs*SAMPLE_RATIO)
  data_points = []
  for pt in data[::SAMPLE_RATIO]:
    data_points.append({
      "measurement": INPUT_AUDIO_NAME,
      "time": curr_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
      "fields": {
        "left_channel": pt[0],
        "right_channel": pt[1]
      }
    })
    curr_time += time_delta

  # connect to InfluxDB and insert data
  client = InfluxDBClient()
  client.drop_database(STFT_DB_NAME)
  client.create_database(STFT_DB_NAME)
  client.switch_database(STFT_DB_NAME)
  # client.drop_measurement(INPUT_AUDIO_NAME)
  client.write_points(data_points)

  print("All data written to InfluxDB.")

  t_overall = []
  f_accum = []
  mag_accum = []
  for i in range(int(len(data_points) / (fs/SAMPLE_RATIO*COMPUTE_PERIOD)) - 1):
    print("Querying from DB...")
    print(f"SELECT * FROM {INPUT_AUDIO_NAME} WHERE time < '{(start_time + timedelta(seconds=i*COMPUTE_PERIOD+1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}' AND time >= '{(start_time + timedelta(seconds=i*COMPUTE_PERIOD)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}';")
    rs = client.query(f"SELECT * FROM {INPUT_AUDIO_NAME} WHERE time < '{(start_time + timedelta(seconds=i*COMPUTE_PERIOD+1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}' AND time >= '{(start_time + timedelta(seconds=i*COMPUTE_PERIOD)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}';")
    points = list(rs.get_points(measurement=INPUT_AUDIO_NAME))
    data_seg = [pt['left_channel'] for pt in points]
    t, f, mag = stft(data_seg, fs//SAMPLE_RATIO)
    if f_accum == []:
      t_overall = t
      f_accum = f
      mag_accum = mag
    else:
      if mag_accum.shape[1] == mag.shape[1]:
        f_accum = np.concatenate((f_accum, f), axis=0)
        mag_accum = np.concatenate((mag_accum, mag), axis=0)
      else:
        # print(mag_accum.shape, mag.shape)
        break
  # print(t_overall.shape, f_accum.shape, mag_accum.shape)
  plot_stft(t_overall, f_accum, mag_accum, {
    'fs': fs/SAMPLE_RATIO,
    'period': str(COMPUTE_PERIOD) + ' s'
  })
else:
  # MODE == 'hht'
  duration = 1.0
  fs = 400
  samples = int(fs*duration)
  t = np.arange(samples) / fs
  data = signal.chirp(t, 50.0, t[-1], 1.0)
  data *= (1.0 + 0.5 * np.sin(2.0*np.pi*3.0*t))

  # prepare data to be inserted
  start_time = datetime.utcnow()
  curr_time = start_time
  time_delta = timedelta(seconds=1/fs*SAMPLE_RATIO)
  data_points = []
  for val in data[::SAMPLE_RATIO]:
    data_points.append({
      "measurement": HHT_SIGNAL_NAME,
      "time": curr_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
      "fields": {
        "val": val
      }
    })
    curr_time += time_delta

  # connect to InfluxDB and insert data
  client = InfluxDBClient()
  client.drop_database(HHT_DB_NAME)
  client.create_database(HHT_DB_NAME)
  client.switch_database(HHT_DB_NAME)
  # client.drop_measurement(HHT_SIGNAL_NAME)
  client.write_points(data_points)

  print("All data written to InfluxDB.")

  data_accum = []
  env_accum = []
  instf_accum = []
  for i in range(int(len(data_points) / (fs/SAMPLE_RATIO*COMPUTE_PERIOD))):
    print("Querying from DB...")
    print(f"SELECT * FROM {HHT_SIGNAL_NAME} WHERE time < '{(start_time + timedelta(seconds=i*COMPUTE_PERIOD+1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}' AND time >= '{(start_time + timedelta(seconds=i*COMPUTE_PERIOD)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}';")
    rs = client.query(f"SELECT * FROM {HHT_SIGNAL_NAME} WHERE time < '{(start_time + timedelta(seconds=i*COMPUTE_PERIOD+1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}' AND time >= '{(start_time + timedelta(seconds=i*COMPUTE_PERIOD)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}';")
    points = list(rs.get_points(measurement=HHT_SIGNAL_NAME))
    data_seg = np.array([pt['val'] for pt in points])
    _t, data, env, instf = hht(data_seg, fs//SAMPLE_RATIO)
    if len(data) != len(env) or len(env) != len(instf):
      l = max(len(data), len(env), len(instf))
      if len(data) != l:
        data = np.pad(data, (0,l-len(data)), 'edge')
      if len(env) != l:
        env = np.pad(env, (0,l-len(env)), 'edge')
      if len(instf) != l:
        instf = np.pad(instf, (0,l-len(instf)), 'edge')
    if data_accum == []:
      data_accum = data
      env_accum = env
      instf_accum = instf
    else:
      data_accum = np.concatenate((data_accum, data), axis=0)
      env_accum = np.concatenate((env_accum, env), axis=0)
      instf_accum = np.concatenate((instf_accum, instf), axis=0)

  # print(t.shape, data_accum.shape, env_accum.shape, instf_accum.shape)
  plot_hht(np.arange(len(data_accum))/(fs//SAMPLE_RATIO), data_accum, env_accum, instf_accum, {
    'fs': fs/SAMPLE_RATIO,
    'period': str(COMPUTE_PERIOD) + ' s'
  })

# # show meta
# print("\nMeta:")
# print(f"  Frames/Sec:{fs}")
# print(f"  Data Shape:{data.shape}\n")


# if MODE == 'stft':
#   plot_stft(data[:,0], fs//SAMPLE_RATIO)
# else:
#   # MODE == 'hht'
#   plot_hht(data, fs//SAMPLE_RATIO)
