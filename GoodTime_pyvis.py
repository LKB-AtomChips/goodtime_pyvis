# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 15:43:47 2018
@author: tmazzoni

Adapted for LKB ENS Rb experiment by Clement Raphin starting from 29 nov 2024
"""
import sys
import numpy as np
import os.path as path
import csv
from PyQt5 import QtCore, QtGui
import PyQt5.QtWidgets as QtW
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
import json
import logging
from datetime import datetime

class GoodTimeWindow(QtW.QMainWindow):
    
    def __init__(self, fileName, commondef = "_goodtime_commondef/241128_SAROC_Commondef.sqi"):
        super().__init__()
        
        self.fileName = fileName
        self.config_filename = "config.json"
        self._loadSettings()
        # GoodTime exp parameters (SAROC):
        self.Nchannels = 107

        self.setWindowTitle('goodTime_sequence')
        self._main = QtW.QWidget()
        self.setCentralWidget(self._main) 
        
        color = self._main.palette().color(QtGui.QPalette.Background)
        red, green, blue = color.red()/256, color.green()/256, color.blue()/256
        self.windowcolor = (red, green, blue)
        self.Desktop = QtW.QDesktopWidget().frameGeometry() # geometry of the Desktop

        self.pausestatus = True
        self.data_arrived = False
        self.data, self.dataplot, self.datatemp = [],[],[]
        self.dtStep = 25e-3 # timestep in ms
        
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
        self.fig = plt.Figure(figsize=(figwidth,figheight), facecolor=self.windowcolor)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.navi_toolbar = NavigationToolbar2QT(self.canvas, self)
        self.ax1 = self.fig.add_subplot(2,1,1)
        self.ax1.set_ylabel('Analog', fontsize=12)
        self.ax1.set_xlim(0, 1); self.ax1.set_ylim(-1, 1)
        self.ax1.tick_params(axis='both', which='major', labelsize=8)
        self.ax2 = self.fig.add_subplot(2,1,2,sharex=self.ax1) 
        self.ax2.set_ylabel('Digital', fontsize=12)
        self.ax2.set_xlabel("t (ms)")
        self.ax2.set_ylim(0, 1) # shared x
        self.ax2.tick_params(axis='both', which='major', labelsize=8)
        self.ax2.set_yticklabels([])
        self.ax1.set_autoscalex_on(1); self.ax2.set_autoscalex_on(1)
        self.ax1.set_autoscaley_on(1); self.ax2.set_autoscaley_on(1)
        self.ax1.grid()
        self.ax2.grid()
        self.reset_data
        self.fig.tight_layout()
        self.canvas.resize(figwidth*self.fig.dpi, figheight*self.fig.dpi)
        # self.canvas.setMinimumSize(figwidth*self.fig.dpi, figheight*self.fig.dpi) # this doesnt work right now
        self.canvas.draw()

        # Widgets
        self.startbutton = QtW.QPushButton('Start', checkable=True)
        self.startbutton.clicked.connect(self.start_SeqPlot)
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
        
        # Time offset button
        self.timeoffsetLabel = QtW.QLabel("Time offset (ms):")
        self.timeoffsetSpinbox = QtW.QDoubleSpinBox()
        self.timeoffsetSpinbox.setRange(0, 10e3)
        self.timeoffsetSpinbox.setDecimals(2)
        self.timeoffsetSpinbox.setValue(self.timeoffset)
        
        self.timeoffsetSpinbox.valueChanged.connect(self.change_timeoffset)
        
        
        ## Generating list of digital channel numbers
        self.listDig = [k for k in range(self.Nchannels) if self.isDigital(k)]
        
        ## Generating channel names
        self.chNames = self.getlabels(commondef)
        
        ##############
        #### ESTHETICS
        
        self.linewidth = 3
        
        # Color table
        def color(channel):
            """ Generates a color for each channel """
            return matplotlib.colors.to_hex( plt.cm.rainbow(np.random.randint(0 + 16, 256 - 16)/256. ))
            
        self.colortable = [color(k) for k in range(self.Nchannels)]
                
        # list1 = [8,24,25,82,83]
        # list2 = ['broken', 'broken', 'broken', 'unused','unused']
        # for idx in range(5):
        #     self.chNames = np.insert(self.chNames,list1[idx],list2[idx])
        
        # Layouts
        self.buttonLayout = QtW.QGridLayout()
        self.buttonLayout.addWidget(self.startbutton,0,0)
        self.buttonLayout.addWidget(self.resetzoombutton,0,1)
#        self.buttonLayout.addWidget(self.plottracelabel,0,1)
#        self.buttonLayout.addWidget(self.numtraceentry,1,1)
        self.buttonLayout.addWidget(self.clearbutton,0,2)
        self.buttonLayout.addWidget(self.resetdatabutton,0,3)
        self.buttonLayout.addWidget(self.updateCheckbox,0,4)
        
        self.buttonLayout.addWidget(self.timeoffsetLabel,0,5)
        self.buttonLayout.addWidget(self.timeoffsetSpinbox,0,6)
#        self.buttonLayout.addWidget(self.savebutton,0,3)
        self.anaChLabel = QtW.QLabel("Analog channels")
        self.digChLabel = QtW.QLabel("Digital channels")
        self.checkLayoutAna = QtW.QGridLayout()
        self.checkLayoutDig = QtW.QGridLayout()
        self.checkLayoutAna.addWidget(self.anaChLabel, 0, 0)
        self.checkLayoutDig.addWidget(self.digChLabel, 0, 0)
        indexAna, indexDig = 0, 0
        
        self.checkboxChs = []
        
        #Initializing checkboxes
        for idx in range(self.Nchannels):
            self.checkboxChs.append(QtW.QCheckBox('Ch' + str(idx).zfill(3) + ':' + self.chNames[idx]))
            if idx in self.checkedChs:
                self.checkboxChs[idx].setChecked(True)
                self.init_plot(idx)
                
            if  self.chNames[idx] != "Inactive":
                if self.isDigital(idx):
                    self.checkLayoutDig.addWidget(self.checkboxChs[idx],indexDig//8 + 1,indexDig%8)
                    indexDig += 1
                else:
                    self.checkLayoutAna.addWidget(self.checkboxChs[idx],indexAna//8 + 1,indexAna%8)
                    indexAna += 1
            self.checkboxChs[idx].clicked.connect(self.add_plot) # connect checkboxes click event

        self.vbl = QtW.QVBoxLayout(self._main)
        self.vbl.addWidget(self.navi_toolbar)
        self.vbl.addWidget(self.canvas)
        self.vbl.addLayout(self.buttonLayout)
        self.vbl.addLayout(self.checkLayoutAna)
        self.vbl.addLayout(self.checkLayoutDig)
        
        self.setLayout(self.vbl) # compose grid layout
        self.show() # show main window
        fg = self.frameGeometry()  # geometry of the main window
        cp = QtW.QDesktopWidget().availableGeometry().center() # center point of screen
        fg.moveCenter(cp) # move rectangle's center point to screen's center point
        self.move(fg.topLeft()) # top left of rectangle becomes top left of window centering it
        self.setWindowTitle("GoodTime Python Visualization for SAROCEMA sequences")
        self.showMaximized() # MAKE IT BIG
        
        # Window icon
        app_icon = QtGui.QIcon()
        app_icon.addFile('icons/GT_logo.png', QtCore.QSize(32,32))
        self.setWindowIcon(app_icon)

        # Fixing an initialization problem (the dirty way)
        if self.checkedChs != []:
            idx = self.checkedChs[0]
            self.checkboxChs[idx].setChecked(False)
            self.checkboxChs[idx].setChecked(True)
        
    def change_timeoffset(self):
        self.timeoffset = self.timeoffsetSpinbox.value()
        self.update_plot()
        
    def isDigital(self, chnumber):
        """ Returns True if chnumber represents a digital channel. Edit this if more chnumbers need to be accounted for """
        if chnumber <= 31:
            return True
        elif (chnumber <= 107) & (chnumber >= 76):
            return True
        return False

    def start_SeqPlot(self):
        if self.startbutton.isChecked(): 
            self.startbutton.setText('Stop')
            self.pausestatus = False
        else:
            self.startbutton.setText('Start')
            self.pausestatus = True
            
    
    def _saveSettings(self):
        settings = {"checkedChs": self.checkedChs, "checkedDig": self.checkedDig, "timeoffset":self.timeoffset, "colortable": self.colortable}
        with open(self.config_filename, 'w') as f:
            json.dump(settings, f)
            print("Config file saved !")
    
    def _loadSettings(self):
        self.checkedChs = []
        self.checkedDig = []
        try:
            with open(self.config_filename, 'r') as f:
                imported_settings = json.load(f)
                logging.info("Config file loaded !")
            self.timeoffset = imported_settings["timeoffset"]
            # self.checkedChs = imported_settings["checkedChs"]
            # self.checkedDig = imported_settings["checkedDig"]
            # self.colortable = imported_settings["colortable"]
        except:
            logging.info("No config file found.")
            self.timeoffset = 0
        
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

    def _formattext(self, label):
        """Formats a label by removing tabs, white spaces and ;"""
        return label.replace('\t', "").replace(";", "").replace(" ", "")

    def _formatlist(self, inputlist):
        """Returns a formatted array of channel names.
        Input:
        inputlist: ndarray from GoodTime commondef (raw)
        Output:
        res: ndarray of channel labels"""
        res = np.full(self.Nchannels,"Inactive", dtype=object)
        for label in inputlist:
            label = self._formattext(label)
            split = label.split("=")
            if len(split) > 1:
                chname, chnumber = split[0], int(split[1])
                res[chnumber] = chname
        return res

    def getlabels(self, commondef_fname):
        # listed_names = np.genfromtxt(commondef_fname, dtype='str', comments='//', delimiter = ' = ', skip_header=15, max_rows=self.Nchannels + 5, usecols=(0,))
        listed_names = np.genfromtxt(commondef_fname, dtype='str', comments='//', delimiter = '\n', skip_header=15, max_rows=self.Nchannels + 10, usecols=(0,))
        return self._formatlist(listed_names)
    
    @QtCore.pyqtSlot(object)
    def update_data(self, data):
        self.datatemp = data
        if self.pausestatus == False and self.updateCheckbox.isChecked() or self.data == []:
            self.data_arrived = True
            self.data = data
            self.x = self.dtStep * np.arange(data[0].shape[0])
#            self.tracelabel.setText(str(len(self.data))+' traces in memory')
            self.update_plot()
        elif self.pausestatus == False and not self.updateCheckbox.isChecked():
            self.data_arrived = True
        else:
            pass

    def chselect(self, chn):
        '''
        Returns data, formatted according to channel number specificity.
        channel number start with 0
        0  -- 31 digital channels NI6533 - Device 1
        32 -- 39 analog channels NI6733 16 bits - Device 2
        40 -- 71 analog NI6723 13 bits - Device 3
        72 -- 75 analog NI6259 16 bits - Device 5
        76 -- 107 digital NI6259 - Device 5
        Device 4 (PIC6723, same as 3) not used 
        '''
#        print('chselect')
        if chn >=0 and chn < 32: dataout = np.array(self.data[0][:,chn], dtype = np.float64)
        elif chn < 40: dataout = np.array(self.data[1][:,chn-32], dtype = np.float64) / (2**16 - 1)
        elif chn < 72: dataout = np.array(self.data[2][:,chn-40], dtype = np.float64) / (2**13 - 1)
        elif chn < 76: dataout = np.array(self.data[3][:,chn-72], dtype = np.float64) / (2**16 - 1)
        elif chn < 108: dataout = np.array(self.data[4][:,chn-76], dtype = np.float64)
        else: print('channel number error!'); return None
        return dataout
        
    ################################################################################
    ####                             PLOTTING                                   ####
    ################################################################################
    
    def init_plot(self, num):
        i = num
        if self.isDigital(i):
            newplot = self.ax2.plot([0], [0], "-", color = self.colortable[i])
        else:
            newplot = self.ax1.plot([0], [0], "-", color = self.colortable[i])
        self.dataplot.append(newplot)
        if i in self.checkedChs:
            # self.checkboxChs[i].setStyleSheet('color:'+ newplot[0].get_color() + ';')
            self.checkboxChs[i].setStyleSheet('background-color:'+ self.colortable[i] + ';')
        return True
    
    def add_plot(self):
        boxtext = self.sender()
        i = int(boxtext.text()[2:5])
#        print('add_plot ch%.0f' %(i))
        if self.checkboxChs[i].isChecked():
            self.checkedChs.append(i)
            if i in self.listDig:
                self.checkedDig.append(i)
                newplot = self.ax2.plot(self.x- self.timeoffset, self.chselect(i) - 1.1*float(self.checkedDig.index(i)), '-',
                                        lw = self.linewidth, color = self.colortable[i]) # shift digital lines according to the position in the list
                # ydata = self.chselect(i)
                # newplot = self.ax2.fill_between(self.x- self.timeoffset, ydata - 1.1*float(self.checkedDig.index(i)),
                                                # np.multiply(ydata, 0.01) - 1.1*float(self.checkedDig.index(i)), '-',  color = self.colortable[i]) # shift digital lines according to the position in the list
                # newplot = self.ax2.fill_between(self.x- self.timeoffset, self.chselect(i) - 1.1*float(self.checkedDig.index(i)),
                                                # 0* self.chselect(i) - 1.1*float(self.checkedDig.index(i)), '-') # shift digital lines according to the position in the list
              
            else:
                newplot = self.ax1.plot(self.x- self.timeoffset, self.chselect(i), '-', 
                                        lw = self.linewidth, color = self.colortable[i])
            # self.checkboxChs[i].setStyleSheet('color:'+ newplot[0].get_color() + ';')
            self.checkboxChs[i].setStyleSheet('background-color:'+  self.colortable[i] + ';')
            self.dataplot.append(newplot)
        else:
            self.checkboxChs[i].setStyleSheet('background-color:rgba(255, 255, 255, 0)')
            if i in self.checkedChs: 
                idx2remove = self.checkedChs.index(i)
                self.dataplot[idx2remove].pop(0).remove() # not remove list, but remove line
                del self.dataplot[idx2remove]
                self.checkedChs.remove(i)
            if i in self.checkedDig:
            # if i in self.listDig:
                old_checkedDig = self.checkedDig.copy() # save old list to know how much they were shifted
                self.checkedDig.remove(i)               # new list to determine how much they should be shifted
                for j, jj in enumerate(self.checkedChs): # to reposition the digital lines
                    if jj in self.checkedDig: 
                        dataOld = self.dataplot[j][0].get_ydata() # get data of the old line (to be shifted)
                        self.dataplot[j][0].set_ydata(dataOld + 1.1*float(old_checkedDig.index(jj) - self.checkedDig.index(jj)))
                
        # self.ax1.relim(); self.ax2.relim()
        self.ax1.autoscale(axis='y');self.ax2.autoscale(axis='y')
        self.canvas.draw() 
        
    def update_plot(self):
        """
        Updates plot with new data.
        """
        for i in range(len(self.dataplot)):
            self.dataplot[i][0].set_xdata(self.x - self.timeoffset)
            idx = self.checkedChs[i]
            if self.isDigital(idx):
                self.dataplot[i][0].set_ydata(self.chselect(self.checkedChs[i])-1.1*float(self.checkedDig.index(idx)))     
            else:
                self.dataplot[i][0].set_ydata(self.chselect(self.checkedChs[i]))
        # self.ax1.set_xlim(self.x[0] - self.timeoffset,self.x[-1]- self.timeoffset)  
        # self.ax1.relim(); self.ax2.relim()
#        self.ax1.autoscale();self.ax2.autoscale()        
        self.canvas.draw()
        
    def clear_plot(self):
        for i in range(len(self.dataplot)):
            self.dataplot[i].pop(0).remove()
            self.checkboxChs[self.checkedChs[i]].setChecked(False)
            self.checkboxChs[self.checkedChs[i]].setStyleSheet('background-color:rgba(255, 255, 255, 0)')
        self.dataplot = []
        self.checkedChs = []
        self.checkedDig = []
        self.ax1.set_xlim(self.x[0] - self.timeoffset,self.x[-1]- self.timeoffset)  
#        self.ax2.set_xlim(self.x[0],self.x[-1])  
#        self.ax1.set_ylim(0,1)
        self.canvas.draw()
        
    def reset_zoom(self):
        self.ax1.set_xlim(self.x[0]- self.timeoffset,self.x[-1]- self.timeoffset)  
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
        self._saveSettings()
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
        self.lastmodtimeNOW = path.getmtime(self.fileName + '/AnaBuffer1.bin')
        if self.startcount == 0:
            self.dataRetriever()
        if abs(self.lastmodtimeNOW - self.lastmodtime) >= 0.2:
            self.dataRetriever()
            
    def dataRetriever(self):
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
        time = datetime.now().strftime("%H:%M:%S")
        logging.info("@ "time + f': Loading dataset #{self.startcount}')
            
            

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = QtCore.QCoreApplication.instance() # checks if QApplication already exists 
    if app is None: # create QApplication if it doesnt exist 
        app = QtW.QApplication(sys.argv)
    goodtimefolder = "//MOUFFETARD/goodTime_exchange"
    goodTimeSeq = GoodTimeWindow(goodtimefolder, commondef=goodtimefolder + '/SAROC_Commondefs_2024_04_30.sqi')
    goodTimeSeq.activateWindow()
    app.aboutToQuit.connect(app.deleteLater)
    app.exec_()            
