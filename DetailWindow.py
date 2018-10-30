from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import time

class DetailWindow(QMainWindow):
    def __init__(self):
        super(DetailWindow,self).__init__()
        self.graph=None
        self.mainWidget=QWidget()
        self.setCentralWidget(self.mainWidget)
        self.output=None
        layout=QHBoxLayout(self.mainWidget)
        layout.addWidget(self.getMenu())
        canvas,figure = self.getCanvas()
        self.figure=figure
        layout.addWidget(canvas)

    def getOutputBox(self):
        scroll=QScrollArea()
        output=QWidget()
        scroll.setWidgetResizable(True)
        scroll.setFixedSize(500,500)
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
        return canvas,figure

    def log(self,text):
        self.output.addRow(QLabel("%.02f"%(time.time()%100)),QLabel(str(text)))



