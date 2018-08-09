# Program: 
#   calculate_gev.R
#
# Author:
#   Louise.Wilson@csiro.au
#
# Purpose:
#   To calculate GEV parameters in preparation for ARI calcualtion  
#
# Useage:
#   Rscript calc_GEV [infile] [method] [var] [start] [end]
#   pipeline calc_gev_workflow.xml calc_GEV "season=ann|DJF|MAM|JJA|SON,fit_method=lmom" -uv
#
# Inputs/Outputs:
#   input  : variable maxima for the globe (infile)
#   output : netcdf containing (location,scale,shape) xi, alpha, k, 
#	     return levels (5, 10, 20, 50, 100) 
#	     method used for fitting GEV distribution (lmom,mle,pfit)
#
# Raw files are located on Cherax here: /datastore/cmar/csar4/ftp.cccma.ec.gc.ca/data/climdex/REANALYSES/historical/
#
# Environment:
# module load netcdf/3.6.3
# module load R/2.15.1-gcc or R/2.13.1-gcc
# module load cdo/1.5.4
#
# Updates | By | Description
# --------+----+------------
# 18 Feb 2013 | Louise Wilson | All seasons
#
# requires the packages ncdf,lmom and ismev (what about evir?)
# to install packages on dcc using R:
# install.packages('package_name')
# 
# ncdf:	http://cran.r-project.org/web/packages/ncdf/index.html
# lmom:	http://cran.r-project.org/web/packages/lmom/index.html
# ismev:http://cran.r-project.org/web/packages/ismev/ismev.pdf
# (evir:http://hosho.ees.hokudai.ac.jp/~kubo/Rdoc/library/evir/html/gev.html)

rm(list=ls())

# load required packages
require(ncdf)
require(lmom)
require(ismev)
require(evd)

###################### FUNCTIONS #######################

# Function to open a netcdf file and read in any variable
read_netcdf <- function(filename,variable=c("txxETCCDI","rx1dayETCCDI","tnnETCCDI","sfcWindmax","pr","tasmax","tasmin","rx1day","txx","tnn","sfcWind")){
    nc <- open.ncdf(filename)
    lons <- nc$dim$lon$vals	# x
    lats <- nc$dim$lat$vals	# y
    # get the time attribute into something useful 
    # (http://geography.kcl.ac.uk/micromet/Troubleshoot/Handle_netCDF.R)
    tvar <- get.var.ncdf(nc,"time")
    origin <- nc$dim$time$units
    tunits <- strsplit(nc$dim$time$units,split=" ")
    # if the unit is "minutes", they have to be converted to "mins" so that the strptime function can cope with it
    if(identical(tunits[[1]][1],"minutes")) tunits[[1]][1]<-"mins"
    print(origin)
    print(tvar)
    # now your relative time axis tvar can be converted to an absolute time axis.
    # note that the resulting object from strptime function is a time object
    #TIME   <- strptime(paste(tunits[[1]][3]),format="%Y-%m-%d",tz="GMT")+
		       #as.numeric(as.difftime(tvar,units=tunits[[1]][1]),units="secs")
    TIME    <-  seq(as.Date(origin=tunits[[1]][3]),length.out=length(tvar),by=tunits[[1]][1])
    print(TIME)
    # get variable
    var<-match.arg(variable)
    var_data <- get.var.ncdf(nc,var)
    if (sum(range(var_data)>1e20)) {stop('Execution halted: Missing variable data')}
    close.ncdf(nc)

    if (variable == 'pr') {
	if (nc$var$pr$units == "kg m-2 s-1") {var_data <- var_data * 86400}
	}
    if (variable == 'tasmin') {
	if (nc$var$tasmin$units == "K") {var_data <- var_data -273.15}
	}
    if (variable == 'tasmax') {
	if (nc$var$tasmin$units == "K") {var_data <- var_data -273.15}
	}

    ncfile<-list(TIME,origin,lons,lats,var_data)
    names(ncfile)<-c('time','origin','lons','lats',as.character(variable))
    return(ncfile)
    }


