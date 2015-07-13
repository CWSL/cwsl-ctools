#!/usr/bin/env python

''' Script to plot directly from CDO seas output files in cwsl. '''

from argparse import ArgumentParser
import numpy as np
import os,commands,cdms2

from mpl_toolbox import utils
from mpl_toolbox import colour_utils
from mpl_toolbox import Plot, Panel

m_list = ('january','february','march','april','may','june','july','august','september','october','november','december')
s_list = ('djf','mam','jja','son','ndjfma','mjjaso','annual')

cdms2.setNetcdfShuffleFlag(0) ## where value is either 0 or 1
cdms2.setNetcdfDeflateFlag(0) ## where value is either 0 or 1
cdms2.setNetcdfDeflateLevelFlag(0) ## where value is a integer between 0 and 9 included



# Main
##############################################################################

if __name__ == '__main__':

    parser = ArgumentParser(description='''Make a quick plot of some netCDF files''')

    parser.add_argument('infile',
                        help='The netcdf file to plot.')#nargs='+',
    parser.add_argument('outfile',
                        help='The output plot file.')
    parser.add_argument('--variable',
                        help='The name of the variable to plot.',
                        default=None)
    parser.add_argument('--region',
                        help='The region of the world to show in the plot.',
                        default='WORLD360')
    parser.add_argument('--title',
                        help='The title of the output plot.',
                        default=None)
    parser.add_argument('--colourmap',
                        help='The colour map to use for this plot.',
                        default='hot')
    parser.add_argument('--ticks',
                        help='''The levels to break up the colour map at. Takes a string of the form:
                        (0.1,1.3,2.5,3.8,4.1) for open intervals or [0.0,1.1,2.0,3.6,4.8] for closed''',
                        type=str,
                        default=None)
    parser.add_argument('--plot_type',
                        help='The type of plot to be drawn',
                        choices=['pcolor', 'contourf', 'contour'],
                        default='pcolor')
    parser.add_argument('--units',
                        help='''Override the 'units' metadata in the netCDF file''',
                        default=None)
    parser.add_argument('--shapefile',
                        help='''Path to a shapefile to draw over every plot in the panel''',
                        default=None)
    parser.add_argument('--conv_units',
                        help='''Convert the units of the variable plotted in the panel''',
                        default='False')
    args = parser.parse_args()
    
    infile = args.infile
    variable = args.variable
    
    ### convert conv_units to boolean ###
    conv_units = args.conv_units
    if conv_units.lower() in ['true', 't', '1','on','yes','y']:
        conv_units = True
    else:
        conv_units = False

    ### if variable not specified get first one listed in file ###
    if (variable == None or variable == ''):
        
        variable = commands.getstatusoutput('cdo showname %s' %infile )[1].split('\n')[1].split()[0]
    
    ### generate a list of tmp filenames ###
    fpath,fname = os.path.split(infile)
    tmpfname,extn = os.path.splitext(fname)
    tmpInFile = cdms2.open(infile,'r')
    tvar_orig = tmpInFile[variable]
    tvals     = tvar_orig.getTime().asComponentTime()
    noseas    = len(tvals)
    glob_atts = tmpInFile.attributes
 
    ### add the filename as title if no title supplied ###
    if args.title == None:
        title = fname
    else:
        title = args.title
    print conv_units
    ### split input aggregated file into seperate season files ### 
    inFileList =[]
    for seas in range(1, noseas + 1):
        outFileName = '%s_%s%s' %(fname,seas,extn)
	outFileName = os.path.join(fpath,outFileName)
	inFileList.append(outFileName)
	tvar = tvar_orig[seas - 1 ]
	tvar.id = variable
	
	outFile = cdms2.open(outFileName,'w')
	glob_atts['model_id'] = str(seas)
        try:
            glob_atts['parent_experiment_rip'] = ''
	except:
            pass
        for key,value in glob_atts.iteritems():
	    setattr(outFile, key, value)
	outFile.write(tvar)
	outFile.close()
    tmpInFile.close()	
    
    # Set the correct number of rows and columns
    nrows, ncols = utils.calc_rows_cols(inFileList)
    
    # Make an empty numpy array to hold the plots.
    plot_array = np.empty((nrows, ncols), dtype=Plot)
    
    # Sort the file list alphabetically.
    #infiles.sort(key=lambda x: os.path.basename(x.lower()))

    # We want all the files to have the same colourmap, so we create
    # it first and then pass it to all the plots in the quick_plot.
    # Do do this we need a dummy plot to base the colourmap on.
    # This is only necessary when a cmap name, but not ticks are given.
    # The dummy_plot is required for the maximum and minumum.
    
    dummy_plot = Plot.from_file(inFileList[0], variable, args.region, units=args.units,
                                convert_units=conv_units)
    colourmap = colour_utils.process_cmap(args.colourmap, dummy_plot,
                                          tick_string=args.ticks)

    # For every file in the file list create a plot
    # and add it to the array.
    
    for i,fileName in enumerate(inFileList):
	plot_array.flat[i] = Plot.from_file(fileName,
                                            variable,
                                            region=args.region,
                                            shapefile=args.shapefile,
                                            cmap=colourmap,
                                            units=args.units,
                                            convert_units=conv_units,)

    # Make the panel.
    climate_panel = Panel(plot_array,
                          args.outfile,
                          title=title)

    # Draw the panel, add the colour bar and dates
    # then save the figure to the output file.
    climate_panel.add_panel_colourbar()
    climate_panel.draw_plots(plot_type=args.plot_type)
    climate_panel.add_date()
    climate_panel.save_figure()
    
    for i,fileName in enumerate(inFileList):
        os.remove(fileName)
    
