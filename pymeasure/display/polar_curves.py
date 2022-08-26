#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2022 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import logging
from turtle import update

import numpy as np
import pandas as pd
import pyqtgraph as pg

from .Qt import QtCore, QtGui
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.opengl import (GLViewWidget, 
                              MeshData,
                              GLMeshItem,
                              GLGridItem,
                              GLLinePlotItem,
                              GLAxisItem,
                              GLScatterPlotItem,
                              GLSurfacePlotItem,
                              GLMeshItem,
)
from pyqtgraph import colormap, ColorBarItem, LegendItem

from stl import mesh
from OpenGL.GL import * # glEnable, glHint, glBegin, glColor4f, glVertex3f, glEnd
import pytransform3d.coordinates as pc


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

def elaz2abc(el,az,r):
    #elevation over azimuth
    #(el,az) (rad)-->(a,b,c) direction cosine
    az1=-az+np.pi/2
    # az1 = az
    a=r*np.sin(az1)
    b=r*np.cos(az1)*np.sin(el)
    c=r*np.cos(az1)*np.cos(el)
    return np.array([a, b, c]).T

def Rx(theta):
  return np.matrix([[ 1, 0           , 0           ],
                   [ 0, np.cos(theta),-np.sin(theta)],
                   [ 0, np.sin(theta), np.cos(theta)]])

def Ry(theta):
  return np.matrix([[ np.cos(theta), 0, np.sin(theta)],
                   [ 0           , 1, 0           ],
                   [-np.sin(theta), 0, np.cos(theta)]])


def Rz(theta):
  return np.matrix([[ np.cos(theta), -np.sin(theta), 0 ],
                   [ np.sin(theta), np.cos(theta) , 0 ],
                   [ 0           , 0            , 1 ]])

class Results3DMesh(GLMeshItem):
    def __init__(self, results, x, y, force_reload=False, y_offset=0, **kwargs):
        super().__init__(**kwargs)
        self.results = results
        self.x, self.y = x, y
        self.force_reload = force_reload
        self.y_offset = y_offset
        md = MeshData.sphere(rows=10, cols=20, radius=0.1) # avoid warning if meshdata is None
        self.setMeshData(meshdata=md)
    
   
    def update_data(self):
        if self.force_reload:
            self.results.reload()
        data3d = self.results.data.copy()
        if data3d.empty != True and not (self.y in ["Theta","Phi"]):
            data3d = pd.DataFrame({'Theta':data3d["Theta"],"Phi":data3d["Phi"],self.y: data3d[self.y]})
            data3d.columns = data3d.columns.str.replace(self.y, 'magnitude')
            # self.y_offset = self.results.get_stat_data("min").min()
            self.y_offset = min(self.y_offset,data3d['magnitude'].min())
            data3d['magnitude'] += abs(self.y_offset)
            data3d=data3d.reindex(columns=['magnitude', 'Theta', 'Phi'])
            data3d['Phi'] = np.radians(data3d['Phi'])
            data3d['Theta'] = np.radians(data3d['Theta'])

            phi_size = list(data3d['Theta']).count(0.0) # cols
            theta_size = list(data3d['Phi']).count(0.0) # rows
            verts = np.empty((theta_size, phi_size, 3), dtype=float)
            rows = theta_size - 1
            cols = phi_size
            try:
                # data3d_cart=pc.cartesian_from_spherical(data3d.to_numpy(copy=True))
                data3d_cart = elaz2abc(data3d['Phi'],data3d['Theta'],data3d['magnitude'])
                # data3d_cart = data3d_cart*Rz(-np.pi/2)
                verts[...,2] = data3d_cart[:,2].reshape(rows+1, cols)
                verts[...,0] = data3d_cart[:,0].reshape(rows+1, cols)
                verts[...,1] = data3d_cart[:,1].reshape(rows+1, cols)

                verts = verts.reshape((rows+1)*cols, 3)[cols-1:-(cols-1)]  ## remove redundant vertexes from top and bottom
                faces = np.empty((rows*cols*2, 3), dtype=np.uint)
                rowtemplate1 = ((np.arange(cols).reshape(cols, 1) + np.array([[0, 1, 0]])) % cols) + np.array([[0, 0, cols]])
                rowtemplate2 = ((np.arange(cols).reshape(cols, 1) + np.array([[0, 1, 1]])) % cols) + np.array([[cols, 0, cols]])
                for row in range(rows):
                    start = row * cols * 2 
                    faces[start:start+cols] = rowtemplate1 + row * cols
                    faces[start+cols:start+(cols*2)] = rowtemplate2 + row * cols
                faces = faces[cols:-cols]  ## cut off zero-area triangles at top and bottom

                # adjust for redundant vertexes that were removed from top and bottom
                vmin = cols-1
                faces[faces<vmin] = vmin
                faces -= vmin  
                vmax = verts.shape[0]-1
                faces[faces>vmax] = vmax

                md = MeshData(vertexes=verts, faces=faces)
                cm = colormap.get('CET-R4')

                magnitudes = np.array([np.sqrt(np.dot(c,c)) for c in md.vertexes()])
                magnitudes = magnitudes/max(magnitudes)
                colors = cm.map(magnitudes, mode=colormap.ColorMap.FLOAT)

                md.setVertexColors(colors)
                self.setMeshData(meshdata=md)
            except:
                pass


