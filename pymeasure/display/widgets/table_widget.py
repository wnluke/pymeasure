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
from numpy import float64, isnan, NaN
from functools import partial
import pyqtgraph as pg
import pandas as pd

from ..Qt import QtCore, QtWidgets, QtGui
from .tab_widget import TabWidget
from ...experiment import Procedure

SORT_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1

SORTING_ENABLED = True  # Allow to disable sorting, for debug purpose only

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ResultsTable(QtCore.QObject):
    """ Class representing a panda dataframe """
    data_changed = QtCore.Signal(int, int, int, int)
    color_changed = QtCore.Signal(object)

    def __init__(self, results, color, column_index=None,
                 force_reload=False, wdg=None, **kwargs):
        super().__init__()
        self.results = results
        self.color = color
        self.force_reload = force_reload
        self.last_row_count = 0
        self.wdg = wdg
        self.column_index = column_index
        self.data = self.results.data
        self._started = False

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value
        if self.column_index is not None:
            self._data = self._data.set_index(self.column_index)

    @property
    def rows(self):
        return self._data.shape[0]

    @property
    def columns(self):
        return self._data.shape[1]

    def init(self):
        self.last_row_count = 0

    def start(self):
        self._started = True

    def stop(self):
        self._started = False

    def update_data(self):
        if not self._started:
            return
        if self.force_reload:
            self.results.reload()
        self.data = self.results.data
        current_row_count, columns = self._data.shape
        if (self.last_row_count < current_row_count):
            # Request cells content update
            self.data_changed.emit(self.last_row_count, 0,
                                   current_row_count - 1, columns - 1)
            self.last_row_count = current_row_count

    def set_color(self, color):
        self.color = color
        self.color_changed.emit(color)


