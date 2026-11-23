



"""
Productivity & Task Tracker
Phases: 1 Design | 2 CRUD + JSON storage | 3 Pandas analysis + charts
        4 Tests + exception handling | 5 Console demo / report

DESIGN (Phase 1)
  Fields    : id, title, category, priority, status, created_date,
              due_date, completed_date, est_hours
  Categories: Study, Work, Personal, Health, Finance
  Priority  : High (urgent/important), Medium (normal), Low (can wait)
  Status    : Pending -> In Progress -> Completed
  Storage   : tasks.json (atomic write; corrupted files are backed up)
  Output    : console tables, summary metrics, 3 PNG charts in ./charts
"""
import json
import os
import random
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta

DATA_FILE = "tasks.json"
CHART_DIR = "charts"
CATEGORIES = ["Study", "Work", "Personal", "Health", "Finance"]
PRIORITIES = ["High", "Medium", "Low"]
STATUSES = ["Pending", "In Progress", "Completed"]
MAX_TITLE = 100
DATE_FMT = "%Y-%m-%d"


class TaskError(Exception):
    """Raised for any invalid input or task operation."""


# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------
def parse_date(text):
    try:
        return datetime.strptime(str(text).strip(), DATE_FMT).date()
    except ValueError:
        raise TaskError(f"Invalid date '{text}'. Use YYYY-MM-DD.")


def validate_title(title):
    title = str(title).strip()
    if not title:
        raise TaskError("Title cannot be empty.")
    if len(title) > MAX_TITLE:
        raise TaskError(f"Title too long (max {MAX_TITLE} characters).")
    return title


def validate_choice(value, options, label):
    for opt in options:
        if str(value).strip().lower() == opt.lower():
            return opt
    raise TaskError(f"Invalid {label} '{value}'. Choose from: {', '.join(options)}")


def validate_hours(value):
    try:
        hours = float(value)
    except (TypeError, ValueError):
        raise TaskError(f"Estimated hours must be a number, got '{value}'.")
    if not 0 < hours <= 24:
        raise TaskError("Estimated hours must be greater than 0 and at most 24.")
    return hours


# ----------------------------------------------------------------------
# Storage (Phase 2)
# ----------------------------------------------------------------------
def load_tasks(path=DATA_FILE):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Root must be a list")
        return data
    except (json.JSONDecodeError, ValueError):
        backup = path + ".corrupt"
        os.replace(path, backup)
        print(f"[Warning] {path} was corrupted. Backed up to {backup}. Starting fresh.")
        return []
    except OSError as e:
        raise TaskError(f"Cannot read file: {e}")


def save_tasks(tasks, path=DATA_FILE):
    folder = os.path.dirname(os.path.abspath(path))
    try:
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
        os.replace(tmp, path)  # atomic write: no half-written files
    except OSError as e:
        raise TaskError(f"Cannot save file: {e}")


# ----------------------------------------------------------------------
# Task operations (Phase 2)
# ----------------------------------------------------------------------
def next_id(tasks):
    return max((t["id"] for t in tasks), default=0) + 1


def find_task(tasks, task_id):
    try:
        task_id = int(task_id)
    except (TypeError, ValueError):
        raise TaskError("Task ID must be a whole number.")
    for t in tasks:
        if t["id"] == task_id:
            return t
    raise TaskError(f"No task found with ID {task_id}.")


def add_task(tasks, title, category, priority, due, est_hours=1.0, today=None):
    today = today or date.today()
    due_d = parse_date(due)
    if due_d < today:
        raise TaskError("Due date cannot be in the past.")
    task = {
        "id": next_id(tasks),
        "title": validate_title(title),
        "category": validate_choice(category, CATEGORIES, "category"),
        "priority": validate_choice(priority, PRIORITIES, "priority"),
        "status": "Pending",
        "created_date": today.strftime(DATE_FMT),
        "due_date": due_d.strftime(DATE_FMT),
        "completed_date": None,
        "est_hours": validate_hours(est_hours),
    }
    tasks.append(task)
    return task


