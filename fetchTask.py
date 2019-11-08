import requests
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from authkey import KEY, USER_ID, WORKSPACE_ID


ENDPOINT = 'https://api.clockify.me/api/v1'
colors = ['b', 'g', 'r', 'c', 'm', 'y']


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


def get_dates(entries):
    range_d = [None, None]
    one_day = timedelta(days=1)
    for entry in entries:
        d = entry.start.date()
        if range_d[0] is None or d < range_d[0]:
            range_d[0] = d
        if range_d[1] is None or d > range_d[1]:
            range_d[1] = d
    # Build dict
    dates = [range_d[0]]
    while dates[-1] <= range_d[1]:
        dates.append(dates[-1] + one_day)
    date_idx = {d: i for i, d in enumerate(dates)}
    return date_idx


def plot_entries(entries_by_project, selected_groups, date_idx):
    num_x = len(date_idx)
    x = np.arange(num_x)
    print(date_idx)
    total_sum = np.zeros(num_x)
    for i, projects in enumerate(selected_projects):
        group_sum = np.zeros(num_x)
        for project in projects:
            entries = entries_by_project[project]
            for entry in entries:
                duration = entry.duration.total_seconds()/3600.0
                group_sum[date_idx[entry.start.date()]] += duration
        color = colors[i]
        next_sum = total_sum + group_sum
        plt.fill_between(x, total_sum, next_sum, color=color)
        plt.plot(x, next_sum, label=', '.join(projects), color=color)
        total_sum = next_sum
    plt.legend()
    plt.show()


# print(req)
if __name__ == '__main__':
    selected_projects = [
                        ['😴😴😴'],
                        ['SCOPE', 'Misc Work', 'ENTREP', 'ML', 'BIO'],
                        ['Misc not work', '🔥🔥🔥', 'Guitar Hero', '🤝🤝🤝'],
                        ['Misc life stuff',  '💪💪💪']
    ]
    proj_name = getProjects()
    print(proj_name.values())
    last_week = datetime.now() - timedelta(days=21)
    last_week = last_week.replace(microsecond=0)
    last_week_str = last_week.isoformat() + "Z"
    entries, entries_by_project = getTimes(proj_name, last_week_str)
    date_idx = get_dates(entries)
    plot_entries(entries_by_project, selected_projects, date_idx)
    # print(entries_by_project)
