import requests
import time
from datetime import datetime, timedelta
import matplotlib
from authkey import KEY, USER_ID, WORKSPACE_ID

ENDPOINT = 'https://api.clockify.me/api/v1'
selected_projects = ['Misc not work', 'Misc life stuff', '🤝🤝🤝', '😴😴😴', '💪💪💪',
                     '🔥🔥🔥', 'Misc Work', 'ENTREP', 'Guitar Hero', 'BIO', 'ML', 'SCOPE']


class TimeEntry:
    def __init__(self, start, end, project_name):
        self.start = start
        self.end = end
        self.project_name = project_name
        self.duration = end - start

    def __repr__(self):
        return f'{self.project_name}: {self.start}, {self.duration}'


def getProjects():
    path = f'/workspaces/{WORKSPACE_ID}/projects'
    url = ENDPOINT + path
    req = requests.get(url, headers={'content-type': 'application/json', 'X-Api-Key': KEY})
    req = req.json()
    proj_name = {}
    for entry in req:
        proj_name[entry['id']] = entry['name']
    return proj_name


def getTimes(proj_name, start_time):
    path = f'/workspaces/{WORKSPACE_ID}/user/{USER_ID}/time-entries'
    arguements = f'?start={start_time}&page-size=1000'
    # path = '/workspaces'
    url = ENDPOINT + path + arguements
    req = requests.get(url, headers={'content-type': 'application/json', 'X-Api-Key': KEY})
    req = req.json()
    entries = []
    entries_by_project = {}
    for entry in req[::-1]:
        project = proj_name.get(entry['projectId'], 'NULL')
        if (project not in entries_by_project):
            entries_by_project[project] = []
        start = entry['timeInterval']['start']
        start = datetime.fromisoformat(start[:-1])
        end = entry['timeInterval']['end']
        if (end is None):
            continue
        end = datetime.fromisoformat(end[:-1])
        # Check checkMidnight
        if start.date() != end.date():
            new_end = start.replace(hour=23, minute=59, second=59)
            new_start = end.replace(hour=0, minute=0, second=0)
            first_entry = TimeEntry(start, new_end, project)
            entries.append(first_entry)
            prev_entries = entries_by_project[project]
            prev_entries.append(first_entry)
            start = new_start
        entry = TimeEntry(start, end, project)
        entries.append(entry)
        prev_entries = entries_by_project[project]
        prev_entries.append(entry)

    return entries, entries_by_project


# print(req)
if __name__ == '__main__':
    proj_name = getProjects()
    print(proj_name.values())
    last_week = datetime.now() - timedelta(days=14)
    last_week = last_week.replace(microsecond=0)
    last_week_str = last_week.isoformat() + "Z"
    entries = getTimes(proj_name, last_week_str)
    print(entries)
