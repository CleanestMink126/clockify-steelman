import requests
import time
from datetime import datetime, timedelta
from dateutil import tz
import matplotlib.pyplot as plt
import numpy as np
from authkey import KEY, USER_ID, WORKSPACE_ID


ENDPOINT = 'https://api.clockify.me/api/v1'
from_zone = tz.tzutc()
to_zone = tz.tzlocal()
colors = ['b', 'g', 'r', 'c', 'm', 'y']
weekdays = ['M', 'T', 'W', 'Th', 'F', 'S', 'Su']


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
    proj_info = {}
    for entry in req:
        proj_name[entry['id']] = entry['name']
        proj_info[entry['name']] = entry['color']
    return proj_name, proj_info


def getTimes(proj_name, start_time, end_time=None):
    path = f'/workspaces/{WORKSPACE_ID}/user/{USER_ID}/time-entries'
    arguements = f'?start={start_time}&page-size=1000'
    if end_time is not None:
        arguements += f'&end={end_time}'
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
        start = datetime.fromisoformat(start[:-1]).replace(tzinfo=from_zone).astimezone(to_zone)
        end = entry['timeInterval']['end']
        if (end is None):
            continue
        end = datetime.fromisoformat(end[:-1]).replace(tzinfo=from_zone).astimezone(to_zone)
        # Check checkMidnight
        if start.date() != end.date():
            new_end = start.replace(hour=23, minute=59, second=59)
            new_start = end.replace(hour=0, minute=0, second=0)
            first_entry = TimeEntry(start, new_end, project)
            entries.append(first_entry)
            prev_entries = entries_by_project[project]
            prev_entries.append(first_entry)
            start = new_start
        if start.date() == datetime.today().date():
            continue
        entry = TimeEntry(start, end, project)
        entries.append(entry)
        prev_entries = entries_by_project[project]
        prev_entries.append(entry)

    return entries, entries_by_project


def get_expected_activity(curr_datetime):
    proj_name, proj_info = getProjects()
    start_str = (curr_datetime - timedelta(days=1000)).isoformat() + "Z"
    entries, entries_by_project = getTimes(proj_name, start_str)
    project_idx = {v: i for i, v in enumerate(proj_name.values())}
    counts = np.zeros(len(proj_name))
    for entry in entries:
        if(entry.start.weekday() != curr_datetime.weekday()):
            continue
        if(entry.start.time() <= curr_datetime.time() <= entry.end.time()):
            counts[project_idx[entry.project_name]] += 1
    counts = counts / np.sum(counts)
    for k, v in proj_name.items():
        if(counts[project_idx[v]]):
            print(f'{v}: {counts[project_idx[v]]}')


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
    while dates[-1] < range_d[1]:
        dates.append(dates[-1] + one_day)
    date_idx = {d: i for i, d in enumerate(dates)}
    return date_idx


def get_range(entries_by_project, selected_groups, date_idx):
    num_x = len(date_idx)
    x = list(date_idx.keys())
    groups_times = []
    for i, projects in enumerate(selected_projects):
        group_sum = np.zeros(num_x)
        for project in projects:
            entries = entries_by_project[project]
            for entry in entries:
                duration = entry.duration.total_seconds()/3600.0
                group_sum[date_idx[entry.start.date()]] += duration
        groups_times.append(group_sum)
    return x, groups_times


def get_average_week(entries_by_project, selected_groups, date_idx):
    num_x = len(date_idx)
    rev_date_idx = {i: d for d, i in date_idx.items()}
    x, groups_times = get_range(entries_by_project, selected_groups, date_idx)
    total_sum = np.zeros(num_x)
    avg_group_times = []
    for i, group_sum in enumerate(groups_times):
        days_tot = np.zeros(7)
        days_num = np.zeros(7)
        for j in range(group_sum.shape[0]):
            curr_date = rev_date_idx[j]
            days_tot[curr_date.weekday()] += group_sum[j]
            days_num[curr_date.weekday()] += 1
        avg_group_times.append(days_tot/days_num)
    return weekdays, avg_group_times