# Function to create annual maximum time series for input to GEV calculation
# NOTE: DJF is currently defined during one year, not across two years...
calc_annual_max <- function(ncfile,season=c("ann","DJF","MAM","JJA","SON","MJJASO","NDJFMA")){
    year_list<-unique(strftime(ncfile$time,"%Y"))
    yindex<-strftime(ncfile$time,"%Y")
    mindex<-as.numeric(strftime(ncfile$time,"%m"))
    ann <- as.numeric(unique(strftime(ncfile$time,"%m")))
    DJF <- c(12,01,02)
    MAM <- c(03,04,05)
    JJA <- c(06,07,08)
    SON <- c(09,10,11)
    MJJASO <- c(05,06,07,08,09,10)
    NDJFMA <- c(11,12,01,02,03,04)
    seas<-get(match.arg(season))
    
    annual_var<-array(NA,dim=c(length(ncfile$lats),length(ncfile$lons),length(year_list)))
    for (i in 1:length(year_list)){
	if (season == 'ann'){
	    yy<-which(yindex==year_list[i])
	    mm<-c( yy[mindex[yy]==seas[1]],yy[mindex[yy]==seas[2]],yy[mindex[yy]==seas[3]],yy[mindex[yy]==seas[4]],yy[mindex[yy]==seas[5]],yy[mindex[yy]==seas[6]],yy[mindex[yy]==seas[7]],yy[mindex[yy]==seas[8]],yy[mindex[yy]==seas[9]],yy[mindex[yy]==seas[10]],yy[mindex[yy]==seas[11]],yy[mindex[yy]==seas[12]] )
	    kk<-yy[mm]
	}
	if (season != 'DJF' & season != 'NDJFMA') {  
	    yy<-which(yindex==year_list[i])
	    if (length(seas)==3) mm<-c( yy[mindex[yy]==seas[1]], yy[mindex[yy]==seas[2]], yy[mindex[yy]==seas[3]] )
	    if (length(seas)==6) mm<-c( yy[mindex[yy]==seas[1]], yy[mindex[yy]==seas[2]], yy[mindex[yy]==seas[3]], yy[mindex[yy]==seas[4]], yy[mindex[yy]==seas[5]], yy[mindex[yy]==seas[6]] )
	    kk<-mm
	    }
	if (season == 'DJF') {
	    if (i==1) next # skip first year
	    yy<-which(yindex==year_list[i])
	    yyD<-which(yindex==year_list[i-1])  # previous year for December
	    mm<-c( yyD[mindex[yyD]==seas[1]], yy[mindex[yy]==seas[2]], yy[mindex[yy]==seas[3]] )
	    kk<-mm
	    }
	if (season == 'NDJFMA') {
	    if (i==1) next # skip first year
	    yy<-which(yindex==year_list[i])
	    yyD<-which(yindex==year_list[i-1])  # previous year for December
	    mm<-c( yyD[mindex[yyD]==seas[1]], yyD[mindex[yyD]==seas[2]], yy[mindex[yy]==seas[3]] , yy[mindex[yy]==seas[4]], yy[mindex[yy]==seas[5]], yy[mindex[yy]==seas[6]])
	    kk<-mm
	    }

	if (names(ncfile)[5] == 'rnd24'){
	    annual_var[,,i]<-apply(ncfile$rnd24[,,kk],1:2, max)
	    }
	if (names(ncfile)[5] == 'pr'){
	    annual_var[,,i]<-apply(ncfile$pr[,,kk],1:2, max)
	    }
	if (names(ncfile)[5] == 'rx1dayETCCDI'){
	    annual_var[,,i]<-apply(ncfile$rx1dayETCCDI[,,kk],1:2, max)
	    }
	if (names(ncfile)[5] == 'txxETCCDI'){
	    annual_var[,,i]<-apply(ncfile$txxETCCDI[,,kk],1:2, max)
	    }
	if (names(ncfile)[5] == 'tnnETCCDI'){
	    annual_var[,,i]<-apply(ncfile$tnnETCCDI[,,kk],1:2, min)*c(1,1,-1)
	    }
	if (names(ncfile)[5] == 'sfcWindmax'){
	    annual_var[,,i]<-apply(ncfile$sfcWindmax[,,kk],1:2, max)
	    }
	if (names(ncfile)[5] == 'tasmax'){
	    annual_var[,,i]<-apply(ncfile$tasmax[,,kk],1:2, max)
	    }
	if (names(ncfile)[5] == 'tasmin'){
	    annual_var[,,i]<-apply(ncfile$tasmin[,,kk],1:2, max)*c(1,1,-1)
	    }
	if (names(ncfile)[5] == 'rx1day'){
	    annual_var[,,i]<-apply(ncfile$rx1day[,,kk],1:2, max)
	    }
	if (names(ncfile)[5] == 'txx'){
	    annual_var[,,i]<-apply(ncfile$txx[,,kk],1:2, max)
	    }
	if (names(ncfile)[5] == 'tnn'){
	    annual_var[,,i]<-apply(ncfile$tnn[,,kk],1:2, min)*c(1,1,-1)
	    }
	if (names(ncfile)[5] == 'sfcWind'){
	    annual_var[,,i]<-apply(ncfile$sfcWind[,,kk],1:2, max)
	    }

	    }
    
    return(annual_var)
    }


