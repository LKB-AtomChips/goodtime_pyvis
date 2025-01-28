# %%
import numpy as np
import os
import matplotlib.pyplot as plt
# %%
# Commondef reading & formatting
commondef = "_goodtime_commondef/241128_SAROC_Commondef.sqi"

class Dummy():
    pass

self = Dummy

self.Nchannels = 106

def formattext(label: str)->str:
    """Formats a label by removing tabs, white spaces and ;"""
    return label.replace('\t', "").replace(";", "").replace(" ", "")

def formatlist(inputlist: np.ndarray)->np.ndarray:
    """Returns a formatted array of channel names.
    Input:
    inputlist: ndarray from GoodTime commondef (raw)
    Output:
    res: ndarray of channel labels"""
    res = np.full(self.Nchannels,"Inactive", dtype=object)
    for label in inputlist:
        label = formattext(label)
        split = label.split("=")
        if len(split) > 1:
            chname, chnumber = split[0], int(split[1])
            print(chname)
            res[chnumber] = chname
    return res

def getlabels(commondef_fname):
    listed_names = np.genfromtxt(commondef_fname, dtype='str', comments='//', delimiter = '\n', skip_header=15, max_rows=106 + 10, usecols=(0,))
    return formatlist(listed_names)

getlabels(commondef)
# %%

# %%
# Making sense of file formats from GT

class Test():
    def __init__(self):
        # self.fileName = "//MOUFFETARD/goodTime_exchange"
        self.fileName = "D:/PythonProjects/goodTime_pyvis/_sampleGTfiles"
        Device1 = np.fromfile(self.fileName + '/DigBuffer1.bin', dtype=np.uint8).reshape(-1,1)
        self.Device1 = np.flip(np.unpackbits(Device1, axis=1), axis=1).reshape(-1,32)
        Device5dig = np.fromfile(self.fileName + '/DigBuffer2.bin', dtype=np.uint8).reshape(-1,1)
        self.Device5dig = np.flip(np.unpackbits(Device5dig, axis=1), axis=1).reshape(-1,32)
        

test = Test()

test.Device5dig

test.Device1

# %%
np.shape(test.Device5dig)
# %%
# Listening action
import os.path as path
from PyQt5 import QtCore, QtGui
import PyQt5.QtWidgets as QtW


class GoodTimeControl(QtCore.QObject):
    goodTimeData = QtCore.pyqtSignal(object)

    def __init__(self, fileName):
        super().__init__()
        self.fileName = fileName
        self.lastmodtime = path.getmtime(self.fileName)
        self.active = False
        self.timer = QtCore.QTimer(self, interval=50)
        self.timer.timeout.connect(self.acquire)
        self.startcount = 0
        
    @QtCore.pyqtSlot()
    def start(self):
        self.timer.start()
        
    @QtCore.pyqtSlot(bool)
    def setSeqPlotState(self, state):
        self.active = state
        
    @QtCore.pyqtSlot()
    def acquire(self):
        """ this is the method running indefinitly in the associated thread """
        if self.active:
            self.get_data()
            
    def get_data(self):
        self.lastmodtimeNOW = path.getmtime(self.fileName)
        if self.startcount == 0 or (self.lastmodtimeNOW - self.lastmodtime != 0):
            
            Device2 = np.fromfile(self.fileName + '/AnaBuffer1.bin', dtype=np.int16).reshape(-1,8)
            Device3 = np.fromfile(self.fileName + '/AnaBuffer2.bin', dtype=np.int16).reshape(-1,32)
            Device5ana = np.fromfile(self.fileName + '/AnaBuffer3.bin', dtype=np.int16).reshape(-1,4)
            Device1 = np.fromfile(self.fileName + '/DigBuffer1.bin', dtype=np.uint8).reshape(-1,1)
            Device1 = np.flip(np.unpackbits(Device1, axis=1), axis=1).reshape(-1,32)
            Device5dig = np.fromfile(self.fileName + '/DigBuffer2.bin', dtype=np.uint8).reshape(-1,1)
            Device5dig = np.flip(np.unpackbits(Device5dig, axis=1), axis=1).reshape(-1,32)
            dataout = [Device1, Device2, Device3, Device5ana, Device5dig]
            
            self.lastmodtime = self.lastmodtimeNOW
            self.goodTimeData.emit(dataout)
            self.startcount += 1
            print('loaded_data')


class Test():
    def __init__(self):
        self.goodTime_thread = QtCore.QThread()
        self.goodTime_worker = GoodTimeControl(self.fileName)
        self.goodTime_worker.moveToThread(self.goodTime_thread)
        self.goodTime_thread.started.connect(self.goodTime_worker.start)
        self.goodTime_thread.finished.connect(self.goodTime_worker.deleteLater)
        self.goodTime_worker.goodTimeData.connect(self.update_data)
        self.goodTime_thread.start()

gtc = GoodTimeControl("//MOUFFETARD/goodTime_exchange")
timer = QtCore.QTimer.singleShot(1000, gtc.deleteLater)

# %%

import matplotlib.colors
self = Test()
self.Nchannels = 107
colortable = [matplotlib.colors.to_hex( plt.cm.jet(k/self.Nchannels)  )  for k in range(self.Nchannels)]
# %%
import time, datetime
# %%
