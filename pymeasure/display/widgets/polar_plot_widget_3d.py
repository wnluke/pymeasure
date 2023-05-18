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

import pyqtgraph as pg

from ..Qt import QtCore, QtGui
from .tab_widget import TabWidget
from .plot_widget import CheckableComboBox
from ..polar_curves import Results3DMesh
from .polar_plot_frame_3d import PolarPlotFrame3D
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class PolarPlotWidget3D(TabWidget, QtGui.QWidget):

    def __init__(self, name, columns, x_axis=None, y_axis=None, refresh_time=0.2,
                 check_status=True, linewidth=1, parent=None, model_file = None):
        super().__init__(name, parent)
        self.model_file = model_file
        self.columns = columns
        self.refresh_time = refresh_time
        self.check_status = check_status
        self.linewidth = linewidth
        self._setup_ui()
        self._layout()
        if x_axis is not None:
            self.columns_x.setCurrentIndex(self.columns_x.findText(x_axis))
            self.plot_frame.change_x_axis(x_axis)
        if y_axis is not None:
            if isinstance(y_axis, str):
                y_list = (y_axis,)
            else:
                y_list = y_axis
            self.columns_y.setCurrentIndex(self.columns_y.findText(y_list[0]))
            for y in y_list:
                self.columns_y.set_check_state(y, True)
            self.plot_frame.change_y_axis(y_list)

    def _setup_ui(self):
        self.columns_x_label = QtGui.QLabel(self)
        self.columns_x_label.setMaximumSize(QtCore.QSize(45, 16777215))
        self.columns_x_label.setText('X Axis:')
        self.columns_y_label = QtGui.QLabel(self)
        self.columns_y_label.setMaximumSize(QtCore.QSize(45, 16777215))
        self.columns_y_label.setText('Y Axis:')

        self.columns_x = QtGui.QComboBox(self)
        self.columns_y = CheckableComboBox()
        for column in self.columns:
            self.columns_x.addItem(column)
            self.columns_y.addItem(column)
        self.columns_x.activated.connect(self.update_x_column)
        self.columns_y.activated.connect(self.update_y_column)

        self.plot_frame = PolarPlotFrame3D(
            self.columns[0],
            self.columns[1],
            self.refresh_time,
            self.check_status,
            model_file = self.model_file,
        )
        self.updated = self.plot_frame.updated
        self.plot = self.plot_frame.plot
        self.columns_x.setCurrentIndex(0)
        self.columns_y.setCurrentIndex(1)

    def _layout(self):
        vbox = QtGui.QVBoxLayout(self)
        vbox.setSpacing(0)

        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.setContentsMargins(-1, 6, -1, 6)
        hbox.addWidget(self.columns_x_label)
        hbox.addWidget(self.columns_x)
        hbox.addWidget(self.columns_y_label)
        hbox.addWidget(self.columns_y)

        vbox.addLayout(hbox)
        vbox.addWidget(self.plot_frame)
        self.setLayout(vbox)

    def sizeHint(self):
        return QtCore.QSize(300, 600)

    def new_curve(self, results, color=pg.intColor(0), **kwargs):
        styles = (QtCore.Qt.SolidLine,
                  QtCore.Qt.DashLine,
                  QtCore.Qt.DotLine,
                  QtCore.Qt.DashDotLine,
                  QtCore.Qt.DashDotDotLine)
        need_pen = False
        if 'pen' not in kwargs:
            need_pen = True
        if 'antialias' not in kwargs:
            kwargs['antialias'] = False

        curve = {}
        for index, column in enumerate(self.columns):
            if need_pen:
                kwargs['pen'] = pg.mkPen(color=color,
                                         width=self.linewidth,
                                         style = styles[index % len(styles)],
                                         )
            curve[column] = Results3DMesh(results,
                                         x=self.plot_frame.x_axis,
                                         y=column,
                                         drawEdges = False,
                                         **kwargs
                                     )

        return curve

    def update_x_column(self, index):
        axis = self.columns_x.itemText(index)
        self.plot_frame.change_x_axis(axis)

    def update_y_column(self, index):
        axis = self.columns_y.itemText(index)
        checked = self.columns_y.item_checked(index)
        for item in self.plot.items:
            if isinstance(item, Results3DMesh):
                if item.y == axis:
                    if checked:
                        item.show()
                    else:
                        item.hide()
                    item.update_data()
        self.plot_frame.change_y_axis(self.columns_y.checked_items())

    def load(self, curve):
        # Add new set of curves
        checked = self.columns_y.checked_items()
        for i,i_curve in enumerate(curve.values()):
            i_curve.x = self.columns_x.currentText()
            i_curve.y = self.columns[i]
            i_curve.update_data()
            self.plot.addItem(i_curve)
            if not i_curve.y in checked:
                i_curve.hide()
                i_curve.update_data()

    def remove(self, curve):
        for i_curve in curve.values():
            self.plot.removeItem(i_curve)

    def set_color(self, curve, color):
        """ Change the color of the pen of the curve """
        for i_curve in curve.values():
            i_curve.pen.setColor(color)
            # i_curve.updateItems(styleUpdate=True)