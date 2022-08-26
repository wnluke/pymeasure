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

from locale import normalize
import logging

import re
import pyqtgraph as pg

from ..polar_curves import Results3DMesh
from ..Qt import QtCore, QtGui
from ...experiment import Procedure

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
import numpy as np

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui, QtWidgets
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
import pandas as pd

from OpenGL.GL import * # glEnable, glHint, glBegin, glColor4f, glVertex3f, glEnd
import pytransform3d.coordinates as pc


class MyGLAxisItem(GLAxisItem):
    """
    **Bases:** :class:`GLGraphicsItem <pyqtgraph.opengl.GLGraphicsItem>`
    
    Displays three lines indicating origin and orientation of local coordinate system. 
    
    """
    
    def paint(self):

        
        self.setupGLState()
        # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glEnable( GL_BLEND )
        # glEnable( GL_ALPHA_TEST )
        if self.antialias:
            glEnable(GL_LINE_SMOOTH)
            glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
            
        glBegin( GL_LINES )
        
        x,y,z = self.size()
        glColor4f(0, 0, 1, .6)  # z is blue
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, z)

        glColor4f(0, 1, 0, .6)  # y is green
        glVertex3f(0, 0, 0)
        glVertex3f(0, y, 0)

        glColor4f(1, 0, 0, .6)  # x is red
        glVertex3f(0, 0, 0)
        glVertex3f(x, 0, 0)
        glEnd()

