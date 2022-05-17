# +
'''
Copyright Jay Unruh, Stowers Institute 2022
License GPLv3:
'''
import numpy as np
import pandas as pd
import napari
from magicgui import magicgui
from napari.types import LabelsData,ImageData,PointsData
from . import ipfunctions as ipf
import enum

#def makeSegWidget(seglayer:ImageData=None,backlayer:PointsData=None,viewer=None):
def makeSegWidget(viewer=None):

    if(viewer is None):
        viewer=napari.Viewer

    class Choice(enum.Enum):
        Max='Max'
        Percentile='Percentile'
        Avg='Avg'
        Identity='Identity'

    class Stats(enum.Enum):
        Avg='Avg'
        Median='Median'
        Std='Std'
        Max='Max'

    @magicgui(call_button='Update',
             threshfrac={'min':0.0,'step':0.05},
             maxarea={'max':1000000,'step':10},
             percentile={'max':100.0,'step':0.5})
    def outlineObjects(measurelayer:ImageData,seglayer:ImageData,backlayer:PointsData,
                       smoothstd:float=3,threshfrac:float=0.2,threshstat=Choice.Max,
                       minarea:float=10,maxarea:float=10000,percentile:float=99.0,
                       measurestat=Stats.Avg,meascirc:bool=False,circrad:int=4,
                       outmeasurement:bool=False)->LabelsData:
        if(seglayer is None):
            return None
        else:
            simg=seglayer
        if(backlayer is not None):
            backcoords=backlayer[0]
        else:
            backcoords=ipf.findBackground(simg,3,40,200,30)
        print('backcoords:'+str(backcoords))
        backavg=ipf.measureCirc(simg,int(backcoords[0]),int(backcoords[1]),40,np.mean)
        subimg=simg-backavg
        if(meascirc):
            nucdata=ipf.findCirc(subimg,smstd=smoothstd,threshfrac=threshfrac,threshstat=threshstat.value,
                              threshpercentile=percentile,minarea=minarea,maxarea=maxarea,circgap=2,circrad=circrad)
        else:
            nucdata=ipf.findNuclei(subimg,smstd=smoothstd,threshfrac=threshfrac,threshstat=threshstat.value,
                          threshpercentile=percentile,minarea=minarea,maxarea=maxarea)
        return nucdata

    @outlineObjects.called.connect
    def printMeasurement():
        #measure the objects and their areas
        #put the measurements in measdf
        if(outlineObjects.outmeasurement.value):
            nuclabels=viewer.layers[-1].data
            measimg=outlineObjects.measurelayer.value
            #print(measimg)
            if(outlineObjects.backlayer is None):
                return
            backcoords=outlineObjects.backlayer.value[0]
            print('back coords:'+str(backcoords))
            stat=outlineObjects.measurestat.value.value
            #print('measuring:'+stat)
            print('measurement commands:')
            print('segsub=segimg-ipfunctions.measureCirc(nucimg,'+str(backcoords[0])+','+str(backcoords[1])+',40,np.mean)')
            tsm=str(outlineObjects.smoothstd.value)
            tfrac=str(outlineObjects.threshfrac.value)
            tstat=str(outlineObjects.threshstat.value.value)
            tper=str(outlineObjects.percentile.value)
            mina=str(outlineObjects.minarea.value)
            maxa=str(outlineObjects.maxarea.value)
            crad=str(outlineObjects.circrad.value)
            if(outlineObjects.meascirc.value):
                print('seglabels=ipfunctions.findCirc(segsub,'+tsm+','+tfrac+','+tstat+','+tper+','+mina+','+maxa+','+crad+')')
            else:
                print('seglabels=ipfunctions.findNuclei(segsub,'+tsm+','+tfrac+','+tstat+','+tper+','+mina+','+maxa+')')
            print('measdf=ipfunctions.getMeasurement(measimg,nuclabels,'+repr(list(backcoords))+',\"'+stat+'\")')

            if(outlineObjects.meascirc.value):
                print('output is in segwidget.circdf')
                global circdf
                circdf=ipf.getMeasurement(measimg,nuclabels,backcoords,stat)
                print(circdf.head())
            else:
                print('output is in segwidget.measdf')
                global measdf
                measdf=ipf.getMeasurement(measimg,nuclabels,backcoords,stat)
                print(measdf.head())

    viewer.window.add_dock_widget(outlineObjects)
    outlineObjects.result_name="Segmentation_Labels"
    outlineObjects()
    napari.run()
    return viewer
