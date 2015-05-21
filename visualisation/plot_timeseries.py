#!/bin/env python

import argparse
import datetime

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

def plot(title,variable,ifile,ofile):
    """
    Based on example from http://matplotlib.org/examples/api/date_demo.html
    """

    fin = cdms2.open(ifile,'r')
    data = fin(variable,squeeze=1)

    #Convert time axis to datetime
    time_axis = [datetime.datetime(d.year,d.month,d.day) for d in data.getAxis(0).asComponentTime()]
    units = data.units

    fig, ax = plt.subplots()
    ax.plot(time_axis,np.array(data),color='blue',lw=3.0,label=variable)

    years    = mdates.YearLocator(5)   # every 5 years
    yearly   = mdates.YearLocator()  # every year
    yearsFmt = mdates.DateFormatter('%Y')

    # format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(yearly)

    datemin = time_axis[0]
    datemax = datetime.date(time_axis[-1].year+1, 1, 1)
    ax.set_xlim(datemin, datemax)

    # format the coords message box
    ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')

    # rotates and right aligns the x labels, and moves the bottom of the
    # axes up to make room for them
    fig.autofmt_xdate()

    ax.set_ylabel(units)
    ax.set_xlabel('Time')
    ax.set_title(title)

    font = font_manager.FontProperties(size='medium')
    legend(loc=2,prop=font,numpoints=1,labelspacing=0.3,ncol=2)

    fig.savefig(ofile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot timeseries from NetCDF file')
    parser.add_argument('variable', help='variable name')
    parser.add_argument('input', help='input file (nc)')
    parser.add_argument('output', help='output file (png)')
    parser.add_argument('--title', help='Plot Title',
                        default="Timeseries Plot")

    args = parser.parse_args()

    plot(args.title, args.variable, args.input, args.output)
