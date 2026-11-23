# capstone-project-python-assignment-
task tracker app assignment

# Task & Productivity Tracker

A lightweight command line task manager that keeps your tasks in a local JSON file and turns your progress into useful summaries and charts.

<p align="center">
  <strong>Plan your work. Track your progress. Understand your habits.</strong>
</p>

## ✨ Features

- Create, view, update, complete, delete, and search tasks
- Organize tasks by category, priority, and status
- Validate task details, dates, and estimated hours
- Save data locally in `tasks.json` using an atomic file replacement
- Back up malformed JSON data as `tasks.json.corrupt` and start with an empty task list
- Analyze completion, overdue tasks, on-time performance, and estimated hours
- Generate three PNG charts in the `charts/` folder
- Load sample data to explore the reports
- Run built-in unit tests

## 📋 Task fields

| Field | Details |
| --- | --- |
| Title | Required, up to 100 characters |
| Category | Study, Work, Personal, Health, or Finance |
| Priority | High, Medium, or Low |
| Status | Pending, In Progress, or Completed |
| Due date | `YYYY-MM-DD` format |
| Estimated hours | Greater than 0 and up to 24 |

## 🚀 Getting started

### Requirements

- Python 3.9 or newer
- `pandas` and `matplotlib` for analysis and charts

### Install

Clone your repository and move into the project directory:

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>


# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
