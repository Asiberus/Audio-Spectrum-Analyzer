import collections
import colorsys
import sys

import numpy as np
import pyaudio
# import pyqtgraph as pg
# from pyqtgraph.Qt import QtGui, QtCore

import tkinter as tk
from microphone_recorder import MicrophoneRecorder


class AudioVisualizerUI(tk.Frame):
  def __init__(self, master=None):
    super().__init__(master)
    self.master = master
    self.pack()



    self.FORMAT = pyaudio.paInt16
    self.CHANNELS = 1
    self.RATE = 44100
    self.CHUNKSIZE = 1024
    self.N_FFT = 2048

    self.recorder = MicrophoneRecorder(sample_rate=self.RATE, chunksize=self.CHUNKSIZE)
    self.recorder.start()

    self.x = np.arange(0, 2 * self.CHUNKSIZE, 2)
    self.f = np.linspace(1, self.RATE / 2, self.CHUNKSIZE)

    self.previous_hue = None
    self.hue_offset = 0
    self.previous_spectrum = collections.deque(maxlen=10)

  def start(self):
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
      QtGui.QGuiApplication.instance().exec_()

  def update(self):
    frames = self.recorder.get_frames()
    if len(frames) == 0:
      data = np.zeros((self.recorder.chunksize,), dtype=np.int)
    else:
      data = frames[-1]

    self.set_waveform_data(data)

    if data.max() > 1:
      self.set_spectrum_data(data)

  def set_waveform_data(self, data):
    # self.waveform_plot.setData(x=self.x, y=data)
    pass

  def set_spectrum_data(self, data):
    spectrum = np.fft.fft(np.hanning(data.size) * data, n=self.N_FFT)

    # if len(self.previous_spectrum) == 10:
    #   for i in range(self.spectrum_smooth_slider.value()):
    #     spectrum = spectrum + (self.previous_spectrum[i] - spectrum) * (self.spectrum_smooth_offset_slider.value() / 10)

    # self.previous_spectrum.appendleft(spectrum)

    self.get_bark_split(spectrum)

    spectrum_magnitude = np.sqrt(np.real(spectrum) ** 2 + np.imag(spectrum) ** 2)
    spectrum_magnitude = spectrum_magnitude[:self.CHUNKSIZE] * 2 / (128 * self.CHUNKSIZE)

    # self.spectrum_plot.setData(x=self.f, y=spectrum_magnitude)

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

    # self.bark_spectrum_plot.setData(x=bark_scale, y=y)

  def set_color(self, data):
    blue = np.linalg.norm(data[:8]) * 0.8
    green = np.linalg.norm(data[8:16])
    red = np.linalg.norm(data[16:])

    sum = blue + green + red

    red_ratio = red / sum
    green_ratio = green / sum
    blue_ratio = blue / sum

    hue, saturation, value = colorsys.rgb_to_hsv(red_ratio, green_ratio, blue_ratio)

    if self.previous_hue is None:
      self.previous_hue = hue

    hue = hue + (self.previous_hue - hue) * (self.hue_smooth_slider.value() / 10)
    self.previous_hue = hue

    # if self.rainbow_mode_checkbox.isChecked():
      # hue = hue + (self.previous_hue - hue) * 0.5
      # self.hue_offset += 0.005
      # hue = (hue + self.hue_offset) % 1
      # print(hue)
    # print((self.slider.value() / 10))

    r = colorsys.hsv_to_rgb(hue, 1, 1)

    # self.label_rgb.setText('███')
    # self.label_rgb.setAttr('color', '%02x%02x%02x' % (int(r[0] * 255), int(r[1] * 255), int(r[2] * 255)))

  def animation(self):
    # timer = QtCore.QTimer()
    # timer.timeout.connect(self.update)
    # timer.start(10)

    self.start()


if __name__ == '__main__':
  root = tk.Tk()
  audio_app = AudioVisualizerUI(master=root)

  audio_app.master.title('Audio Visualizer')
  audio_app.master.maxsize(1000, 1000)
  audio_app.mainloop()
  # audio_app.animation()
