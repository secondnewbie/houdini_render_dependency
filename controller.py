#!/usr/bin/env python
# encoding=utf-8

# author        : sj
# created date  : 2024.03.19
# modified date : 2024.03.19
# description   :

import hou
import pathlib
import xmlrpc.client as xc
import logging
import datetime
import subprocess
import platform

from PySide2 import QtWidgets, QtCore, QtGui

from libraries.qt import library as qt_lib

from view import UIView
from model import ListModel, TableModel

from shotgrid import ShotGrid
from datathread import DataThread


class Controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.view = UIView()
        self.list_item = list()
        self.table_item = list()

        self.list_model = ListModel(self.list_item)
        self.table_model = TableModel(self.table_item)

        self.view.list_node.setModel(self.list_model)
        self.view.table_ren_node.setModel(self.table_model)

        self.view.show()

        self.main_sig()

        self.tmp_check_lst = []

        self.__msg = qt_lib.LogHandler(out_stream=self.view.debug_slot)

        self.data_threads = []

    def main_sig(self):
        self.view.tool_btn.clicked.connect(self.open_file)
        self.list_model.checkStateChanged.connect(self.check_node)
        self.view.push_btn_ren.clicked.connect(self.start_render)
        self.view.push_btn_can.clicked.connect(self.cancel_render)
        self.view.push_btn_clear.clicked.connect(self.tree_clear)

    def slot_open(self):
        """
        렌더할 후디니 파일 오픈
        """
        dir = QtWidgets.QFileDialog.getOpenFileName(self.view, 'Open File', '/data/workspace/houdini/sj')
        if dir[0]:
            fpath = pathlib.Path(dir[0])
            self.view.line_fpath.setText(str(fpath))
            return fpath
        else:
            return None

    @property
    def get_file_path(self) -> pathlib.Path:
        """
        파일 경로를 메서드화한다.
        """
        fpath = self.view.line_fpath.text()
        return pathlib.Path(fpath)

    def open_file(self):
        fpath = self.slot_open()
        if fpath:
            hou.hipFile.load(str(fpath))

            out_node = hou.node('/out')
            self.show_node(out_node)

    def show_node(self, node):
        """
        자식 노드들 중 'f1'이라는 파라미터를 갖고 있는 노드들만 찾는다.
        :param node: 부모노드
        """
        self.list_item.clear()
        for child in node.children():
            if child.parm('f1'):
                self.list_item.append(child.name())

        self.list_model.updateItems(self.list_item)

    @QtCore.Slot(str, bool)
    def check_node(self, nodeName, checked):
        """
        :param nodeName: 시그널의 변경이 있던 노드
        :param checked: 체크 상태(True, False)
        :return:
        """
        # 추가를 위해 체크박스를 클릭했다면, checked == True
        if checked:
            if nodeName not in self.tmp_check_lst:
                self.tmp_check_lst.append(nodeName)

                # table_ren_node의 맨 밑에 새로운 열 추가
                newRow = len(self.table_item)
                self.table_model.beginInsertRows(QtCore.QModelIndex(), newRow, newRow)
                self.table_item.append([newRow + 1, nodeName, None, None])
                self.table_model.endInsertRows()

                # 공백이었던 프레임 시작과 끝 값을 해당 노드에서 가져온다.
                fs_index = self.table_model.index(newRow, 2)
                fe_index = self.table_model.index(newRow, 3)
                fs = self.table_model.data(fs_index, TableModel.FS)
                fe = self.table_model.data(fe_index, TableModel.FE)
                self.table_item[-1][2] = fs
                self.table_item[-1][3] = fe

        # 제거를 위해 체크박스를 클릭했다면, checked == False
        else:
            if nodeName in self.tmp_check_lst:
                self.tmp_check_lst.remove(nodeName)

                # nodeName과 일치하는 열 제거
                for row, item in enumerate(self.table_item):
                    if item[1] == nodeName:
                        self.table_model.beginRemoveRows(QtCore.QModelIndex(), row, row)
                        self.table_item.pop(row)
                        self.table_model.endRemoveRows()

    def make_dependency_dict(self):
        """
        노드별 기입한 우선순위를 기준으로 노드의 종속성을 딕셔너리로 구현한다. (key: priority, value: node이름)
        """
        num_list = []
        ren_dict = {}
        # table_model에 있는 모든 데이터의 우선순위를 num_list에 담는다.
        for i in range(len(self.tmp_check_lst)):
            index = self.table_model.index(i, 0)
            num = self.table_model.data(index, QtCore.Qt.DisplayRole)
            num_list.append(num)

        for id, it in enumerate(num_list):
            # 중복 숫자가 없다면 ren_dict에 담는다.
            if num_list.count(it) == 1:
                index = self.table_model.index(id, 1)
                name = self.table_model.data(index, QtCore.Qt.DisplayRole)
                ren_dict[it] = name

            # 중복 숫자가 있다면 value값인 node이름들을 리스트로 만든 후에 ren_dict에 담는다.
            else:
                ch_list = list(filter(lambda x: num_list[x] == it, range(len(num_list))))
                sm_list = []
                if id == ch_list[0]:
                    for tmp in ch_list:
                        index = self.table_model.index(tmp, 1)
                        name = self.table_model.data(index, QtCore.Qt.DisplayRole)
                        sm_list.append(name)
                    ren_dict[it] = sm_list

        # 우선순위에 맞게 오름차순으로 정렬한다.
        sorted_ren_dict = {k: ren_dict[k] for k in sorted(ren_dict)}

        # print(sorted_ren_dict)
        return sorted_ren_dict

    def find_row_by_name(self, name):
        """
        table_model에서 이름을 활용해 데이터의 row 넘버를 찾는다.
        :param name: 노드 이름
        """
        for row in range(self.table_model.rowCount()):
            index = self.table_model.index(row, 1)
            if self.table_model.data(index, QtCore.Qt.DisplayRole) == name:
                return row
        return -1

    def set_hrender(self, node):
        """
        노드를 렌더하기 위한 command의 기본 틀을 만든다.
        :param node: 노드이름
        """
        node_row = self.find_row_by_name(node)
        fs_index = self.table_model.index(node_row, 2)
        fs_num = self.table_model.data(fs_index, QtCore.Qt.DisplayRole)
        fe_index = self.table_model.index(node_row, 3)
        fe_num = self.table_model.data(fe_index, QtCore.Qt.DisplayRole)

        res = {
            "name": f"{node}",
            "shell": "bash",
            "command":(
                "cd /opt/hfs19.5;"
                "source houdini_setup;"
                f"hrender -e -f {fs_num} {fe_num} -v -d /out/{node} {str(self.get_file_path)};"
            )
        }
        return res

    def make_render_dependency(self, data:dict):
        """
        종속성을 바탕으로 render job의 부모-자식 관계를 재귀함수로 구현한다.
        :param data: 종속성을 구현한 노드 딕셔너리 (key: 우선순위, value: 노드 이름)
        """
        data_copy = data.copy()
        num = list(data_copy.keys())[0]
        node = data_copy.pop(num)

        # value값이 리스트가 아니라면,
        if not isinstance(node, list):
            result = self.set_hrender(node)
            if data_copy:
                if isinstance(list(data_copy.values())[0], list):
                    result["children"] = self.make_render_dependency(data_copy)
                else:
                    result["children"] = [self.make_render_dependency(data_copy)]

        # value값이 리스트라면,
        else:
            result = [self.set_hrender(child) for child in node]
            if data_copy:
                if isinstance(list(data_copy.values())[0], list):
                    result[0]["children"] = self.make_render_dependency(data_copy)
                else:
                    result[0]["children"] = [self.make_render_dependency(data_copy)]
        # print(result)
        return result

    def start_render(self):
        # 렌더 시작 전, 초기화
        self.data_threads.clear()
        self.view.debug_slot.clear()
        self.view.progressbar.setValue(0)

        self.view.debug_slot.setTextColor(QtGui.QColor("Orange"))
        self.view.debug_slot.setText(f'*****{self.get_file_path.name} RENDER START*****')

        tmp_final_dict = self.make_dependency_dict()

        # 렌더 시작
        self.hq_server = xc.ServerProxy("http://192.168.5.26:5000")
        self.job_id_list = self.hq_server.newjob(self.make_render_dependency(tmp_final_dict))

        self.fin_dict = self.make_fin_dict(tmp_final_dict)

        self.pause_job(self.fin_dict)

        for jid in self.job_id_list:
            data_thread = DataThread(jid)
            self.data_threads.append(data_thread)
            data_thread.signals.data.connect(self.debug_msg)
            data_thread.run_start()

        self.work_data = dict()
        self.get_single_ratio()

    def job_detail_lst(self, job_id: list):
        """
        job마다의 정보들을 가져와 딕셔너리로 만든다. (key: id, value: 정보)
        :param job_id: 렌더 job id
        """
        job_dict = {}
        for id in job_id:
            job_dict[id] = self.hq_server.getJob(id)
        return job_dict

    def make_fin_dict(self, rdict: dict):
        """
        렌더가 시작된 후, 기존의 딕셔너리의 value값을 '노드 이름'에서 'job id'로 바꾼다.
        :param rdict: 종속성을 구현한 기존의 딕셔너리
        """
        for id, detail in self.job_detail_lst(self.job_id_list).items():
            for pri, name in rdict.items():
                if not isinstance(name, list):
                    if name == detail["name"]:
                        rdict[pri] = id
                else:
                    for i, na in enumerate(name):
                        if na == detail["name"]:
                            rdict[pri][i] = id
        return rdict

    def pause_job(self, fdict: dict):
        for job in fdict.values():
            if isinstance(job, list):
                for i, id in enumerate(job):
                    if i == 0:
                        pass
                    else:
                        self.hq_server.pauseJobs([id])

    def resume_job(self, id: int, fi_dict: dict):
        for jobs in fi_dict.values():
            if isinstance(jobs, list):
                for i, job in enumerate(jobs):
                    if job == id and i != len(jobs) - 1:
                        self.hq_server.resumeJobs([jobs[i + 1]])
                        return

    @QtCore.Slot(int, str, str, xc.DateTime, xc.DateTime)
    def debug_msg(self, id, name, status, starttime, endtime):
        """
        job의 현재 상태에 맞게 디버깅창에 메시지를 띄운다.
        :param id: job id
        :param name: job 이름
        :param status: job 상태
        :param starttime: job 시작 시간
        :param endtime: job 끝난 시간
        """
        status_lst = []

        if status in ["running", "resuming"] and status not in status_lst:
            qt_lib.LogHandler.log_msg(logging.info, f'RENDER START : {name}')
            pass

        elif status == "succeeded":
            st = datetime.datetime.strptime(str(starttime), "%Y%m%dT%H:%M:%S")
            et = datetime.datetime.strptime(str(endtime), "%Y%m%dT%H:%M:%S")
            qt_lib.LogHandler.log_msg(logging.debug, f'RENDER SUCCEED : {name}, TOTAL TIME : {et-st}')
            self.resume_job(id, self.fin_dict)

        elif status == "failed":
            qt_lib.LogHandler.log_msg(logging.critical, f'RENDER FAIL : {name}')
            self.view.debug_slot.setTextColor(QtGui.QColor("Red"))
            self.view.debug_slot.append(f'*****{self.get_file_path.name} RENDER FAIL*****')
            self.send_fail_notice()

        if status not in status_lst:
            status_lst.append(status)
        else:
            pass

    def get_single_ratio(self):
        for thread in self.data_threads:
            thread.signals.jid.connect(self.total_progress)

    @QtCore.Slot(int)
    def total_progress(self, jid):
        self.work_data[jid] = 1
        completed_count = sum(self.work_data.values())
        total_count = len(self.data_threads)
        ratio = (completed_count / total_count) * 100
        self.view.progressbar.setValue(ratio)

        if self.view.progressbar.value() == 100:
            self.view.debug_slot.setTextColor(QtGui.QColor("Blue"))
            self.view.debug_slot.append(f'*****{self.get_file_path.name} RENDER SUCCESS*****')
            self.upload_shotgrid()
            self.send_success_notice()

    def cancel_render(self):
        for thread in self.data_threads:
            if thread.isRunning():
                thread.stop()
                thread.wait()
        self.view.debug_slot.setTextColor(QtGui.QColor("Red"))
        self.view.debug_slot.append(f'*****{self.get_file_path.name} RENDER CANCEL*****')

        self.hq_server.cancelJobs(self.job_id_list)

    def tree_clear(self):
        for i in range(self.view.list_node.model().rowCount()):
            index = self.view.list_node.model().index(i)
            self.view.list_node.model().setData(index, QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

    def upload_shotgrid(self):
        """
        작성한 내용들을 샷그리드에 올린다.
        """
        version = self.view.set_version_name.text()
        shot = self.view.set_shot_name.text()
        task = self.view.set_task_name.text()
        des = self.view.set_description.toPlainText()
        path = self.view.set_final_path.text()
        sg = ShotGrid(version, shot, task, des, path)
        sg.add_shot_version_file_path()

    def send_success_notice(self):
        message = f"{self.get_file_path.name} Render Success : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        os_name = platform.system()
        if os_name == "Windows":
            subprocess.Popen(['msg', '*', message])
        elif os_name == "Darwin":
            subprocess.Popen(['osascript', '-e', f'display notification "{message}" with title "notification"'])
        elif os_name == "Linux":
            subprocess.Popen(["notify-send", "notification", message])

    def send_fail_notice(self):
        message = f"{self.get_file_path.name} Render Fail : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        os_name = platform.system()
        if os_name == "Windows":
            subprocess.Popen(['msg', '*', message])
        elif os_name == "Darwin":
            subprocess.Popen(['osascript', '-e', f'display notification "{message}" with title "notification"'])
        elif os_name == "Linux":
            subprocess.Popen(["notify-send", "notification", message])

if __name__ == "__main__":
    pass