# Function required for gevp.fit 
stedLogPrior <- function(xi){
    if(any(xi < -.5 | xi > .5)){
	return(-Inf)
	}
    else {
	out1 <- lgamma(15) - lgamma(9) - lgamma(6)
	out2 <- 8*log(.5 + xi) + 5*log(.5 - xi)
	return(out1+out2)
	}
    }


# Function to calculate penalised fit GEV distribution
# requires stedLogPrior function
# Contact: Louise Wilson louise.wilson@csiro.au
# Developed by Dan Cooley; modified from ismev package
gevp.fit <- function(xdat, ydat=NULL, mul = NULL, sigl = NULL, shl = NULL, 
    mulink = identity, siglink = identity, shlink = identity, 
    show = TRUE, method = "Nelder-Mead", maxit = 10000, ...){

    z <- list()
    npmu <- length(mul) + 1
    npsc <- length(sigl) + 1
    npsh <- length(shl) + 1
    z$trans <- FALSE
    in2 <- sqrt(6 * var(xdat))/pi
    in1 <- mean(xdat) - 0.57722 * in2
    if (is.null(mul)) {
        mumat <- as.matrix(rep(1, length(xdat)))
        muinit <- in1
    }
    else {
        z$trans <- TRUE
        mumat <- cbind(rep(1, length(xdat)), ydat[, mul])
        muinit <- c(in1, rep(0, length(mul)))
    }
    if (is.null(sigl)) {
        sigmat <- as.matrix(rep(1, length(xdat)))
        siginit <- in2
    }
    else {
        z$trans <- TRUE
        sigmat <- cbind(rep(1, length(xdat)), ydat[, sigl])
        siginit <- c(in2, rep(0, length(sigl)))
    }
    if (is.null(shl)) {
        shmat <- as.matrix(rep(1, length(xdat)))
        shinit <- 0.1
    }
    else {
        z$trans <- TRUE
        shmat <- cbind(rep(1, length(xdat)), ydat[, shl])
        shinit <- c(0.1, rep(0, length(shl)))
    }
    z$model <- list(mul, sigl, shl)
    z$link <- deparse(substitute(c(mulink, siglink, shlink)))
    init <- c(muinit, siginit, shinit)
    gev.lik <- function(a) {
        mu <- mulink(mumat %*% (a[1:npmu]))
        sc <- siglink(sigmat %*% (a[seq(npmu + 1, length = npsc)]))
        xi <- shlink(shmat %*% (a[seq(npmu + npsc + 1, length = npsh)]))
        y <- (xdat - mu)/sc
        y <- 1 + xi * y
        if (any(y <= 0) || any(sc <= 0)) 
            return(10^6)
        sum(log(sc)) + sum(y^(-1/xi)) + sum(log(y) * (1/xi + 
            1))-stedLogPrior(xi[1])
    }
    x <- optim(init, gev.lik, hessian = TRUE, method = method, 
        control = list(maxit = maxit, ...))
    z$conv <- x$convergence
    mu <- mulink(mumat %*% (x$par[1:npmu]))
    sc <- siglink(sigmat %*% (x$par[seq(npmu + 1, length = npsc)]))
    xi <- shlink(shmat %*% (x$par[seq(npmu + npsc + 1, length = npsh)]))
    z$nllh <- x$value
    z$data <- xdat
    if (z$trans) {
        z$data <- -log(as.vector((1 + (xi * (xdat - mu))/sc)^(-1/xi)))
    }
    z$mle <- x$par
    z$cov <- solve(x$hessian)
    z$se <- sqrt(diag(z$cov))
    z$vals <- cbind(mu, sc, xi)
    if (show) {
        if (z$trans) 
            print(z[c(2, 3, 4)])
        else print(z[4])
        if (!z$conv) 
            print(z[c(5, 7, 9)])
    }
    invisible(z)
 }


