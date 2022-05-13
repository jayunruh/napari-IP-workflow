# +
'''
Copyright Jay Unruh, Stowers Institute 2022
License GPLv2: 
'''
import numpy as np
import pandas as pd
import napari
from magicgui import magicgui
from napari.types import LabelsData,ImageData
import ipfunctions as ipf
import enum

def makeSegWidget(seglayer,backlayer,viewer=None):
    
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
             maxarea={'max':1000000,'step':10})
    def outlineObjects(measurelayer:ImageData,smoothstd:float=3,threshfrac:float=0.2,threshstat=Choice.Max,
                       minarea:float=10,maxarea:float=10000,percentile:float=0.99,
                       measurestat=Stats.Avg,outmeasurement:bool=False)->LabelsData:
        backcoords=backlayer.data[0]
        #print('backcoords:'+str(backcoords))
        simg=seglayer.data
        backavg=ipf.measureCirc(simg,backcoords[0],backcoords[1],40,np.mean)
        subimg=simg-backavg
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
            backcoords=backlayer.data[0]
            print('back coords:'+str(backcoords))
            stat=outlineObjects.measurestat.value.value
            #print('measuring:'+stat)
            print('measurement command:')
            print('measdf=ipwidgets.getMeasurement(measimg,nuclabels,'+repr(list(backcoords))+',\"'+stat+'\")')
            global measdf
            measdf=ipf.getMeasurement(measimg,nuclabels,backcoords,stat)
            print(measdf.head())
    
    
    viewer.window.add_dock_widget(outlineObjects)
    outlineObjects.result_name="Nuclear_Labels"
    outlineObjects()
    napari.run()
    return viewer
