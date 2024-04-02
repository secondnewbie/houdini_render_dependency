#!/usr/bin/env python
# encoding=utf-8

# author        : sj
# created date  : 2024.03.15
# modified date : 2024.03.15
# description   :

import xmlrpc.client as xc
import time
import datetime
from PySide2 import QtWidgets, QtGui, QtCore

class Signals(QtCore.QObject):
    data = QtCore.Signal(int, str, str, xc.DateTime, xc.DateTime)
    jid = QtCore.Signal(int)

class DataThread(QtCore.QThread):
    def __init__(self, jid, parent=None):
        super().__init__(parent)
        self.jid = jid
        self.__signals: Signals = Signals()
        self.hq_server = xc.ServerProxy("http://192.168.5.26:5000")
        self.is_running = True
        self.first_running = True

    def stop(self):
        self.is_running = False

    @property
    def signals(self):
        return self.__signals

    def run(self):
        # 스레드가 돌고 있을 때 상태별로 다른 정보를 emit한다.
        while self.is_running:
            try:
                job = self.hq_server.getJob(self.jid, ["id", "name", "status", "children", "startTime", "endTime"])
                id = job["id"]
                name = job["name"]
                status = job["status"]
                starttime = job["startTime"]
                endtime = job["endTime"]

                if status in ["running", "resuming"] and self.first_running:
                    self.signals.data.emit(id, name, status, starttime, endtime)
                    self.first_running = False

                elif status in ["paused", "pausing"]:
                    self.first_running = True

                elif status == "succeeded":
                    self.signals.data.emit(id, name, status, starttime, endtime)
                    self.signals.jid.emit(self.jid)
                    break

                elif status == "failed":
                    self.signals.data.emit(id, name, status, starttime, endtime)
                    break

            except Exception as err:
                print("an error occurred:", err)

            time.sleep(1)

    def run_start(self):
        self.start()

if __name__ == '__main__':
    pass
