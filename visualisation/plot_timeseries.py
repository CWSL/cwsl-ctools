#!/bin/env python

import argparse

#CDAT
import cdms2
import numpy as np

#Matplotlib libraries
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as font_manager
from pylab import legend

def plot(variable,ifile,ofile):

    fin = cdms2.open(ifile,'r')
    data = fin(variable,squeeze=1)

    time_axis = data.getAxis(0).asComponentTime()[:]
    time_axis = data.getAxis(0)
    units = data.units

    plt.plot(time_axis,np.array(data),color='blue',lw=3.0,label=variable)

    plt.ylabel(units)
    plt.xlabel('Time')

    font = font_manager.FontProperties(size='medium')
    legend(loc=2,prop=font,numpoints=1,labelspacing=0.3,ncol=2)

    #plt.show()
    plt.savefig(ofile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot timeseries from NetCDF file')
    parser.add_argument('variable', help='variable name')
    parser.add_argument('input', help='input file (nc)')
    parser.add_argument('output', help='output file (png)')
    args = parser.parse_args()

    plot(args.variable, args.input, args.output)