class PandasModelBase(QtCore.QAbstractTableModel):
    def __init__(self, column_index=None, float_digits=6, parent=None):
        super().__init__(parent)
        self.results_list = []
        self.float_digits = float_digits
        self.column_index = column_index
        self.header_decoration = {}
        self.compose_dataframe()

    def clear(self):
        self.beginResetModel()
        for results in self.results_list:
            results.stop()
        self.results_list = []
        self.endResetModel()

    def add_results(self, results):
        if results not in self.results_list:
            self.results_list.append(results)
            results.data_changed.connect(partial(self._data_changed, results))
            results.color_changed.connect(partial(self._color_changed, results))
            results.init()
            results.start()
            results.update_data()

    def remove_results(self, results):
        if results in self.results_list:
            self.results_list.remove(results)
        results.stop()
        self._data_changed(None, 0, 0, 0, 0)
        self._color_changed(None, None)

    def rowCount(self, parent=None):
        return self.df.shape[0]

    def columnCount(self, parent=None):
        return self.df.shape[1]

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role in (QtCore.Qt.ItemDataRole.DisplayRole, SORT_ROLE):
            row = index.row()
            col = index.column()
            try:
                value = self.df.iloc[row][col]
                column_type = self.df.dtypes[col]
                # Cast to column type
                value_render = column_type.type(value) #???
            except IndexError:
                value = pd.NA #NaN

            if pd.isna(value):
                value_render = ""
            if isinstance(value_render, float64):
                # limit maximum number of decimal digits displayed
                value_render = f"{value_render:.{self.float_digits:d}f}"

            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return str(value_render)
            elif role == SORT_ROLE:
                # For numerical sort
                return float(value)

        return None

    def headerData(self, section, orientation, role):
        """ Return header information

        Override method from QAbstractTableModel
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self.df.columns[section])

            if orientation == QtCore.Qt.Orientation.Vertical:
                return str(self.df.index[section])
        elif role == QtCore.Qt.ItemDataRole.DecorationRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self.horizontal_header_decoration(section)

            if orientation == QtCore.Qt.Orientation.Vertical:
                return self.vertical_header_decoration(section)

        return None

    def _data_changed(self, results, r1, c1, r2, c2):
        """ Internal method to handle data changed signal """
        self.beginResetModel()
        self.compose_dataframe()
        self.endResetModel()

    def _color_changed(self, results, color):
        self.header_decoration = {}

    def update_dataframe(self, df):
        self.df = self.df.join(df, how='outer').convert_dtypes().dropna(how='all')

    def compose_dataframe(self):
        """ Compose a pandas dataframe from a list of dataframes """
        raise Exception("Subclass should implement it")

    def horizontal_header_decoration(self, section):
        return None

    def vertical_header_decoration(self, section):
        return None

class PandasModelByColumn(PandasModelBase):
    def compose_dataframe(self):
        if self.results_list:
            self.df = pd.concat((r.data for r in self.results_list), axis=1, copy=False).fillna(pd.NA)
        else:
            self.df = pd.DataFrame()
        return self.df

    def horizontal_header_decoration(self, section):
        if not section in self.header_decoration:
            df_hdec = []
            for r in self.results_list:
                df_hdec += [r.color]*r.columns
                if len(df_hdec) > section:
                    break
            pixelmap = QtGui.QPixmap(6, 6)
            pixelmap.fill(df_hdec[section])
            self.header_decoration[section] = pixelmap
        return self.header_decoration[section]


class PandasModelByRow(PandasModelBase):
    def compose_dataframe(self):
        if self.results_list:
            self.df = pd.concat((r.data for r in self.results_list),
                                axis=0,
                                ignore_index=(self.column_index is None))
        else:
            self.df = pd.DataFrame()
        return self.df

    def vertical_header_decoration(self, section):
        if not section in self.header_decoration:
            df_dec = []
            for r in self.results_list:
                df_dec += [r.color]*r.rows
                if len(df_dec) > section:
                    break
            pixelmap = QtGui.QPixmap(6, 6)
            pixelmap.fill(df_dec[section])
            self.header_decoration[section] = pixelmap
        return self.header_decoration[section]


class Table(QtWidgets.QTableView):
    """ Table format view of :class:`Experiment<pymeasure.display.manager.Experiment>`
    objects

    """

    supported_formats = {
        "CSV file (*.csv)": 'csv',
        "Excel file (*.xlsx)": 'excel',
        "HTML file (*.html *.htm)": 'html',
        "JSON file (*.json)": 'json',
        "LaTeX file (*.tex)": 'latex',
        "Markdown file (*.md)": 'markdown',
        "XML file (*.xml)": 'xml',
    }

    def __init__(self, refresh_time=0.2, check_status=True,
                 force_reload=False, by_column=True, column_index=None, parent=None):
        super().__init__(parent)
        self.force_reload = force_reload
        if by_column:
            model = PandasModelByColumn(column_index=column_index)
        else:
            model = PandasModelByRow(column_index=column_index)

        self.setModel(model)
        self.horizontalHeader().setStyleSheet("font: bold;")
        self.sortByColumn(-1, QtCore.Qt.SortOrder.AscendingOrder)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

        self.setup_context_menu()

        self.refresh_time = refresh_time
        self.check_status = check_status
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_tables)
        self.timer.start(int(self.refresh_time * 1e3))

    def setModel(self, model):
        if SORTING_ENABLED:
            proxyModel = QtCore.QSortFilterProxyModel(self)
            proxyModel.setSourceModel(model)
            model = proxyModel

            model.setSortRole(SORT_ROLE)
        super().setModel(model)

    def source_model(self):
        if SORTING_ENABLED:
            model = self.model().sourceModel()
        else:
            model = self.model()
        return model

    def export_action(self):
        df = self.source_model().df

        if df is not None:
            formats = ";;".join(self.supported_formats.keys())
            filename_and_ext = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                     "Save File",
                                                                     "",
                                                                     formats)
            filename = filename_and_ext[0]
            ext = filename_and_ext[1]
            if filename:
                mode = self.supported_formats[ext]
                prefix = df.style if mode == "latex" else df
                getattr(prefix, 'to_' + mode)(filename)

    def refresh_action(self):
        self.update_tables()

    def copy_action(self):
        df = self.composed_dataframe()
        if df is not None:
            df.to_clipboard()

    def setup_context_menu(self):
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.copy = QtGui.QAction("Copy table data", self)
        self.copy.triggered.connect(self.copy_action)
        self.refresh = QtGui.QAction("Refresh table data", self)
        self.refresh.triggered.connect(self.refresh_action)
        self.export = QtGui.QAction("Export table data", self)
        self.export.triggered.connect(self.export_action)

    def context_menu(self, point):
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.copy)
        menu.addAction(self.refresh)
        menu.addAction(self.export)
        menu.exec(self.mapToGlobal(point))

    def update_tables(self):
        model = self.source_model()
        for item in model.results_list:
            if self.check_status:
                if item.results.procedure.status == Procedure.RUNNING:
                    item.update_data()
            else:
                item.update_data()

    def set_color(self, table, color):
        table.set_color(color)

    def add_table(self, table):
        model = self.source_model()
        model.add_results(table)

    def remove_table(self, table):
        model = self.source_model()
        model.remove_results(table)
        table.stop()

    def clear(self):
        model = self.model().source_model()

        model.clear()


class TableWidget(TabWidget, QtWidgets.QWidget):
    """ Widget to display experiment data in a tabular format
    """
    float_digits = 6

    def __init__(self, name, columns, column_index=None, by_column=True, refresh_time=0.2,
                 check_status=True, parent=None):
        super().__init__(name, parent)
        self.columns = columns
        self.by_column = by_column
        self.column_index = column_index
        self.refresh_time = refresh_time
        self.check_status = check_status
        self._setup_ui()
        self._layout()

    def _setup_ui(self):
        self.table = Table(refresh_time=self.refresh_time,
                           check_status=self.check_status,
                           force_reload=False,
                           by_column=self.by_column,
                           #column_index=self.column_index,
                           parent=self,
                           )

    def _layout(self):
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setSpacing(0)

        vbox.addWidget(self.table)
        self.setLayout(vbox)

    def new_curve(self, results, color=pg.intColor(0), **kwargs):
        ret = ResultsTable(results, color, self.column_index, wdg=self, **kwargs)
        return ret

    def load(self, table):
        self.table.add_table(table)

    def remove(self, table):
        self.table.remove_table(table)

    def set_color(self, table, color):
        """ Change the color of the pen of the curve """
        self.table.set_color(table, color)

    def preview_widget(self, parent=None):
        """ Return a widget suitable for preview during loading """

        return TablePreviewWidget("Table preview",
                                  columns=self.columns,
                                  by_column=self.by_column,
                                  refresh_time=self.refresh_time,
                                  check_status=True,
                                  parent=None)


class TablePreviewWidget(TableWidget):
    """ Class variant intended to be used during preview """

    def preview_update(self, results):
        """ Update the preview widget """
        self.table.clear()
        curve = self.new_curve(results)
        self.load(curve)
