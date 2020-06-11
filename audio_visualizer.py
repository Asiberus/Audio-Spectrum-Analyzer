from threading import *
import collections
import colorsys

import numpy as np
import pyaudio

from microphone_recorder import MicrophoneRecorder


class AudioVisualizer(Thread):
  def __init__(self, event):
    Thread.__init__(self)
    self.stopped = event

    self.FORMAT = pyaudio.paInt16
    self.CHANNELS = 1
    self.RATE = 44100
    self.CHUNKSIZE = 1024
    self.N_FFT = 2048

    self.previous_hue = None
    self.hue_offset = 0
    self.previous_spectrum = collections.deque(maxlen=10)

    self.recorder = MicrophoneRecorder(sample_rate=self.RATE, chunksize=self.CHUNKSIZE)
    self.recorder.start()


  def run(self):
    while not self.stopped.wait(0.05):
      self.update()

  def update(self):
    frames = self.recorder.get_frames()
    if len(frames) == 0:
      data = np.zeros((self.recorder.chunksize,), dtype=np.int)
    else:
      data = frames[-1]

    if data.max() > 1:
      self.get_spectrum_data(data)

  def get_spectrum_data(self, data):
    spectrum = np.fft.fft(np.hanning(data.size) * data, n=self.N_FFT)

    self.get_bark_split(spectrum)

    # spectrum_magnitude = np.sqrt(np.real(spectrum) ** 2 + np.imag(spectrum) ** 2)
    # spectrum_magnitude = spectrum_magnitude[:self.CHUNKSIZE] * 2 / (128 * self.CHUNKSIZE)

  def get_bark_split(self, data):
    bark_scale = [0, 100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480, 1720, 2000,
                  2320, 2700, 3150, 3700, 4400, 5300, 6400, 7700, 9500, 12000, 15500]

    bark_scale_vector = [
      {'freq': 100, 'data': [], 'value': 0},
      {'freq': 200, 'data': [], 'value': 0},
      {'freq': 300, 'data': [], 'value': 0},
      {'freq': 400, 'data': [], 'value': 0},
      {'freq': 510, 'data': [], 'value': 0},
      {'freq': 630, 'data': [], 'value': 0},
      {'freq': 770, 'data': [], 'value': 0},
      {'freq': 920, 'data': [], 'value': 0},
      {'freq': 1080, 'data': [], 'value': 0},
      {'freq': 1270, 'data': [], 'value': 0},
      {'freq': 1480, 'data': [], 'value': 0},
      {'freq': 1720, 'data': [], 'value': 0},
      {'freq': 2000, 'data': [], 'value': 0},
      {'freq': 2320, 'data': [], 'value': 0},
      {'freq': 2700, 'data': [], 'value': 0},
      {'freq': 3150, 'data': [], 'value': 0},
      {'freq': 3700, 'data': [], 'value': 0},
      {'freq': 4400, 'data': [], 'value': 0},
      {'freq': 5300, 'data': [], 'value': 0},
      {'freq': 6400, 'data': [], 'value': 0},
      {'freq': 7700, 'data': [], 'value': 0},
      {'freq': 9500, 'data': [], 'value': 0},
      {'freq': 12000, 'data': [], 'value': 0},
      {'freq': 15500, 'data': [], 'value': 0},
    ]

    step = self.RATE // self.N_FFT

    for i in range(self.CHUNKSIZE):
      freq = i * step
      value = data[i]

      for bark in bark_scale_vector[::-1]:
        if freq >= bark['freq']:
          bark['data'].append(value)
          break

    y = []
    for bark in bark_scale_vector:
      magnitude = np.sqrt(np.real(bark['data']) ** 2 + np.imag(bark['data']) ** 2)
      d = np.linalg.norm(magnitude)
      bark['value'] = int(d)

      y.append(bark['value'])

    y = np.array(y)
    y = (y - y.min()) / (y.max() - y.min())

    self.set_color(y)

  def set_color(self, data):
    blue = np.linalg.norm(data[:8]) * 0.8
    green = np.linalg.norm(data[8:16])
    red = np.linalg.norm(data[16:])

    sum = blue + green + red

    red_ratio = red / sum
    green_ratio = green / sum
    blue_ratio = blue / sum

    hue, saturation, value = colorsys.rgb_to_hsv(red_ratio, green_ratio, blue_ratio)
    r = colorsys.hsv_to_rgb(hue, 1, 1)

    print(hue)



stopFlag = Event()
thread = AudioVisualizer(stopFlag)
thread.start()