def update_task(tasks, task_id, today=None, **changes):
    today = today or date.today()
    task = find_task(tasks, task_id)
    allowed = {"title", "category", "priority", "status", "due_date", "est_hours"}
    unknown = set(changes) - allowed
    if unknown:
        raise TaskError(f"Cannot update field(s): {', '.join(sorted(unknown))}")
    new = dict(task)  # validate everything before applying anything
    for key, val in changes.items():
        if key == "title":
            new[key] = validate_title(val)
        elif key == "category":
            new[key] = validate_choice(val, CATEGORIES, "category")
        elif key == "priority":
            new[key] = validate_choice(val, PRIORITIES, "priority")
        elif key == "status":
            new[key] = validate_choice(val, STATUSES, "status")
        elif key == "due_date":
            new[key] = parse_date(val).strftime(DATE_FMT)
        elif key == "est_hours":
            new[key] = validate_hours(val)
    if new["status"] == "Completed" and task["status"] != "Completed":
        new["completed_date"] = today.strftime(DATE_FMT)
    elif new["status"] != "Completed":
        new["completed_date"] = None
    task.update(new)
    return task


def delete_task(tasks, task_id):
    task = find_task(tasks, task_id)
    tasks.remove(task)
    return task


def search_tasks(tasks, keyword=None, category=None, status=None, priority=None):
    results = tasks
    if keyword:
        k = keyword.strip().lower()
        results = [t for t in results if k in t["title"].lower()]
    if category:
        c = validate_choice(category, CATEGORIES, "category")
        results = [t for t in results if t["category"] == c]
    if status:
        s = validate_choice(status, STATUSES, "status")
        results = [t for t in results if t["status"] == s]
    if priority:
        p = validate_choice(priority, PRIORITIES, "priority")
        results = [t for t in results if t["priority"] == p]
    return results


def display_tasks(tasks):
    if not tasks:
        print("No tasks found.")
        return
    head = f"{'ID':<4}{'Title':<31}{'Category':<10}{'Priority':<9}{'Status':<13}{'Due':<11}"
    print(head)
    print("-" * len(head))
    for t in tasks:
        title = t["title"] if len(t["title"]) <= 29 else t["title"][:28] + "..."
        print(f"{t['id']:<4}{title:<31}{t['category']:<10}{t['priority']:<9}"
              f"{t['status']:<13}{t['due_date']:<11}")
    print(f"({len(tasks)} task(s))")


# ----------------------------------------------------------------------
# Analysis and charts (Phase 3)
# ----------------------------------------------------------------------
def analyze(tasks, today=None):
    import pandas as pd
    if not tasks:
        raise TaskError("No tasks to analyze. Add tasks or load sample data first.")
    ts = pd.Timestamp(today or date.today())
    df = pd.DataFrame(tasks)
    for c in ("created_date", "due_date", "completed_date"):
        df[c] = pd.to_datetime(df[c])
    done = df[df["status"] == "Completed"]

    metrics = {
        "total": len(df),
        "completed": len(done),
        "in_progress": int((df["status"] == "In Progress").sum()),
        "pending": int((df["status"] == "Pending").sum()),
        "completion_rate": round(len(done) / len(df) * 100, 1),
        "overdue": int(((df["status"] != "Completed") & (df["due_date"] < ts)).sum()),
        "on_time_rate": round((done["completed_date"] <= done["due_date"]).mean() * 100, 1)
        if len(done) else 0.0,
        "avg_days_to_complete": round(
            (done["completed_date"] - done["created_date"]).dt.days.mean(), 1)
        if len(done) else 0.0,
        "hours_completed": round(float(done["est_hours"].sum()), 1),
    }

    def rate_table(col):
        t = df.groupby(col).agg(total=("id", "count"),
                                completed=("status", lambda s: int((s == "Completed").sum())))
        t["rate"] = (t["completed"] / t["total"] * 100).round(1)
        return t

    by_cat, by_pri = rate_table("category"), rate_table("priority")
    days = pd.date_range(ts - pd.Timedelta(days=29), ts)
    daily = done.groupby("completed_date").size().reindex(days, fill_value=0)

    insights = []
    if len(by_cat):
        insights.append(f"Best category: {by_cat['rate'].idxmax()} ({by_cat['rate'].max()}% done).")
        insights.append(f"Needs attention: {by_cat['rate'].idxmin()} ({by_cat['rate'].min()}% done).")
    if len(done):
        insights.append(f"Most productive weekday: {done['completed_date'].dt.day_name().mode()[0]}.")
    if metrics["overdue"]:
        insights.append(f"{metrics['overdue']} task(s) are overdue - reschedule or finish them.")
    if metrics["on_time_rate"] and metrics["on_time_rate"] < 70:
        insights.append("On-time rate is below 70%: try setting more realistic due dates.")
    return {"metrics": metrics, "by_category": by_cat, "by_priority": by_pri,
            "daily": daily, "insights": insights}