class PolarPlotFrame3D(QtWidgets.QFrame):
    LABEL_STYLE = {'font-size': '10pt', 'font-family': 'Arial', 'color': '#000000'}
    updated = QtCore.QSignal()
    ResultsClass = Results3DMesh
    x_axis_changed = QtCore.QSignal(str)
    y_axis_changed = QtCore.QSignal(list)
    limits = {
            "FCC Limit": -41.2,
            "ETSI Limit": -30,
            }

    def __init__(self, x_axis=None, y_axis=None, refresh_time=0.2, check_status=True, parent=None, model_file = None):
        super().__init__(parent)
        self.model_file = model_file
        self.refresh_time = refresh_time
        self.check_status = check_status
        self.polar_axis_max_circle = 25
        self.polar_axis_min_offset = 1000
        self._setup_ui()
        

        
    def _setup_ui(self):


        vbox = QtWidgets.QVBoxLayout(self)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_curves)
        self.timer.timeout.connect(self.updated)
        self.timer.start(int(self.refresh_time * 1e3))

        self.plot= GLViewWidget(self)
        self.plot.setCameraPosition(distance=100)
 
        self.hbox = QtWidgets.QHBoxLayout()

        self._normalize = True
        self.normalize_cb = QtWidgets.QCheckBox("Normalize")
        self.normalize_cb.setChecked(self._normalize)
        self.normalize_cb.stateChanged.connect(self.set_normalize)
        vbox.addWidget(self.normalize_cb)

        self.polar_axis_limit_circle = {}
        # for limit in self.limits.keys():
        #     limit_cb = QtWidgets.QCheckBox(limit)
        #     limit_cb.setChecked(True)
        #     self.insertLimit(self.limits[limit])
        #     limit_cb.stateChanged.connect(self.showLimit)
        #     self.hbox.addWidget(limit_cb)

        body3D_cb = QtWidgets.QCheckBox("Show 3D body")
        body3D_cb.setChecked(True)
        self.hbox.addWidget(body3D_cb)
        from stl import mesh
        # import pywavefront
        # stl_mesh = mesh.Mesh.from_file("BLUENRG_LPS_QFN32_SMD_EMC_2L.stl")
        # stl_mesh.translate(np.array([15.45,-27.93,0]))
        # stl_mesh.rotate([1, 0, 0], -np.pi/2)
        # stl_mesh.rotate([0, 0, 1], np.pi)
        
        # # stl_mesh = mesh.Mesh.from_file("STEVAL_IDB013V1.stl")
        # vehicle = scene = pywavefront.Wavefront("STEVAL_IDB012V1_test.obj", strict=False, create_materials=True, collect_faces=True)#, cache=True) # Cache is currently not working?!
        # # Conversion - Pywavefront to PyQtGraph GLMeshItem
        # vertices_array = np.asarray(vehicle.vertices)
        # faces_array = []
        # for mesh_lists in vehicle.mesh_list:
        #     for faces in mesh_lists.faces:
        #         faces_array.append(np.array([faces[0],faces[1],faces[2]]))
        # faces_array = np.asarray(faces_array)
        # # Plotting the data in PyQtGraph
        # mesh_data = MeshData(vertexes=vertices_array, faces=faces_array)
        # # vehicleGL = GLMeshItem(meshdata=vehicleMesh, shader='shaded',drawEdges=False,  smooth=True)

        if self.model_file != None:
            stl_mesh = mesh.Mesh.from_file(self.model_file)
            stl_mesh.translate(np.array([-40,-27.5,0]))
            stl_mesh.rotate([0, 0, 1], np.pi/2)
            stl_mesh.rotate([1, 0, 0], np.pi/2)

        points = stl_mesh.points.reshape(-1, 3)
        faces = np.arange(points.shape[0]).reshape(-1, 3)
        mesh_data = MeshData(vertexes=points, faces=faces)
        mesh = GLMeshItem(meshdata=mesh_data, smooth=True, drawFaces=True, shader='shaded',drawEdges=False, edgeColor=(0, 1, 0, 1))
        # mesh.scale(100,100,100)
        body3D_cb.stateChanged.connect(lambda state : mesh.setVisible(state))
      

        # mesh.scale(0.5,0.5,0.5)
        self.plot.addItem(mesh)

        vbox.addLayout(self.hbox)

        axis = MyGLAxisItem(QtGui.QVector3D(50,50,50), glOptions='opaque')
        g = GLGridItem()
        g.scale(10, 10, 1)
        
        self.plot.addItem(axis)
        self.plot.addItem(g)

        vbox.addWidget(self.plot)
        self.setLayout(vbox)
    
    def set_normalize(self,state):
        for item in self.plot.items:
            if isinstance(item, self.ResultsClass):
                if state:
                    item.y_offset = 0
                else:
                    item.y_offset = self.polar_axis_min_offset
                item.update_data()


    def insertLimit(self, limit):
        for i in range(self.hbox.count()):
            widget = self.hbox.itemAt(i).widget()
            if isinstance(widget,QtWidgets.QCheckBox):
                if str(widget.text()) == str(limit):
                    return
        limit_cb = QtWidgets.QCheckBox(str(limit))
        limit_cb.setChecked(True)
        limit_cb.stateChanged.connect(self.showLimit)
        self.hbox.addWidget(limit_cb)

        if limit < self.polar_axis_min_offset:
            self.polar_axis_min_offset = limit #- 5 #to avoid to create a circle with radius 0
        r = limit + abs(self.polar_axis_min_offset)
        limit_sphere = GLMeshItem(meshdata=MeshData.sphere(rows=50, cols=100, radius=r), color = (1.,1.,1.,.5) )
        # limit_sphere.setGLOptions('additive')
        self.plot.addItem(limit_sphere)
        self.polar_axis_limit_circle[limit_cb] = limit_sphere
    

    def updateLimit(self,limit):
        r = float(limit.text())
        r = r + abs(self.polar_axis_min_offset)
        md=MeshData.sphere(rows=10, cols=20, radius=r)
        self.polar_axis_limit_circle[limit].setMeshData(meshdata=md)


    def showLimit(self, state):
        # cbutton = self.sender()
        # limit = self.limits[cbutton.text()]
        item = self.polar_axis_limit_circle[self.sender()]
        if state:
            item.show()
        else:
            item.hide()

    def update_curves(self):
        min_offset = 1000
        for item in self.plot.items:
            if isinstance(item, self.ResultsClass):

                if item.y_offset < min_offset:
                    min_offset = item.y_offset
                
                # print(item.y_offset)
                if self.check_status:
                    if item.results.procedure.status == Procedure.RUNNING:
                        item.update_data()
                else:
                    item.update_data()

        if min_offset < self.polar_axis_min_offset:
            self.polar_axis_min_offset = (min_offset)
            for limit in self.polar_axis_limit_circle:
                self.updateLimit(limit)
                    

    def parse_axis(self, axis):
        """ Returns the units of an axis by searching the string
        """
        units_pattern = r"\((?P<units>\w+)\)"
        try:
            match = re.search(units_pattern, axis)
        except TypeError:
            match = None

        if match:
            if 'units' in match.groupdict():
                label = re.sub(units_pattern, '', axis)
                return label, match.groupdict()['units']
        else:
            return axis, None

    def change_x_axis(self, axis):
        for item in self.plot.items:
            if isinstance(item, self.ResultsClass):
                item.x = axis
                item.update_data()
        
        label, units = self.parse_axis(axis)
        # self.plot.setLabel('bottom', label, units=units, **self.LABEL_STYLE)
        self.x_axis = axis
        self.x_axis_changed.emit(axis)
        # self.plot.hideAxis('bottom')
        # self.plot.hideAxis('left')


    def change_y_axis(self, axis_list):
        label_list = []
        units = None
        for axis in axis_list:
            label, units = self.parse_axis(axis)
            label_list.append(label)
        label = ",".join(label_list)
        # self.plot.setLabel('left', label, units=units, **self.LABEL_STYLE)
        self.y_axis = axis_list
        self.y_axis_changed.emit(list(axis_list))
        # self.plot.hideAxis('bottom')
        # self.plot.hideAxis('left')