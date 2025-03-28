# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 15:43:47 2018

@author: tmazzoni
"""
import sys
import numpy as np
import os.path as path
import csv
from PyQt5 import QtCore, QtGui
import PyQt5.QtWidgets as QtW
from PyQt5.QtCore import Qt
import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class GoodTimeWindow(QtW.QMainWindow):
    
    def __init__(self, fileName):
        super().__init__()
        
        self.fileName = fileName

        self.setWindowTitle('goodTime_sequence')
        self._main = QtW.QWidget()
        self.setCentralWidget(self._main) 
        
        color = self._main.palette().color(QtGui.QPalette.Background)
        red, green, blue = color.red()/256, color.green()/256, color.blue()/256
        self.windowcolor = (red, green, blue)
        self.Desktop = QtW.QDesktopWidget().frameGeometry() # geometry of the Desktop

        self.pausestatus = True
        self.data_arrived = False
        self.data, self.x, self.dataplot, self.datatemp = [],[],[],[]
        self.dtStep = 50e-6
        
        # Thread inizialization
        self.goodTime_thread = QtCore.QThread()
        self.goodTime_worker = GoodTimeControl(self.fileName)
        self.goodTime_worker.moveToThread(self.goodTime_thread)
        self.goodTime_thread.started.connect(self.goodTime_worker.start)
        self.goodTime_thread.finished.connect(self.goodTime_worker.deleteLater)
        self.goodTime_thread.finished.connect(self.goodTime_thread.deleteLater)
        self.goodTime_worker.goodTimeData.connect(self.update_data)
        self.goodTime_thread.start()
        
        # Canvas
        figwidth, figheight = 9, 6
        self.fig = matplotlib.figure.Figure(figsize=(figwidth,figheight), facecolor=self.windowcolor)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.navi_toolbar = NavigationToolbar2QT(self.canvas, self)
        self.ax1 = self.fig.add_subplot(2,1,1)
        self.ax1.set_ylabel('Analog', fontsize=12)
        self.ax1.set_xlim(0, 1); self.ax1.set_ylim(-1, 1)
        self.ax1.tick_params(axis='both', which='major', labelsize=8)
        self.ax2 = self.fig.add_subplot(2,1,2,sharex=self.ax1) 
        self.ax2.set_ylabel('Digital', fontsize=12)
        self.ax2.set_ylim(0, 1) # shared x
        self.ax2.tick_params(axis='both', which='major', labelsize=8)
        self.ax2.set_yticklabels([])
        self.ax1.set_autoscalex_on(1); self.ax2.set_autoscalex_on(1)
        self.ax1.set_autoscaley_on(1); self.ax2.set_autoscaley_on(1)
        self.fig.tight_layout()
        self.canvas.resize(figwidth*self.fig.dpi, figheight*self.fig.dpi)
        self.canvas.setMinimumSize(figwidth*self.fig.dpi, figheight*self.fig.dpi)
        self.canvas.draw()

        # Widgets
        self.startbutton = QtW.QPushButton('Start', checkable=True)
#        self.startbutton.clicked.connect(self.start_SeqPlot)
        self.startbutton.toggled.connect(self.start_SeqPlot)
        self.startbutton.toggled.connect(self.goodTime_worker.setSeqPlotState)
        self.startbutton.setChecked(True)
#        self.tracelabel = QtW.QLabel('0 traces in memory', self)
#        self.tracelabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter) 
#        self.plottracelabel = QtW.QLabel('Plot # traces', self)
#        self.plottracelabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter) 
#        self.numtraceentry = QtW.QSpinBox(self); self.numtraceentry.setFixedWidth(60)
#        self.numtraceentry.setRange(1, 1e7); self.numtraceentry.setSingleStep(1)
#        self.numtraceentry.setValue(10)
        self.resetzoombutton = QtW.QPushButton('Reset Zoom')
        self.resetzoombutton.clicked.connect(self.reset_zoom)
        self.clearbutton = QtW.QPushButton('Clear Plots')
        self.clearbutton.clicked.connect(self.clear_plot)
        self.resetdatabutton = QtW.QPushButton('Update Data')
        self.resetdatabutton.clicked.connect(self.reset_data)
        self.updateCheckbox = QtW.QCheckBox("Auto update")
        self.updateCheckbox.setChecked(False)
#        self.savebutton = QtW.QPushButton('Save')
#        self.savebutton.clicked.connect(self.save)
        self.listDig = np.arange(32).tolist() + [32,33,34,35,36, 38, 45, 48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63]
        
#        self.chNames = np.genfromtxt('//LPTFPC18/SequencesGoodtime/temp/TACC2defs.sqi', \
#                            dtype='str', comments='//', delimiter = ' = ', skip_header=15, max_rows=79, usecols=(0,))
        self.chNames = np.genfromtxt('G:/Sequences/210917/sequences/TACC2defs.sqi', \
                            dtype='str', comments='//', delimiter = ' = ', skip_header=15, max_rows=79, usecols=(0,))
        
        list1 = [8,24,25,82,83]
        list2 = ['broken', 'broken', 'broken', 'unused','unused']
        for idx in range(5):
            self.chNames = np.insert(self.chNames,list1[idx],list2[idx])
        
        self.checkboxChs, self.checkedChs = [], []
        self.checkedDig = []
        for idx in range(84):
            self.checkboxChs.append(QtW.QCheckBox('Ch' + str(idx).zfill(2) + ':' + self.chNames[idx]))
            self.checkboxChs[idx].setChecked(False)
            self.checkboxChs[idx].clicked.connect(self.add_plot) # connect checkboxes click event

        # Layouts
        self.buttonLayout = QtW.QGridLayout()
        self.buttonLayout.addWidget(self.startbutton,0,0)
        self.buttonLayout.addWidget(self.resetzoombutton,0,1)
#        self.buttonLayout.addWidget(self.plottracelabel,0,1)
#        self.buttonLayout.addWidget(self.numtraceentry,1,1)
        self.buttonLayout.addWidget(self.clearbutton,0,2)
        self.buttonLayout.addWidget(self.resetdatabutton,0,3)
        self.buttonLayout.addWidget(self.updateCheckbox,0,4)
#        self.buttonLayout.addWidget(self.savebutton,0,3)
        self.checkLayout = QtW.QGridLayout()
        for idx in range(84):
            self.checkLayout.addWidget(self.checkboxChs[idx],idx//8,idx%8)

        self.vbl = QtW.QVBoxLayout(self._main)
        self.vbl.addWidget(self.navi_toolbar)
        self.vbl.addWidget(self.canvas)
        self.vbl.addLayout(self.buttonLayout)
        self.vbl.addLayout(self.checkLayout)
        
        self.setLayout(self.vbl) # compose grid layout
        self.show() # show main window
        fg = self.frameGeometry()  # geometry of the main window
        cp = QtW.QDesktopWidget().availableGeometry().center() # center point of screen
        fg.moveCenter(cp) # move rectangle's center point to screen's center point
        self.move(fg.topLeft()) # top left of rectangle becomes top left of window centering it


    def start_SeqPlot(self):
        if self.startbutton.isChecked(): 
            self.startbutton.setText('Stop')
            self.pausestatus = False
        else:
            self.startbutton.setText('Start')
            self.pausestatus = True
        
#    @QtCore.pyqtSlot(dict)
#    def camera_status(self, datacam):
#        if self.cameracheckbox.isChecked() and self.data_arrived==True and self.datatemp!=[]:
#            datacamtemp = []
#            for key in datacam.keys():
#                if key.find('param')==0 or (key.find('Nsum')==0 and len(key)<6):
#                    datacamtemp.append(datacam[key])
#            self.datacam.append(np.array(datacamtemp))
#            self.data.append(self.datatemp)
#            self.x.append(np.arange(len(self.datatemp)))
#            self.tracelabel.setText(str(len(self.data))+' traces in memory')
#            self.update_plot()
#            self.data_arrived = False
    
    @QtCore.pyqtSlot(object)
    def update_data(self, data):
        self.datatemp = data
        if self.pausestatus == False and self.updateCheckbox.isChecked() or self.data == []:
            self.data = data
            self.x = self.dtStep *np.arange(data[0].shape[0])
#            self.tracelabel.setText(str(len(self.data))+' traces in memory')
            self.update_plot()
        elif self.pausestatus == False and not self.updateCheckbox.isChecked():
            self.data_arrived = True

    def chselect(self, chn):
        ''' channel number start with 0
        0 -- 31 digital channels NI6259
        32 -- 63 bad analog channels NI6723
        64 -- 67 analog output of NI6259
        68 -- 75 analog NI6733
        76 -- 83 analog NI6733b
        '''
#        print('chselect')
        if chn >=0 and chn < 32: dataout = np.array(self.data[0][:,chn])
        elif chn < 64: 
            dataout = np.array(self.data[1][:,chn-32]) /4095

        elif chn < 68: dataout = np.array(self.data[2][:,chn-64]) /32767
        elif chn < 76: dataout = np.array(self.data[3][:,chn-68]) /32767
        elif chn < 84: dataout = np.array(self.data[4][:,chn-76]) /32767
        else: print('channel number error!'); return None
        return dataout
        
            
    def add_plot(self):
        boxtext = self.sender()
        i = int(boxtext.text()[2:4])
#        print('add_plot ch%.0f' %(i))
        if self.checkboxChs[i].isChecked():
            self.checkedChs.append(i)
            if i in self.listDig:
                self.checkedDig.append(i)
                newplot = self.ax2.plot(self.x, self.chselect(i) - 1.1*float(self.checkedDig.index(i)), '-') # shift digital lines according to the position in the list

            else:
                newplot = self.ax1.plot(self.x, self.chselect(i), '-')
            self.checkboxChs[i].setStyleSheet('color:'+ newplot[0].get_color() + ';')
            self.dataplot.append(newplot)
        else:
            self.checkboxChs[i].setStyleSheet('color:k')
            if i in self.checkedChs: 
                idx2remove = self.checkedChs.index(i)
                self.dataplot[idx2remove].pop(0).remove() # not remove list, but remove line
                del self.dataplot[idx2remove]
                self.checkedChs.remove(i)
            if i in self.listDig:
                old_checkedDig = self.checkedDig.copy() # save old list to know how much they were shifted
                self.checkedDig.remove(i)               # new list to determine how much they should be shifted
                for j, jj in enumerate(self.checkedChs): # to reposition the digital lines
                    if jj in self.checkedDig: 
                        dataOld = self.dataplot[j][0].get_ydata() # get data of the old line (to be shifted)
                        self.dataplot[j][0].set_ydata(dataOld + 1.1*float(old_checkedDig.index(jj) - self.checkedDig.index(jj)))
                
        print(self.checkedChs, self.checkedDig)
        self.ax1.relim(); self.ax2.relim()
        self.ax1.autoscale(axis='y');self.ax2.autoscale(axis='y')
        self.canvas.draw() 
        
    def update_plot(self): # update plot with new data.         
        for i in range(len(self.dataplot)):
            self.dataplot[i][0].set_xdata(self.x)
            idx = self.checkedChs[i]
            if idx in self.checkedDig:
                self.dataplot[i][0].set_ydata(self.chselect(self.checkedChs[i])-1.1*float(self.checkedDig.index(idx)))     
            else:
                self.dataplot[i][0].set_ydata(self.chselect(self.checkedChs[i]))
        self.ax1.relim(); self.ax2.relim()
#        self.ax1.autoscale();self.ax2.autoscale()        
        self.canvas.draw()
        
        
    def clear_plot(self):
        for i in range(len(self.dataplot)):
            self.dataplot[i].pop(0).remove()
            self.checkboxChs[self.checkedChs[i]].setChecked(False)
            self.checkboxChs[self.checkedChs[i]].setStyleSheet('color:k')
        self.dataplot = []
        self.checkedChs = []
        self.checkedDig = []
        self.ax1.set_xlim(self.x[0],self.x[-1])  
#        self.ax2.set_xlim(self.x[0],self.x[-1])  
#        self.ax1.set_ylim(0,1)
        self.canvas.draw()
        
    def reset_zoom(self):
        self.ax1.set_xlim(self.x[0],self.x[-1])  
#        self.ax2.set_xlim(self.x[0],self.x[-1])  
        self.ax1.autoscale(axis='y'); self.ax2.autoscale(axis='y')
        self.canvas.draw()
    
    def reset_data(self):
#        self.data, self.x, self.datatemp = [],[],[]
#        self.clear_plot()
#        self.tracelabel.setText('x traces in memory')
        if self.data_arrived:
            self.data = self.datatemp
            self.x = self.dtStep *np.arange(self.data[0].shape[0])
            
            self.data_arrived = False
        self.update_plot()
    
#    def save(self):
#        if self.data != []:
#            data2save = []
#            for i in range(len(self.data)):
#                if self.datacam[i] is not None:
#                    data2save.append(self.datacam[i].tolist() + self.data[i].tolist())
#                else:
#                    data2save.append(self.data[i].tolist())
#            fileToSave,_ = QtW.QFileDialog.getSaveFileName(self, 
#                        'Save counter data', 'C:\\', 'csv file (*.csv);;All files(*.*)')
#            with open(fileToSave, 'w', newline='') as file:
#                w = csv.writer(file, delimiter=',')
#                for roww in data2save:
#                    w.writerow(roww)
#        

    def closeEvent(self, event):
    # If window is closed
#        self.hide()
        self.goodTime_thread.quit(); self.goodTime_thread.wait()
#        np.seterr(**self.oldsett)  # reset numpy to default settings
        self.close()

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
            Ana6723 = np.fromfile('G:/data/temp/AnaBuffer1.bin', dtype=np.int16).reshape(-1,32)
            Ana6259 = np.fromfile('G:/data/temp/AnaBuffer2.bin', dtype=np.int16).reshape(-1,4)
            Ana6733 = np.fromfile('G:/data/temp/AnaBuffer3.bin', dtype=np.int16).reshape(-1,8)
            Ana6733b = np.fromfile('G:/data/temp/AnaBuffer4.bin', dtype=np.int16).reshape(-1,8)
            Dig6259 = np.fromfile('G:/data/temp/DigBuffer.bin', dtype=np.uint8).reshape(-1,1)
            Dig6259 = np.flip(np.unpackbits(Dig6259, axis=1), axis=1).reshape(-1,32)
            dataout = [Dig6259, Ana6723, Ana6259, Ana6733, Ana6733b]
            self.lastmodtime = self.lastmodtimeNOW
            self.goodTimeData.emit(dataout)
            self.startcount += 1
            print('loaded_data')

if __name__ == '__main__':
    app = QtCore.QCoreApplication.instance() # checks if QApplication already exists 
    if app is None: # create QApplication if it doesnt exist 
        app = QtW.QApplication(sys.argv)
    goodTimeSeq = GoodTimeWindow('G:/data/temp/AnaBuffer1.bin')
    goodTimeSeq.activateWindow()
    app.aboutToQuit.connect(app.deleteLater)
    app.exec_()            
