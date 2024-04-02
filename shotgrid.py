#!/usr/bin/env python
# encoding=utf-8

# author        : sj
# created date  : 2024.03.16
# modified date : 2024.03.16
# description   :

import shotgun_api3

class ShotGrid:
    def __init__(self, version, shot, task, des, path):
        # 샷그리드 연동
        self.sg = shotgun_api3.Shotgun("https://rapavfxtd.shotgrid.autodesk.com",
                          script_name="sj_script_api",
                          api_key="tjkKhqdwcnwgnkfxujel(vo0q")

        self.version = version
        self.shot = shot
        self.task = task
        self.des = des
        self.path = path

        self.project = 'Render_test'

    def find_project_id(self):
        project = self.sg.find_one("Project", [["name", "is", self.project]], ["id"])
        return project['id']

    def find_shot_id(self):
        filters = [
            ['project', 'is', {'type': 'Project', 'id': self.find_project_id()}],
            ['code', 'is', self.shot]
        ]

        fields = ['id', 'code']

        shots = self.sg.find("Shot", filters, fields)

        return shots[0]['id']

    def find_task_id(self):
        filters = [['entity', 'is', {'type': 'Shot', 'id': self.find_shot_id()}], ['content', 'is', self.task]]
        fields = ['id', 'content']

        tasks = self.sg.find("Task", filters, fields)

        return tasks[0]['id']

    def add_shot_version_file_path(self):
        data = {
            'project': {'type': 'Project', 'id': 122},
            'code': self.version,
            'description': self.des,
            'sg_path_to_frames': self.path,
            'sg_status_list': 'na',
            'entity': {'type': 'Shot', 'id': self.find_shot_id()},
            'sg_task': {'type': 'Task', 'id': self.find_task_id()},
            'user': {'type': 'HumanUser', 'id': 88}
        }

        self.sg.create('Version', data)

if __name__ == '__main__':
    pass
