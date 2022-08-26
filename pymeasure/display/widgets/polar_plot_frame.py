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

from faulthandler import disable
from locale import normalize
import logging

import re
from tkinter.tix import Tree
import pyqtgraph as pg

from ..polar_curves import ResultsPolarCurve, PolarCurve
from ..curves import Crosshairs
from ..Qt import QtCore, QtGui
from ...experiment import Procedure

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
import numpy as np
translate = QtCore.QCoreApplication.translate
import time

class PolarPlot(pg.PlotWidget):
    """ Plot widget that prints adjustable polar axis.
        This plot can be used to print user data contained in a PolarDataClass istance.
        It allows to print data on an absolute scale or print each curve according to its scale using the scale flag.
        The axis is automatically scaled according to the data visible on the plot.
    """
    PolarDataClass = PolarCurve
    def __init__(self, parent=None, outer_circle = 25, circles = 10, scale=False, scaling=0, degrees_step = 15, **kwargs):
        super().__init__(parent,**kwargs)
        self._plot = self.getPlotItem()
        self._degrees_step = degrees_step
        self._circles = circles
        self._outer_circle = outer_circle
        self._degrees_step = 15
        self._polar_plot_items = []
        self._scale = scale
        self._scaling = scaling
        self._setup_polar_plot()
        self._toBeUpdated = True
        
    def _setup_polar_plot(self):

        def _getTextAnchor(x,y):
            anchor = (0,0)
            if x >= 0 and y < 0:
                anchor = (0,0)
            elif x > 0 and y >= 0:
                anchor = (0,1)
            elif x <= 0 and y >= 0:
                anchor = (1,1)
            else:
                anchor = (1,0)
            return anchor

        def _getTextItem(text, anchor = (0,0), pos = (0,0), size = 11):
            x = pos[0]
            y = pos[1]
            
            textItem = pg.TextItem(anchor=anchor,text=text)
            font = QtGui.QFont("Times", size)
            color = QtGui.QColor(0, 0, 0, 255)
            textItem.setFont(font)
            textItem.setColor(color)
            textItem.setPos(x,y)
            return textItem
        
        if self.scale == False:
            scaling = 0
            normalize = self.outer_circle
        else:
            scaling = self.scaling
            normalize = 0
        
        for r in np.linspace(0, self.outer_circle, self.circles):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.1))
            self.addItem(circle)
            self._polar_plot_items.append(circle)
            text = _getTextItem("%.2f"%(r-normalize-scaling), anchor = (1,0), pos = (0,r), size = 10)
            self.addItem(text)
            self._polar_plot_items.append(text)

        # Insert lines for each angle and text
        limit = self.outer_circle
        for angle in range(0,180,self._degrees_step):
            x1 = (limit)*np.cos(np.deg2rad(angle))
            y1 = (limit)*np.sin(np.deg2rad(angle))
            x2 = (limit)*np.cos(np.deg2rad(angle + 180))
            y2 = (limit)*np.sin(np.deg2rad(angle + 180))
            text = _getTextItem("%d°"%angle, anchor = _getTextAnchor(x1,y1), pos = (x1,y1))
            self.addItem(text)
            self._polar_plot_items.append(text)
            text = _getTextItem("%d°"%(angle+180),anchor = _getTextAnchor(x2,y2), pos = (x2,y2))
            self.addItem(text)
            self._polar_plot_items.append(text)

            x = [x1, x2]
            y = [y1, y2]
            line = self.plot(x, y)
            self._polar_plot_items.append(line)


    def paintEvent(self,ev):
        # Ensure always the axis are scaled according to the data plotted
        max_init = -1000
        min_init = -1000
        max_range = max_init
        min_scaling = min_init
        for item in self._plot.items:
            if isinstance(item, self.PolarDataClass) or issubclass(item.__class__, self.PolarDataClass):
                if item.isVisible(): #and (item.x != item.y):
                    phi,radius,r_min,r_max = item.getPolarDataAndRange()
                    
                    if self.scale == False:
                        item.polar_offset = 0
                        # item.polar_offset = (30)
                        # print(item.polar_offset)
                    else:
                        item.polar_offset = max(self.scaling,item.polar_offset)
                    
                    item.updateData(phi,radius) # I'm sure item paint method is triggered.

                    # Find the polar range and the scaling to apply on the plot to get auto-scaling
                    polar_range = abs(max(abs(r_max - r_min),(r_max + item.polar_offset)))   
                    # polar_range = abs(max(30,(r_max + item.polar_offset)))      
                    if polar_range > max_range:
                        max_range = polar_range
                    
                    scaling = max(abs(r_min),item.polar_offset)
                    if scaling > min_scaling: 
                        min_scaling = scaling

        if min_scaling != min_init:
            self.scaling = min_scaling
        if max_range != max_init:
            self.outer_circle = max_range

        # Refresh the plot if there is something to change
        self.refresh_plot()    
        return super().paintEvent(ev)

    @property
    def outer_circle(self):
        return self._outer_circle

    @outer_circle.setter
    def outer_circle(self,circle):
        if circle != self._outer_circle:
            self._outer_circle = circle
            self._toBeUpdated = True

    @property
    def scaling(self):
        return self._scaling

    @scaling.setter
    def scaling(self,scaling):
        if scaling != self._scaling:
            self._scaling = scaling
            self._toBeUpdated = True
    
    @property
    def circles(self):
        return self._circles
    
    @circles.setter
    def circles(self,circles):
        if circles != self._circles:
            self._circles = circles
            self._toBeUpdated = True
    
    @property
    def degrees_step(self):
        return self.degrees_step
    
    @degrees_step.setter
    def degrees_step(self,step):
        if step != self._degrees_step:
            self._degrees_step = step
            self._toBeUpdated = True
    
    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self,scale):
        if scale != self._scale:
            self._scale = scale
            self._toBeUpdated = True
    
    def refresh_plot(self):
        if self._toBeUpdated == True:
            self._toBeUpdated = False
            for item in self._polar_plot_items:
                self.removeItem(item)
            self._setup_polar_plot()



