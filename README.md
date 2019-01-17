# PyInfluxTFA: A simple test of querying data from InfluxDB and performing Time-Frequency Analysis using Python

## How to Run

```
> python3 main.py
```

## Configurable Parameters

* `MODE`: TFA mode, can be `stft` or `hht`
* `INPUT_AUDIO_NAME`: Input wav file name in `data/`
* `SAMPLE_RATIO`: Ratio of sample with respect to original sampling rate
* `COMPUTE_PERIOD`: The time duration each STFT/HHT performs on, which is also the period from one InfluxDB query to another.