def print_report(res):
    print("\n===== PRODUCTIVITY SUMMARY =====")
    for k, v in res["metrics"].items():
        print(f"{k.replace('_', ' ').title():<24}: {v}")
    print("\nBy category:\n", res["by_category"])
    print("\nBy priority:\n", res["by_priority"])
    print("\nInsights:")
    for line in res["insights"]:
        print(" -", line)


def make_charts(res, outdir=CHART_DIR):
    import matplotlib
    matplotlib.use("Agg")  # no GUI needed; saves PNG files
    import matplotlib.pyplot as plt
    os.makedirs(outdir, exist_ok=True)
    paths = []

    # 1) Completion trend (last 30 days)
    daily = res["daily"]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(daily.index, daily.values, marker="o", label="Completed per day")
    ax.plot(daily.index, daily.rolling(7, min_periods=1).mean(), linestyle="--",
            label="7-day average")
    ax.set_title("Task Completion Trend (Last 30 Days)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Tasks completed")
    ax.legend()
    fig.autofmt_xdate()
    paths.append(os.path.join(outdir, "completion_trend.png"))
    fig.tight_layout(); fig.savefig(paths[-1], dpi=120); plt.close(fig)

    # 2) Total vs completed per category
    cat = res["by_category"]
    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(cat))
    ax.bar([i - 0.2 for i in x], cat["total"], 0.4, label="Total")
    ax.bar([i + 0.2 for i in x], cat["completed"], 0.4, label="Completed")
    ax.set_xticks(list(x)); ax.set_xticklabels(cat.index)
    ax.set_title("Tasks by Category")
    ax.set_xlabel("Category"); ax.set_ylabel("Number of tasks")
    ax.legend()
    paths.append(os.path.join(outdir, "category_summary.png"))
    fig.tight_layout(); fig.savefig(paths[-1], dpi=120); plt.close(fig)

    # 3) Completion rate by priority
    pri = res["by_priority"].reindex([p for p in PRIORITIES if p in res["by_priority"].index])
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(pri.index, pri["rate"], color=["#d9534f", "#f0ad4e", "#5cb85c"][:len(pri)])
    for b, v in zip(bars, pri["rate"]):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v}%", ha="center")
    ax.set_ylim(0, 110)
    ax.set_title("Completion Rate by Priority")
    ax.set_xlabel("Priority"); ax.set_ylabel("Completion rate (%)")
    paths.append(os.path.join(outdir, "priority_rate.png"))
    fig.tight_layout(); fig.savefig(paths[-1], dpi=120); plt.close(fig)
    return paths


def generate_sample_data(n=40, today=None, seed=42):
    """Create realistic sample records spread over the last 30 days."""
    rng = random.Random(seed)
    today = today or date.today()
    titles = ["Read chapter", "Practice coding", "Team meeting prep", "Submit report",
              "Gym session", "Pay bills", "Plan budget", "Clean workspace",
              "Review notes", "Doctor appointment", "Write blog", "Update resume"]
    tasks = []
    for i in range(1, n + 1):
        created = today - timedelta(days=rng.randint(0, 29))
        due = created + timedelta(days=rng.randint(1, 7))
        status = rng.choices(STATUSES, weights=[2, 1, 5])[0]
        completed = None
        if status == "Completed":
            completed = min(created + timedelta(days=rng.randint(0, 8)), today)
        tasks.append({
            "id": i, "title": f"{rng.choice(titles)} #{i}",
            "category": rng.choice(CATEGORIES), "priority": rng.choice(PRIORITIES),
            "status": status, "created_date": created.strftime(DATE_FMT),
            "due_date": due.strftime(DATE_FMT),
            "completed_date": completed.strftime(DATE_FMT) if completed else None,
            "est_hours": round(rng.uniform(0.5, 4), 1),
        })
    return tasks


