#!/usr/bin/env python
# encoding=utf-8

# author        : sj
# created date  : 2024.03.19
# modified date : 2024.03.19
# description   :

import hou

from PySide2 import QtWidgets, QtCore, QtGui

class ListModel(QtCore.QAbstractListModel):
    # 클래스 변수
    checkStateChanged = QtCore.Signal(str, bool)

    def __init__(self, data):
        super().__init__()
        self.items = [(item, False) for item in data]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def data(self, index, role=...):
        # 데이터
        if role == QtCore.Qt.DisplayRole:
            return self.items[index.row()][0]
        # 체크박스를 클릭했을 때 이벤트 발생
        elif role == QtCore.Qt.CheckStateRole:
            return QtCore.Qt.Checked if self.items[index.row()][1] else QtCore.Qt.Unchecked
        return None

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsUserCheckable

    def setData(self, index, value, role=...):

        if role == QtCore.Qt.CheckStateRole:
            self.items[index.row()] = (self.items[index.row()][0], value == QtCore.Qt.Checked)

            self.dataChanged.emit(index, index, [role])

            self.checkStateChanged.emit(self.items[index.row()][0], value == QtCore.Qt.Checked)

            return True
        return False

    def updateItems(self, newItems):
        self.beginResetModel()
        self.items = [(item, False) for item in newItems]
        self.endResetModel()


class TableModel(QtCore.QAbstractTableModel):
    # 클래스 변수
    FS = QtCore.Qt.UserRole + 1
    FE = QtCore.Qt.UserRole + 2

    def __init__(self, data):
        super().__init__()
        self._data = data
        self.headers = ['PRIOR', 'NODE', 'FSTART', 'FEND']

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.headers)

    def data(self, index, role=...):
        if role == QtCore.Qt.DisplayRole:
            return self._data[index.row()][index.column()]

        # 숫자를 바꿀 수 있는 우선순위만 색깔을 다르게 한다.
        elif role == QtCore.Qt.ForegroundRole:
            if index.column() == 0:
                return QtGui.QBrush(QtGui.QColor(255, 0, 0))

        # 시작프레임 정보 가져오기
        elif role == TableModel.FS:
            if self._data[index.row()][1] is not None:
                node = hou.node(f'/out/{self._data[index.row()][1]}')
                return str(int(node.parm('f1').eval()))

        # 끝프레임 정보 가져오기
        elif role == TableModel.FE:
            if self._data[index.row()][1] is not None:
                node = hou.node(f'/out/{self._data[index.row()][1]}')
                return str(int(node.parm('f2').eval()))

        return None

    def headerData(self, section, orientation, role=...):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.headers[section]
        return None

    def flags(self, index):
        if index.column() == 0:
            return super().flags(index) | QtCore.Qt.ItemIsEditable
        else:
            return super().flags(index)

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            if index.column() == 0:
                try:
                    self._data[index.row()][index.column()] = int(value)
                except ValueError:
                    return False
                self.dataChanged.emit(index, index, [role])
                return True
        return False

if __name__ == '__main__':
    pass