class PolarPlotFrame(QtGui.QFrame):
    """ Combines a PyQtGraph Plot with Crosshairs. Refreshes
    the plot based on the refresh_time, and allows the axes
    to be changed on the fly, which updates the plotted data
    """

    LABEL_STYLE = {'font-size': '10pt', 'font-family': 'Arial', 'color': '#000000'}
    updated = QtCore.QSignal()
    ResultsClass = ResultsPolarCurve
    x_axis_changed = QtCore.QSignal(str)
    y_axis_changed = QtCore.QSignal(list)

    def __init__(self, x_axis=None, y_axis=None, refresh_time=0.2, check_status=True, parent=None):
        super().__init__(parent)
        self._theta = x_axis
        self._phi = y_axis
        self._theta_range = range(0,180)
        self._phi_range = range(0,360)
        self._filter = self._theta
        self.refresh_time = refresh_time
        self.check_status = check_status
        self._limit_color = 1
        self._setup_ui()
        self._limit_curves = [] 
        self.menu = self.plot_widget.getViewBox().menu
        viewLimits = QtGui.QAction(translate("ViewBox", "Show Limits"), self)
        viewLimits.triggered.connect(self.showLimits)
        self.menu.addAction(viewLimits)
        hideLimits = QtGui.QAction(translate("ViewBox", "Hide Limits"), self)
        hideLimits.triggered.connect(self.hideLimits)
        self.menu.addAction(hideLimits)
        self.change_x_axis(x_axis)
        if isinstance(y_axis, str):
            y_axis = [y_axis,]
        self.change_y_axis(y_axis)      
        
               
    def _setup_ui(self):
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: #fff")
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Sunken)
        self.setMidLineWidth(1)
        self._normalize = False
        self.plot_widget = PolarPlot(self, outer_circle = 5, scale = not(self._normalize), background='#ffffff')
        self.coordinates = QtGui.QLabel(self)
        self.coordinates.setMinimumSize(QtCore.QSize(0, 20))
        self.coordinates.setStyleSheet("background: #fff")
        self.coordinates.setText("")
        self.coordinates.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)

        self.cut = QtGui.QLabel(self)
        self.cut.setMinimumSize(QtCore.QSize(0, 20))
        self.cut.setFont(QtGui.QFont('Arial', 12))
        self.cut.setStyleSheet("background: #fff")
        self.cut.setText("")
        self.cut.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        

        self.plot = self.plot_widget.getPlotItem()
        self.plot.setAspectLocked(lock=True, ratio=1)

        vbox = QtGui.QVBoxLayout(self)

        vbox1 = QtGui.QVBoxLayout()
        self.filterLabel = QtGui.QLabel("Select %s:"%self._filter)
        self.filterSB = QtGui.QSpinBox()
        self.filterSB.setRange(0, 180)
        if self._filter == self._theta:
            self.filterSB.setSingleStep(self._theta_range.step)
        elif self._filter == self._phi:
            self.filterSB.setSingleStep(self._phi_range.step)
        self.filterSB.setValue(0)
        self.filterSB.valueChanged.connect(self.updateResultFilter)
        vbox1.addWidget(self.filterLabel)
        vbox1.addWidget(self.filterSB)
        vbox.addLayout(vbox1)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.plot_widget)

        self.normalize_cb = QtGui.QCheckBox("Normalize")
        self.normalize_cb.setChecked(self._normalize)
        self.normalize_cb.stateChanged.connect(self.set_normalize)
        vbox.addWidget(self.normalize_cb)
        vbox.addLayout(hbox)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.cut)
        hbox.addWidget(self.coordinates)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.crosshairs = Crosshairs(self.plot,
                                     pen=pg.mkPen(color='#AAAAAA', style=QtCore.Qt.DashLine))
        self.crosshairs.coordinates.connect(self.update_coordinates)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_curves)
        self.timer.timeout.connect(self.crosshairs.update)
        self.timer.timeout.connect(self.updated)
        self.timer.start(int(self.refresh_time * 1e3))

    def insertLimit(self, limit, visible=True):
        phi = np.array(np.arange(0,365,5))
        r = np.array([limit]*len(phi)) #TBD
        alpha = 255 * int(visible)
        curve = PolarCurve("Phi","Radius", xData=phi, yData=r,pen=pg.mkPen(color=pg.intColor(self._limit_color,alpha=alpha),width=2),clickable = True)
        self.plot.addItem(curve)
        curve.show()
        self._limit_color += 3
        self._limit_curves.append(curve)

    def showLimits(self):
        for limit in self._limit_curves:
            limit.show()
    
    def hideLimits(self):
        for limit in self._limit_curves:
            limit.hide()

    def updateFilters(self,filter):
        filter_label = list(filter.keys())[0]
        filter_value= filter[filter_label]
        if filter_label == self._theta or filter_label == self._phi:
              self.cut.setText("%s: %s°"%(filter_label,filter_value))
            

    def updateResultFilter(self, value):
        for item in self.plot.items:
            if isinstance(item, self.ResultsClass):
                item.results.filters[self._filter] = value

    def set_normalize(self,state):
        self.plot_widget.scale = not(state)

    def update_coordinates(self, x, y):
        scale = int(self.plot_widget.scale)
        r = np.sqrt(x*x + y*y) - (self.plot_widget.scaling*scale) - (scale^1)*(self.plot_widget.outer_circle)
        theta = np.rad2deg(np.arctan2(y,x)) % 360
        self.coordinates.setText(f"({r:g}, {theta:g})")

    def update_curves(self):
        for item in self.plot.items:
            if isinstance(item, self.ResultsClass):
                item.update_data()
                self.updateFilters({item.key:item.filters[item.key]})

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

        if axis == self._theta:
            self.filterLabel.setText("Select %s:"%self._phi)
            self._filter = self._phi
            self.filterSB.setRange(self._phi_range.start,self._phi_range.stop)
            self.filterSB.setSingleStep(self._phi_range.step)

        elif axis == self._phi:
            self.filterLabel.setText("Select %s:"%self._theta)
            self._filter = self._theta
            self.filterSB.setRange(self._theta_range.start,self._theta_range.stop)
            self.filterSB.setSingleStep(self._theta_range.step)
        self.updateResultFilter(self.filterSB.value())
        
        for item in self.plot.items:
            if isinstance(item, self.ResultsClass):
                item.x = axis
                item.key = self._filter
                item.update_data()
        label, units = self.parse_axis(axis)
        self.plot.setLabel('bottom', label, units=units, **self.LABEL_STYLE)
        self.x_axis = axis
        self.x_axis_changed.emit(axis)
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')

    def change_y_axis(self, axis_list):
        label_list = []
        units = None
        for axis in axis_list:
            label, units = self.parse_axis(axis)
            label_list.append(label)
        label = ",".join(label_list)
        self.plot.setLabel('left', label, units=units, **self.LABEL_STYLE)
        self.y_axis = axis_list
        self.y_axis_changed.emit(list(axis_list))
        self.plot.hideAxis('bottom')
        self.plot.hideAxis('left')