# ----------------------------------------------------------------------
# Console interface (Phase 5 demo)
# ----------------------------------------------------------------------
def ask(prompt, validator=None, optional=False):
    """Keep asking until the input passes validation."""
    while True:
        raw = input(prompt).strip()
        if optional and not raw:
            return None
        try:
            return validator(raw) if validator else raw
        except TaskError as e:
            print(f"  [Error] {e}")


def menu():
    print("""
===== TASK & PRODUCTIVITY TRACKER =====
1. Add task          5. Mark task complete
2. View all tasks    6. Delete task
3. Search tasks      7. Analysis & charts
4. Update task       8. Load sample data
9. Exit""")


def main():
    try:
        tasks = load_tasks()
    except TaskError as e:
        print(f"[Error] {e}")
        tasks = []
    while True:
        menu()
        choice = input("Choose (1-9): ").strip()
        try:
            if choice == "1":
                title = ask("Title: ", validate_title)
                cat = ask(f"Category {CATEGORIES}: ", lambda v: validate_choice(v, CATEGORIES, "category"))
                pri = ask(f"Priority {PRIORITIES}: ", lambda v: validate_choice(v, PRIORITIES, "priority"))
                due = ask("Due date (YYYY-MM-DD): ", parse_date)
                hrs = ask("Estimated hours (e.g. 1.5): ", validate_hours)
                t = add_task(tasks, title, cat, pri, due.strftime(DATE_FMT), hrs)
                save_tasks(tasks)
                print(f"Added task #{t['id']}.")
            elif choice == "2":
                display_tasks(tasks)
            elif choice == "3":
                kw = input("Keyword (blank to skip): ").strip() or None
                cat = input("Category (blank to skip): ").strip() or None
                st = input("Status (blank to skip): ").strip() or None
                pr = input("Priority (blank to skip): ").strip() or None
                display_tasks(search_tasks(tasks, kw, cat, st, pr))
            elif choice == "4":
                tid = input("Task ID to update: ")
                print("Leave a field blank to keep it unchanged.")
                changes = {}
                for field in ("title", "category", "priority", "status", "due_date", "est_hours"):
                    val = input(f"New {field}: ").strip()
                    if val:
                        changes[field] = val
                if not changes:
                    print("Nothing to update.")
                else:
                    update_task(tasks, tid, **changes)
                    save_tasks(tasks)
                    print("Task updated.")
            elif choice == "5":
                update_task(tasks, input("Task ID: "), status="Completed")
                save_tasks(tasks)
                print("Task marked complete.")
            elif choice == "6":
                t = delete_task(tasks, input("Task ID to delete: "))
                save_tasks(tasks)
                print(f"Deleted: {t['title']}")
            elif choice == "7":
                res = analyze(tasks)
                print_report(res)
                try:
                    for p in make_charts(res):
                        print("Chart saved:", p)
                except ImportError:
                    print("[Error] matplotlib is not installed: pip install matplotlib")
            elif choice == "8":
                if tasks and input("This replaces existing tasks. Continue? (y/n): ").lower() != "y":
                    continue
                tasks = generate_sample_data()
                save_tasks(tasks)
                print(f"Loaded {len(tasks)} sample tasks into {DATA_FILE}.")
            elif choice == "9":
                print("Goodbye!")
                break
            else:
                print("[Error] Please enter a number from 1 to 9.")
        except TaskError as e:
            print(f"[Error] {e}")
        except ImportError as e:
            print(f"[Error] Missing library: {e}. Run: pip install pandas matplotlib")
        except (KeyboardInterrupt, EOFError):
            print("\nInterrupted. Exiting safely.")
            break
        except Exception as e:  # last-resort safety net
            print(f"[Unexpected error] {type(e).__name__}: {e}")


