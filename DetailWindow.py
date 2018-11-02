from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import time
from threading import Thread
from multiprocessing import Process
from queue import Queue
from random import random



class DetailWindow(QMainWindow):
    def __init__(self):
        super(DetailWindow,self).__init__()
        self.cache={} #This data is what is plotted.
        self.figs=[] #These are the figures to plot on.
        self.output=None
        
        canvas,figure = self.getCanvas()
        self.figure=figure #Pyplot
        self.canvas=canvas #QWidget

        self.mainWidget=QWidget()
        self.setCentralWidget(self.mainWidget)
        layout=QHBoxLayout(self.mainWidget)
        layout.addWidget(self.getMenu())        
        layout.addWidget(canvas)
            
    def getOutputBox(self):
        scroll=QScrollArea()
        output=QWidget()
        scroll.setWidgetResizable(True)
        scroll.setWidget(output)
        layout=QFormLayout(output)
        self.output=layout
        return scroll

    def getMenu(self):
        menu=QWidget()
        menu.setFixedWidth(menu.width())
        layout=QFormLayout(menu)
        btn=QPushButton("Force Shutdown")
        btn.clicked.connect(lambda: self.log('pushed'))
        layout.addWidget(btn)
        layout.addWidget(self.getOutputBox())
        return menu
        
    def getCanvas(self):
        figure=plt.figure()
        canvas=FigureCanvas(figure)
        self.testJumple()
        return canvas,figure
            
    def log(self,text):
        self.output.addRow(QLabel("%.02f"%(time.time()%100)),QLabel(str(text)))

    #All on one plot.
    def addPoint(self,point):
        self.fig.clear()
        for key,item in point.items():
            try:
                self.cache[key]
            except KeyError:
                self.cache[key]=[]
            self.cache[key].append(item)
            x=range(len(self.cache[key]))
            self.fig.plot(x,self.cache[key],label=key)
        self.fig.legend()
        self.canvas.draw()
        
    ''' #This is for every data point on its own plot.
    def addPoint(self,point):
        for tmp,fig in zip(point.items(),self.figs):
            key,item=tmp
            try:
                self.cache[key]
            except KeyError:
                self.cache[key]=[]
            self.cache[key].append(item)
            fig.clear()
            x=range(len(self.cache[key]))
            fig.plot(x,self.cache[key])
        self.canvas.draw()
        '''
        
    def testJumple(self):
        for fig in self.figs:
            fig.plot([x for x in range(100)],[random() for y in range(100)])