def plot_entries(x, groups_times, selected_groups, proj_info):
    total_sum = np.zeros(len(x))
    for i, group_sum in enumerate(groups_times):
        projects = selected_groups[i]
        color = proj_info[projects[0]]
        next_sum = total_sum + group_sum
        plt.fill_between(x, total_sum, next_sum, color=color)
        plt.plot(x, next_sum, label=', '.join(projects), color=color)
        total_sum = next_sum
    print(np.mean(total_sum))
    plt.legend()
    plt.show()


def bar_plot(labels, data, selected_projects, proj_info):
    fig, ax = plt.subplots()
    num_groups = len(selected_projects)
    width = 1 / (num_groups + 1)  # the width of the bars
    locs = np.arange(len(labels))
    ax.set_xticks(locs - 0.5)
    ax.set_xticklabels(labels)
    for i, projects in enumerate(selected_projects):
        color = proj_info[projects[0]]
        ax.bar(locs - (1-width)*(i/num_groups), data[i], width, label=', '.join(projects), color=color)
    ax.legend()
    plt.show()


def compareWeek(selected_projects, start_date=None, week_end_date=None):
    proj_name, proj_info = getProjects()
    if start_date is None:
        start_date = datetime.now() - timedelta(days=100)
        start_date = start_date.replace(microsecond=0)
    start_date_str = start_date.isoformat() + "Z"
    entries, entries_by_project = getTimes(proj_name, start_date_str)
    date_idx = get_dates(entries)
    week_x, week_groups_times = get_average_week(entries_by_project, selected_projects, date_idx)
    all_x, all_groups_times = get_range(entries_by_project, selected_projects, date_idx)
    if week_end_date is None:
        week_end_date = datetime.now() - timedelta(days=1)
    start_date = week_end_date - timedelta(days=6)
    offset = start_date.weekday()
    start_idx = date_idx[start_date.date()]
    delta_group_times = []
    percent_group_times = []
    for curr_proj, avg_proj in zip(all_groups_times, week_groups_times):
        curr_week = curr_proj[start_idx:start_idx+7]
        avg_proj = np.roll(avg_proj, -offset)
        delta_group_times.append(curr_week - avg_proj)
        centered = (curr_week/(avg_proj + 0.00001) * 100) - 100
        centered[centered > 500] = 500.0
        percent_group_times.append(centered)
    x = all_x[start_idx:start_idx+7]
    delta_group_times = np.array(delta_group_times)
    percent_group_times = np.array(percent_group_times)
    x_labels = np.roll(np.array(week_x), -offset)
    bar_plot(x_labels, delta_group_times, selected_projects, proj_info)
    bar_plot(x_labels, percent_group_times, selected_projects, proj_info)


def plot(selected_projects, type=None, start_date=None):
    proj_name, proj_info = getProjects()
    if start_date is None:
        start_date = datetime.now() - timedelta(days=100)
        start_date = start_date.replace(microsecond=0)
    start_date_str = start_date.isoformat() + "Z"
    entries, entries_by_project = getTimes(proj_name, start_date_str)
    date_idx = get_dates(entries)
    if (average_week):
        x, groups_times = get_average_week(entries_by_project, selected_projects, date_idx)
    else:
        x, groups_times = get_range(entries_by_project, selected_projects, date_idx)
    plot_entries(x, groups_times, selected_projects, proj_info)


if __name__ == '__main__':

    selected_projects = [
        ['😴😴😴'],
        # ['SCOPE'],
        # ['🤝🤝🤝'],
        ['SCOPE', 'Misc Work', 'ENTREP', 'ML', 'BIO'],
        ['🤝🤝🤝', 'Misc not work', '🔥🔥🔥', 'Guitar Hero'],
        ['Misc life stuff',  '💪💪💪']
    ]
    start_date = datetime(2019, 10, 27)
    get_expected_activity(datetime.now())
    compareWeek(selected_projects, start_date=start_date)  # , week_end_date=datetime.now() - timedelta(days=7))
    # plot(selected_projects, average_week=False)
    # plot(selected_projects, average_week=True)