class PolarCurve(pg.PlotCurveItem):
    """ Creates a curve loaded dynamically from a file through the Results object. The data can
    be forced to fully reload on each update, useful for cases when the data is changing across
    the full file instead of just appending.
    """
    def __init__(self, x,y, xData = None, yData = None, normalize=False, norm_value = 0, polar_offset=0, **kwargs):
    # def __init__(self, **kwargs):
        super().__init__(xData, yData, **kwargs)
        # self.pen = kwargs.get('pen', None)
        # self.shadow_pen = kwargs.get('shadowPen', None)
        self.x, self.y = x, y
        self.polar_offset = polar_offset
        self.normalize = normalize # To be used?
        self.norm_value = norm_value # To be used?
        self.menu = None

    # Get polar data and polar range
    # One method to not repeat getData two times for data, min and max
    def getPolarDataAndRange(self):
        phi, radius = super().getData()
        r_min = 0
        r_max = 0
        if radius.size != 0:
            r_max = radius.max()
            if radius[radius<0].size != 0:
                r_min = radius.min()
        return phi, radius, r_min, r_max
    
    # Get cartesian data necessary to plot a curve since polar plot is not supported
    def getCartData(self):
        phi, radius, r_min, r_max = self.getPolarDataAndRange()
        radius = radius + max(abs(r_min), abs(self.polar_offset))
        y = radius*np.sin((phi*np.pi/180))
        x = radius*np.cos((phi*np.pi/180))      
        return x,y
    
    # OVERRIDE parent's method to create bounding rect and path to be drawn
    # Wrapping of getCartData
    def getData(self):
        return self.getCartData()

    def getContextMenus(self, event=None):
        if self.menu is None:
            self.menu = QtWidgets.QMenu()
            self.menu.setTitle(" options..")
            
            hide = QtGui.QAction("Hide", self.menu)
            hide.triggered.connect(self.hide)
            self.menu.addAction(hide)
        return self.menu

    def raiseContextMenu(self, ev):
        menu = self.getContextMenus()
        
        # Let the scene add on to the end of our context menu
        # (this is optional)
        menu = self.scene().addParentContextMenus(self, menu, ev)
        
        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))
        return True
    
    def mouseClickEvent(self, ev):
        
        # Disable any shadow pen if any
        # if self.opts.get('shadowPen', None) != None:
        #     self.opts.get('shadowPen').setWidth(0)

        if not self.clickable:
            return
            
        if self.mouseShape().contains(ev.pos()) and ev.button() == QtCore.Qt.MouseButton.RightButton:
            # self.setShadowPen('r',width=4)
            ev.accept()
            self.raiseContextMenu(ev)
            self.sigClicked.emit(self, ev)


class ResultsPolarCurve(PolarCurve):#(pg.PlotCurveItem):
    """ Creates a curve loaded dynamically from a file through the Results object. The data can
    be forced to fully reload on each update, useful for cases when the data is changing across
    the full file instead of just appending.
    """
    updateFilter = QtCore.QSignal(dict)
    def __init__(self, results, x, y, force_reload=False, normalize=False, norm_value = 0, polar_offset=0, **kwargs):
    # def __init__(self, **kwargs):
        super().__init__(x,y,normalize=False, norm_value=0, polar_offset=0,**kwargs)
        self.results = results
        self.pen = kwargs.get('pen', None)
        self.force_reload = force_reload
        self.filters = {}
        self.key = "Theta"


    def _signalFilterChanged(self,key,filter):
        if not (key in self.filters):
            self.filters[key] = filter
            # self.updateFilter.emit({key:filter})
        else:
            if self.filters[key] != filter:
                self.filters[key] = filter
                # self.updateFilter.emit({key:filter}) 

    def update_data(self):
        """Updates the data by polling the results"""
        if self.force_reload:
            self.results.reload()
        data = self.results.data  # get the current snapshot

        # Apply filters if any
        data_filtered = data
        # for key in self.results.filters:
        #     try:
        #         data[key]
        #     except:
        #         continue
        #     filter = self.results.filters[key]
        #     self._signalFilterChanged(key,filter)
        #     if(isinstance(filter,str)):
        #         if ("gt" in filter):
        #             filter = float(filter.replace("gt",""))
        #             data_filtered = data_filtered[data_filtered[key]>filter]
        #         elif ("ge" in filter):
        #             filter = float(filter.replace("ge",""))
        #             data_filtered = data_filtered[data_filtered[key]>=filter]
        #         elif ("lt" in filter):
        #             filter = float(filter.replace("lt",""))
        #             data_filtered = data_filtered[data_filtered[key]<filter]
        #         elif ("le" in filter):
        #             filter = float(filter.replace("le",""))
        #             data_filtered = data_filtered[data_filtered[key]<=filter]
        #     else:      
        #         data_filtered = data_filtered[data_filtered[key]==filter]
        try:
            # data[self.key]
            filter = self.results.filters[self.key]
            data_filtered = data_filtered[data_filtered[self.key]==filter]
            self._signalFilterChanged(self.key,filter)
        except:
            self._signalFilterChanged(self.key,"/")

        # Set Polar x-y data
        self.setData(data_filtered[self.x].to_numpy(), data_filtered[self.y].to_numpy())