# Function to fit GEV distribution and calculate KS statistics
# order of parameters - location (mu, xi), scale (sigma, alpha), shape (psi, k)
# Note: the pelgev function defines shape = -k
ks_all <- function(data, fit_method){
    if (fit_method == 'lmom'){  
	# use lmom package to calculate L-moments (samlmu) and then fit GEV distribution (pelgev)
	#params <- pelgev(samlmu(data,nmom=4,sort.data=TRUE))*c(1,1,-1)
	params <- pelgev(samlmu(data,nmom=4,sort.data=TRUE))
	}
    if (fit_method == 'pfit'){
	# use function gevp.fit (modified from ismev package) to calculate GEV penalised fit	
	params <- gevp.fit(data, show=FALSE)$mle*c(1,1,-1)
	}
    if (fit_method == 'mle'){
	# use ismev package to calculate GEV from maximum liklihood method (gev.fit)
	params <- gev.fit(data, show=FALSE)$mle*c(1,1,-1)
	}
    #d_stat <- ks_boot(data,params,fit_method)
    return(c(params))
    }


# Function to calculate GEV for any time period
calc_GEV <- function(fit_method=c('lmom','pfit','mle'),var,times,start,end){
    year_list<-unique(strftime(times,"%Y"))
    print(start)
    print(end)
    index <- which(year_list >= start & year_list <= end)
    if (length(index) < 20) {stop('Execution halted: Less than 20 years available for GEV analysis period')}
    dstat<-apply(var[,,index],1:2,ks_all,match.arg(fit_method))
    return(list(params=dstat[1:3,,]))
    }


# Function to calculate return levels and add to existing netcdf outfile created by write_nc()
calc_RetLevel<-function(nc_GEV,Return_Period,netcdf_outfile,lon_dim,lat_dim){
    RV <- 1 - 1/Return_Period
    infile_Ret_Level <- apply(nc_GEV$params,2:3,quagev,f=RV)
    Ret_Level<-matrix(infile_Ret_Level,length(nc$lons),length(nc$lats))
    # define variables
    RetLevel<- var.def.ncdf(paste('RetLevel',Return_Period,sep=''),'day-1',list(lon_dim, lat_dim),missval=-NA,longname=paste('Return Level: ',Return_Period,'yrs',sep=''),prec='double')
    ## write data to output
    ncout<-open.ncdf(as.character(netcdf_outfile),write=T)
    ncout<-var.add.ncdf(ncout, RetLevel)
    close(ncout)
    ncout<-open.ncdf(as.character(netcdf_outfile),write=T)
    put.var.ncdf(ncout,RetLevel,Ret_Level)
    close(ncout)
    }

# Function to write parameters to netcdf file
write_nc <- function(nc,nc_GEV,out_name){
    xi		<-matrix(nc_GEV$params[1,,],length(nc$lons),length(nc$lats))
    alpha	<-matrix(nc_GEV$params[2,,],length(nc$lons),length(nc$lats))
    k		<-matrix(nc_GEV$params[3,,],length(nc$lons),length(nc$lats))
    
    # define dimensions
    lon_dim 	<- dim.def.ncdf('lon'	,'degrees_east',nc$lons)
    lat_dim 	<- dim.def.ncdf('lat'	,'degrees_north',nc$lats)
    gev_xi	<- var.def.ncdf('xi'	,'none',list(lon_dim,lat_dim),missval=NA,longname='GEV location parameter',prec='double')
    gev_alpha	<- var.def.ncdf('alpha'	,'none',list(lon_dim,lat_dim),missval=NA,longname='GEV scale parameter',prec='double')
    gev_k	<- var.def.ncdf('k'	,'none',list(lon_dim,lat_dim),missval=NA,longname='GEV shape parameter',prec='double')

    # create netCDF outfile
    ncout <- create.ncdf(outfile, list(gev_xi,gev_alpha,gev_k))#,KStest,bKStest,pKStest))   
    put.var.ncdf(ncout, gev_xi, xi)
    put.var.ncdf(ncout, gev_alpha,alpha)
    put.var.ncdf(ncout, gev_k, 	k)

    # define CF attributes
    att.put.ncdf(ncout,varid=0,'institution','CSIRO (Commonwealth Scientific and Industrial Research Organisation, Australia)') 
    att.put.ncdf(ncout,varid=0,'institute_id',"CSIRO")
    att.put.ncdf(ncout,varid=0,'experiment_id',scenario)
    att.put.ncdf(ncout,varid=0,'source',out_name)
    att.put.ncdf(ncout,varid=0,'project_id','CMIP5')
    att.put.ncdf(ncout,varid=0,'model_id',model)
    att.put.ncdf(ncout,varid=0,'parent_experiment_rip',run)
    att.put.ncdf(ncout,varid=0,'season',season)
    att.put.ncdf(ncout,varid=0,'analysis_period',paste(start,'-',end,sep=''))
    att.put.ncdf(ncout,varid=0,'GEV_fitting_method',fit_method)
    att.put.ncdf(ncout,varid=0,'origin', as.character(nc$origin))
    att.put.ncdf(ncout,varid=0,'product','output') 
    att.put.ncdf(ncout,varid=0,'title',paste(model,' return levels for ',var,sep=''))
    att.put.ncdf(ncout,varid=0,'creation_date',as.character(date()))
    #att.put.ncdf(ncout,varid=0,'calc_GEV,seasonal_revision',as.character(Version))
    att.put.ncdf(ncout,varid=0,'references', 'Please see http://www.cccma.ec.gc.ca/data/climdex/climdex.shtml for information regarding the ETCCDI database')
    close(ncout)
    print(paste('Name of output file: ',outfile,sep=''))
    
    for (Return_Period in c(2,5,10,20,50,100)){
        calc_RetLevel(nc_GEV,Return_Period,outfile,lon_dim,lat_dim)
    	}
}