# ----------------------------------------------------------------------
# Tests (Phase 4): python productivity_tracker.py test
# ----------------------------------------------------------------------
class TestTracker(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 11, 23)
        self.tasks = []
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "t.json")

    def add(self, **kw):
        args = dict(title="Study", category="Study", priority="High",
                    due="2026-11-30", est_hours=2, today=self.today)
        args.update(kw)
        return add_task(self.tasks, **args)

    # --- valid inputs
    def test_add_valid(self):
        t = self.add()
        self.assertEqual(t["id"], 1)
        self.assertEqual(t["status"], "Pending")

    def test_case_insensitive_choice(self):
        self.assertEqual(self.add(category="work", priority="LOW")["category"], "Work")

    def test_complete_sets_date(self):
        self.add()
        t = update_task(self.tasks, 1, today=self.today, status="Completed")
        self.assertEqual(t["completed_date"], "2026-11-23")

    def test_search(self):
        self.add(title="Read book"); self.add(title="Gym", category="Health")
        self.assertEqual(len(search_tasks(self.tasks, keyword="read")), 1)
        self.assertEqual(len(search_tasks(self.tasks, category="health")), 1)

    def test_delete(self):
        self.add(); delete_task(self.tasks, 1)
        self.assertEqual(self.tasks, [])

    def test_save_load_roundtrip(self):
        self.add(); save_tasks(self.tasks, self.path)
        self.assertEqual(load_tasks(self.path), self.tasks)

    # --- invalid inputs
    def test_empty_title(self):
        with self.assertRaises(TaskError): self.add(title="   ")

    def test_bad_category(self):
        with self.assertRaises(TaskError): self.add(category="Games")

    def test_bad_date_format(self):
        with self.assertRaises(TaskError): self.add(due="30-11-2026")

    def test_impossible_date(self):
        with self.assertRaises(TaskError): self.add(due="2026-02-30")

    def test_past_due_date(self):
        with self.assertRaises(TaskError): self.add(due="2026-11-22")

    def test_non_numeric_hours(self):
        with self.assertRaises(TaskError): self.add(est_hours="abc")

    def test_delete_missing(self):
        with self.assertRaises(TaskError): delete_task(self.tasks, 99)

    def test_non_numeric_id(self):
        with self.assertRaises(TaskError): find_task(self.tasks, "abc")

    def test_update_unknown_field(self):
        self.add()
        with self.assertRaises(TaskError): update_task(self.tasks, 1, color="red")

    def test_failed_update_changes_nothing(self):
        self.add()
        with self.assertRaises(TaskError):
            update_task(self.tasks, 1, title="New", priority="Urgent")
        self.assertEqual(self.tasks[0]["title"], "Study")

    # --- boundary inputs
    def test_title_length_boundary(self):
        self.add(title="a" * 100)
        with self.assertRaises(TaskError): self.add(title="a" * 101)

    def test_hours_boundary(self):
        self.add(est_hours=24); self.add(est_hours=0.1)
        for bad in (0, -1, 24.5):
            with self.assertRaises(TaskError): self.add(est_hours=bad)

    def test_due_today_allowed(self):
        self.add(due="2026-11-23")

    # --- file errors
    def test_corrupted_file(self):
        with open(self.path, "w") as f: f.write("{not json")
        self.assertEqual(load_tasks(self.path), [])
        self.assertTrue(os.path.exists(self.path + ".corrupt"))

    def test_missing_file(self):
        self.assertEqual(load_tasks(os.path.join(self.tmp, "none.json")), [])

    # --- analysis
    def test_analyze_empty(self):
        with self.assertRaises(TaskError): analyze([])

    def test_analyze_sample(self):
        res = analyze(generate_sample_data(today=self.today), today=self.today)
        self.assertEqual(res["metrics"]["total"], 40)
        self.assertTrue(0 <= res["metrics"]["completion_rate"] <= 100)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        unittest.main(argv=["x"], verbosity=2)
    else:
        main()