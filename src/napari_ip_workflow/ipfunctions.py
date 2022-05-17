# +
'''
Copyright Jay Unruh, Stowers, 2022
License: GPLv3:
'''
import numpy as np
import scipy.ndimage as ndi
import pandas as pd
import skimage.segmentation as sks

def getCircMask(xc,yc,rad,width,height):
    xs,ys=np.meshgrid(np.arange(width),np.arange(height))
    return ((xs-xc)**2+(ys-xc)**2)<=(rad**2)

def measureCirc(img,xc,yc,rad,measfunc):
    return measfunc(img[getCircMask(xc,yc,rad,img.shape[1],img.shape[0])])

def findBackground(timg,smstd,ballrad,border,measrad):
    #now find the background of a multichannel image
    #finds the mininum of a boxcar filter over the image excluding the border
    #start by gaussian filtering
    #note if there is a transmitted light channel it should be removed first
    img=timg
    if(img.ndim<3):
        img=np.array([timg])
    nch=img.shape[0]
    smoothed=[ndi.gaussian_filter(img[i],sigma=smstd,mode='reflect') for i in range(nch)]
    mins=[smoothed[i].min() for i in range(nch)]
    print('sm chan mins: '+str(mins))
    summed=smoothed[0]-mins[0]
    for i in range(1,nch):
        summed+=smoothed[i]-mins[i]
    minfilt=ndi.uniform_filter(summed,size=2*ballrad,mode='reflect')
    minpos=np.argmin(minfilt[border:-border,border:-border])
    print('flat min index:'+str(minpos))
    width2=img.shape[2]-2*border
    miny=int(minpos/width2)
    minx=minpos-miny*width2
    miny=miny+border
    minx=minx+border
    #now measure the background in all the channels
    backlab=getCircMask(minx,miny,measrad,img.shape[2],img.shape[1])
    backavg=[img[i][backlab].mean() for i in range(nch)]
    return minx,miny,backavg,minfilt,summed

def findNuclei(nucimg,smstd=3,threshfrac=0.25,threshstat='Max',threshpercentile=99.0,minarea=10,maxarea=1e+6):
    #takes a nuclear image and thresholds it (fraction of max, percentile, and avg)
    #stats=['Max','Percentile','Avg','Identity']
    stats={'Max':np.max,'Percentile':(lambda x:np.percentile(x,threshpercentile)),
           'Avg':np.mean,'Identity':(lambda x:1.0)}
    #statfuncs=[np.max,np.percentile,np.mean,np.copy]
    #statidx=stats.index(threshstat)
    smoothed=ndi.gaussian_filter(nucimg,sigma=smstd,mode='reflect')
    statval=stats[threshstat](smoothed)
    threshval=threshfrac*statval
    #find the objects
    objects,nobj=ndi.label(smoothed>threshval)
    #filter out the ones that are too big or too small
    areas=ndi.sum(np.ones(objects.shape),objects,range(1,nobj))
    filtered=np.where((areas<minarea) | (areas>maxarea))[0]+1
    for idx in filtered:
        objects[objects==idx]=0.0
    #now filter out the ones on the edges
    edgevals=list(objects[0,:])+list(objects[1:,0])+list(objects[1:,-1])+list(objects[-1,1:-1])
    edgeidx=np.unique(edgevals)
    for idx in edgeidx:
        if(idx!=0.0):
            objects[objects==idx]=0.0
    #refind the objects
    objects,nobj=ndi.label(objects>0.0)
    return objects

def findCirc(nucimg,smstd=3,threshfrac=0.25,threshstat='Max',threshpercentile=99.0,
    minarea=10,maxarea=1e+6,circgap=2,circrad=4):
    labels=findNuclei(nucimg,smstd,threshfrac,threshstat,threshpercentile,minarea,maxarea)
    gapped=sks.expand_labels(labels,circgap)
    circ=sks.expand_labels(gapped,circrad)
    circ[gapped!=0.0]=0.0
    return circ

def getMeasurement(img,labels,backcoords,statfunc='Avg',getareas=True):
    stats={'Avg':np.mean,'Median':np.median,
           'Std':np.std,'Max':np.max}
    nobj=int(labels.max())
    backavg=measureCirc(img,backcoords[1],backcoords[0],40,np.mean)
    meassub=img-backavg
    #stats=ndi.mean(img,labels,range(1,nobj))
    measstats=ndi.labeled_comprehension(meassub,labels,range(1,nobj),stats[statfunc],float,0)
    if(getareas):
        areas=ndi.sum(np.ones(labels.shape),labels,range(1,nobj))
        return pd.DataFrame({'stat':measstats,'area':areas})
    else:
        return pd.DataFrame({'stat':measstats})