################################### START ###########################################
args	<- commandArgs(TRUE)
season	<-args[1]	# season, can be one of 'ann,DJF,MAM,JJA,SON'
fit_method<- args[2]	# fitting method for GEV distribution, eg 'lmom','mle','pfit'
infile 	<-args[3]	# path to the model data
outfilename<-args[4]	# out name of netcdf file
#fit_method<- 'lmom'	# fitting method for GEV distribution, eg 'lmom','mle','pfit'
nboots<-1000		# number of boots for the bootstrapped K-S test, as a minimum use 1000

# for all variables EXCEPT sfcWindmax
#out_name<-(tail(strsplit(infile,'/')[[1]],1))
#model	<-tail(strsplit(out_name,'_')[[1]],4)[1]
#scenario<-tail(strsplit(out_name,'_')[[1]],4)[2]
#run	<-tail(strsplit(out_name,'_')[[1]],4)[3]
#grid	<-strsplit(tail(strsplit(out_name,'_')[[1]],4)[4],'.nc')[[1]]
#var 	<-strsplit(out_name,'_')[[1]][1]

# sfcWindmax
#out_name<-(tail(strsplit(infile,'/')[[1]],1))
#model	<-strsplit(out_name,'_')[[1]][3]
#scenario<-tail(strsplit(out_name,'_')[[1]],4)[1]
#run	<-tail(strsplit(out_name,'_')[[1]],4)[2]
#grid	<-strsplit(tail(strsplit(out_name,'_')[[1]],4)[4],'.nc')[[1]]
#var 	<-strsplit(out_name,'_')[[1]][1]

out_name<-(tail(strsplit(infile,'/')[[1]],1))
model	<-strsplit(out_name,'_')[[1]][3]
scenario<-tail(strsplit(out_name,'_')[[1]],4)[2]
run	<-tail(strsplit(out_name,'_')[[1]],4)[3]
grid	<-strsplit(tail(strsplit(out_name,'_')[[1]],4)[4],'.nc')[[1]]
var 	<-strsplit(out_name,'_')[[1]][1]

if (scenario == 'historical') {
    start<-c('1986')
    end<-c('2005')
    }
if (scenario != 'historical') {
    start <- c('2020','2040','2060','2080')
    end   <- c('2039','2059','2079','2099')
    # for sfcWindmax:
    #start <- c('2080')
    #end   <- c('2099')
    }
# Read in data
nc<-read_netcdf(infile,var)
if (sum(duplicated(nc$time)) > 1) {stop('Execution halted: Bad time axis')}

print(paste('Commencing GEV analysis for ',infile,' for scenario=',scenario,sep=''))

# Convert variable to seasonal maxima for input to L-moments analysis
outfile<-outfilename
nc_max<-calc_annual_max(nc,season)

#if (sum(is.na(nc_max))>0) {stop('Execution halted: missing data')}
# sum_time<-apply(nc_max,1:2,sum,na.rm=T)
# sum_lons<-apply(sum_time,2,sum,na.rm=T)
#if (min( apply( apply(nc_max,2:3,sum,na.rm=T), 1:2, sum, na.rm=T) ) < 1) {stop('Execution halted: Missing or zero values along one or more longitude')}

## Fit a GEV distribution to the data
for (i in 1:length(start)){
    nc_GEV <- calc_GEV(fit_method,nc_max,nc$time,start[i],end[i])
    tmpfile<-strsplit(outfilename,'1986-2005')[[1]]
    outfile<-paste(tmpfile[1],start[i],'-',end[i],tmpfile[2],sep='')
    print(paste('Writing to file: ',outfile,sep=''))
    write_nc(nc,nc_GEV,out_name)
    }


