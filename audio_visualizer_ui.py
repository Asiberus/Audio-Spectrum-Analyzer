import collections
import colorsys
import sys

import numpy as np
import pyaudio
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

from microphone_recorder import MicrophoneRecorder


class AudioVisualizerUI(object):
  def __init__(self):
    self.FORMAT = pyaudio.paInt16
    self.CHANNELS = 1
    self.RATE = 44100
    self.CHUNKSIZE = 1024
    self.N_FFT = 2048

    pg.setConfigOptions(antialias=True)
    self.traces = dict()
    self.app = QtGui.QApplication(sys.argv)
    self.win = pg.GraphicsWindow()
    self.win.resize(1000, 1000)

    wf_xlabels = [(0, '0'), (2048, '2048'), (4096, '4096')]
    wf_xaxis = pg.AxisItem(orientation='bottom')
    wf_xaxis.setTicks([wf_xlabels])

    sp_xlabels = [
      (np.log10(920), '920'), (np.log10(3150), '3150'), (np.log10(15500), '15500')
    ]
    sp_xaxis = pg.AxisItem(orientation='bottom')
    sp_xaxis.setTicks([sp_xlabels])

    bark_xlabels = [
      (920, '920'), (3150, '3150')
    ]
    bark_xaxis = pg.AxisItem(orientation='bottom')
    bark_xaxis.setTicks([bark_xlabels])

    # self.waveform = self.win.addPlot(
    #   title='Waveform', row=1, col=1, axisItems={'bottom': wf_xaxis}
    # )
    # self.waveform.showGrid(True, True)
    # self.waveform.setYRange(-1000, 1000, padding=0)
    # self.waveform.setXRange(0, 2 * self.CHUNKSIZE, padding=0.005)
    # self.waveform.setLabel('left', "Microphone signal", units='A.U.')
    # self.waveform.setLabel('bottom', "Time", units='s')

    # self.waveform_plot = self.waveform.plot(pen='c', width=3)

    self.spectrum = self.win.addPlot(
      title='SPECTRUM', row=2, col=1,
      axisItems={'bottom': sp_xaxis},
    )
    self.spectrum.showGrid(True, True)
    self.spectrum.enableAutoRange('xy', False)
    self.spectrum.setLogMode(x=True, y=True)
    self.spectrum.setYRange(-5, 1, padding=0)
    self.spectrum.setXRange(np.log10(20), np.log10(20000), padding=0.005)
    self.spectrum.setLabel('left', "Amplitude", units='A.U.')
    self.spectrum.setLabel('bottom', "Frequency", units='Hz')

    self.spectrum_plot = self.spectrum.plot(pen='y', width=3)

    self.bark_spectrum = self.win.addPlot(title='Bark Spectrum', row=1, col=1, axisItems={'bottom': bark_xaxis})
    self.bark_spectrum.showGrid(True, True)
    self.bark_spectrum.enableAutoRange('xy', False)
    self.bark_spectrum.setYRange(0, 2, padding=0)
    self.bark_spectrum.setXRange(0, 20000, padding=0.005)
    self.bark_spectrum.setLabel('left', "Amplitude", units='A.U.')
    self.bark_spectrum.setLabel('bottom', "Frequency", units='Hz')

    self.bark_spectrum_plot = self.bark_spectrum.plot(pen='c', width=3, stepMode=True, fillOutline=True)

    control_layout = self.win.addLayout(row=1, col=2)

    self.spectrum_smooth_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
    self.spectrum_smooth_slider.setMinimum(0)
    self.spectrum_smooth_slider.setMaximum(10)

    proxy = QtGui.QGraphicsProxyWidget()
    proxy.setWidget(self.spectrum_smooth_slider)
    control_layout.addItem(proxy, row=1, col=1)

    self.spectrum_smooth_offset_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
    self.spectrum_smooth_offset_slider.setMinimum(0)
    self.spectrum_smooth_offset_slider.setMaximum(5)

    proxy2 = QtGui.QGraphicsProxyWidget()
    proxy2.setWidget(self.spectrum_smooth_offset_slider)
    control_layout.addItem(proxy2, row=2, col=1)

    self.rainbow_mode_checkbox = QtGui.QCheckBox('Rainbow Mode')
    proxy3 = QtGui.QGraphicsProxyWidget()
    proxy3.setWidget(self.rainbow_mode_checkbox)
    control_layout.addItem(proxy3, row=3, col=1)

    self.hue_smooth_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
    self.hue_smooth_slider.setMinimum(0)
    self.hue_smooth_slider.setMaximum(10)

    proxy4 = QtGui.QGraphicsProxyWidget()
    proxy4.setWidget(self.hue_smooth_slider)
    control_layout.addItem(proxy4, row=4, col=1)

    self.control_label = pg.LabelItem()
    control_layout.addItem(self.control_label, row=5, col=1)

    display_layout = self.win.addLayout(row=2, col=2)
    v = display_layout.getViewBox()
    print(v)
    # v.setBackgroundColor((100, 50, 0))

    self.label_rgb = pg.LabelItem('███', size='100pt', angle=90)

    display_layout.addItem(self.label_rgb, row=1, col=1)

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

    self.control_label.setText(
      'Nb of previous spectrum : {0}<br>Spectrum smoothness : {1}<br>Hue color smoothness : {2}'.format(
        self.spectrum_smooth_slider.value(), self.spectrum_smooth_offset_slider.value() / 10,
                                             self.hue_smooth_slider.value() / 10))

  def set_waveform_data(self, data):
    # self.waveform_plot.setData(x=self.x, y=data)
    pass

  def set_spectrum_data(self, data):
    spectrum = np.fft.fft(np.hanning(data.size) * data, n=self.N_FFT)

    if len(self.previous_spectrum) == 10:
      for i in range(self.spectrum_smooth_slider.value()):
        spectrum = spectrum + (self.previous_spectrum[i] - spectrum) * (self.spectrum_smooth_offset_slider.value() / 10)

    self.previous_spectrum.appendleft(spectrum)

    self.get_bark_split(spectrum)

    spectrum_magnitude = np.sqrt(np.real(spectrum) ** 2 + np.imag(spectrum) ** 2)
    spectrum_magnitude = spectrum_magnitude[:self.CHUNKSIZE] * 2 / (128 * self.CHUNKSIZE)

    self.spectrum_plot.setData(x=self.f, y=spectrum_magnitude)

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

    self.bark_spectrum_plot.setData(x=bark_scale, y=y)

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

    if self.rainbow_mode_checkbox.isChecked():
      # hue = hue + (self.previous_hue - hue) * 0.5
      self.hue_offset += 0.005
      hue = (hue + self.hue_offset) % 1
      print(hue)
    # print((self.slider.value() / 10))

    r = colorsys.hsv_to_rgb(hue, 1, 1)

    self.label_rgb.setText('███')
    self.label_rgb.setAttr('color', '%02x%02x%02x' % (int(r[0] * 255), int(r[1] * 255), int(r[2] * 255)))

  def animation(self):
    timer = QtCore.QTimer()
    timer.timeout.connect(self.update)
    timer.start(10)

    self.start()


if __name__ == '__main__':
  audio_app = AudioVisualizerUI()
  audio_app.animation()
