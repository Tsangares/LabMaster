import xlsxwriter
import matplotlib
import time
import platform
from numpy import linspace
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
matplotlib.use("TkAgg")


def writeExcel(data,filename):
    filename="outputfiles.xlsx"
    if "Windows" not in platform.platform():
        filename = tkFileDialog.asksaveasfilename(initialdir="~", title="Save data", filetypes=(("Microsoft Excel file", "*.xlsx"), ("all files", "*.*")))
    fname = (((filename+"_"+str(time.asctime(time.localtime(time.time())))+".xlsx").replace(" ", "_")).replace(":", "_"))
    workbook=xlsxwriter.Workbook(fname)
    worksheet=workbook.add_worksheet()
    #Get parameters
    data={} #assuming map key of variables, place them all into a grid.
    column=0
    for key, values in data:
        worksheet.write(0,column,key)
        for i,value in enumerate(values):
            worksheet.write(i+1,column,value) #i+1 because the title is above
        column+=1
    #chart?

    