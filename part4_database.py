"""
Part 4: Database Integration

- SchoolDB: SQLite schema + CRUD operations for students, instructors,
  courses and enrollments, plus backup/restore of the .db file.
- SchoolDBApp: a Tkinter GUI (same look & feel as Part 2) wired to
  SchoolDB instead of the JSON-based SchoolManager, demonstrating
  "connect PyQt5/Tkinter to SQLite".
"""

import os
import shutil
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from part1_oop import EMAIL_PATTERN, ValidationError

DB_FILE = "school.db"
BACKUP_DIR = "backups"


class SchoolDB:
    """Thin CRUD layer around a SQLite database for the school schema."""

    def __init__(self, path=DB_FILE):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS instructors (
                instructor_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                course_name TEXT NOT NULL,
                instructor_id TEXT REFERENCES instructors(instructor_id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS enrollments (
                student_id TEXT REFERENCES students(student_id) ON DELETE CASCADE,
                course_id TEXT REFERENCES courses(course_id) ON DELETE CASCADE,
                PRIMARY KEY (student_id, course_id)
            );
        """)
        self.conn.commit()

    @staticmethod
    def _validate_person(name, age, email):
        if not name:
            raise ValidationError("Name is required")
        if not isinstance(age, int) or age < 0:
            raise ValidationError(f"Age must be a non-negative integer, got {age!r}")
        if not EMAIL_PATTERN.match(email or ""):
            raise ValidationError(f"Invalid email format: {email!r}")

    # ---------------------------------------------------------- students
    def create_student(self, student_id, name, age, email):
        self._validate_person(name, age, email)
        self.conn.execute(
            "INSERT INTO students (student_id, name, age, email) VALUES (?, ?, ?, ?)",
            (student_id, name, age, email))
        self.conn.commit()

    def get_students(self):
        return self.conn.execute("SELECT * FROM students ORDER BY student_id").fetchall()

    def update_student(self, student_id, name, age, email):
        self._validate_person(name, age, email)
        self.conn.execute(
            "UPDATE students SET name=?, age=?, email=? WHERE student_id=?",
            (name, age, email, student_id))
        self.conn.commit()

    def delete_student(self, student_id):
        self.conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        self.conn.commit()

    # -------------------------------------------------------- instructors
    def create_instructor(self, instructor_id, name, age, email):
        self._validate_person(name, age, email)
        self.conn.execute(
            "INSERT INTO instructors (instructor_id, name, age, email) VALUES (?, ?, ?, ?)",
            (instructor_id, name, age, email))
        self.conn.commit()

    def get_instructors(self):
        return self.conn.execute("SELECT * FROM instructors ORDER BY instructor_id").fetchall()

    def update_instructor(self, instructor_id, name, age, email):
        self._validate_person(name, age, email)
        self.conn.execute(
            "UPDATE instructors SET name=?, age=?, email=? WHERE instructor_id=?",
            (name, age, email, instructor_id))
        self.conn.commit()

    def delete_instructor(self, instructor_id):
        self.conn.execute("DELETE FROM instructors WHERE instructor_id=?", (instructor_id,))
        self.conn.commit()

    # ------------------------------------------------------------ courses
    def create_course(self, course_id, course_name, instructor_id=None):
        if not course_name:
            raise ValidationError("Course name is required")
        self.conn.execute(
            "INSERT INTO courses (course_id, course_name, instructor_id) VALUES (?, ?, ?)",
            (course_id, course_name, instructor_id))
        self.conn.commit()

    def get_courses(self):
        return self.conn.execute("""
            SELECT c.course_id, c.course_name, c.instructor_id, i.name
            FROM courses c LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
            ORDER BY c.course_id
        """).fetchall()

    def assign_instructor(self, course_id, instructor_id):
        self.conn.execute(
            "UPDATE courses SET instructor_id=? WHERE course_id=?", (instructor_id, course_id))
        self.conn.commit()

    def delete_course(self, course_id):
        self.conn.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
        self.conn.commit()

    # -------------------------------------------------------- enrollments
    def enroll(self, student_id, course_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO enrollments (student_id, course_id) VALUES (?, ?)",
            (student_id, course_id))
        self.conn.commit()

    def unenroll(self, student_id, course_id):
        self.conn.execute(
            "DELETE FROM enrollments WHERE student_id=? AND course_id=?", (student_id, course_id))
        self.conn.commit()

    def get_courses_for_student(self, student_id):
        return self.conn.execute("""
            SELECT c.course_id, c.course_name FROM courses c
            JOIN enrollments e ON c.course_id = e.course_id
            WHERE e.student_id=?
        """, (student_id,)).fetchall()

    def get_students_for_course(self, course_id):
        return self.conn.execute("""
            SELECT s.student_id, s.name FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            WHERE e.course_id=?
        """, (course_id,)).fetchall()

    # -------------------------------------------------------- search
    def search(self, term):
        term = f"%{term}%"
        students = self.conn.execute(
            "SELECT * FROM students WHERE name LIKE ? OR student_id LIKE ?", (term, term)).fetchall()
        instructors = self.conn.execute(
            "SELECT * FROM instructors WHERE name LIKE ? OR instructor_id LIKE ?", (term, term)).fetchall()
        courses = self.conn.execute(
            "SELECT * FROM courses WHERE course_name LIKE ? OR course_id LIKE ?", (term, term)).fetchall()
        return students, instructors, courses

    # -------------------------------------------------------- backup/restore
    def backup(self, backup_dir=BACKUP_DIR):
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(backup_dir, f"school_{timestamp}.db")
        self.conn.commit()
        shutil.copy2(self.path, dest)
        return dest

    def restore(self, backup_path):
        self.conn.close()
        shutil.copy2(backup_path, self.path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self):
        self.conn.close()


class SchoolDBApp(tk.Tk):
    """Tkinter front-end for SchoolDB (Part 4 deliverable)."""

    def __init__(self):
        super().__init__()
        self.title("School Management System - SQLite")
        self.geometry("950x620")
        self.db = SchoolDB()
        self.selected_iid = None

        self._build_forms()
        self._build_search()
        self._build_tree()
        self._build_backup_bar()
        self.refresh_tree()

    # ------------------------------------------------------------------ UI
    def _build_forms(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="x", padx=10, pady=10)

        student_tab = ttk.Frame(notebook)
        notebook.add(student_tab, text="Student")
        self.s_id, self.s_name, self.s_age, self.s_email = (tk.Entry(student_tab) for _ in range(4))
        for i, (label, widget) in enumerate(zip(
                ["Student ID", "Name", "Age", "Email"], [self.s_id, self.s_name, self.s_age, self.s_email])):
            tk.Label(student_tab, text=label).grid(row=0, column=2 * i, padx=4, pady=6)
            widget.grid(row=0, column=2 * i + 1, padx=4, pady=6)
        tk.Button(student_tab, text="Add Student", command=self.add_student).grid(row=0, column=8, padx=6)

        tk.Label(student_tab, text="Student ID:").grid(row=1, column=0, padx=4)
        self.s_reg_id = tk.Entry(student_tab)
        self.s_reg_id.grid(row=1, column=1, padx=4)
        tk.Label(student_tab, text="Course:").grid(row=1, column=2, padx=4)
        self.s_course_dropdown = ttk.Combobox(student_tab, state="readonly", width=25)
        self.s_course_dropdown.grid(row=1, column=3, padx=4)
        tk.Button(student_tab, text="Register", command=self.register_course).grid(row=1, column=4, padx=6)

        instr_tab = ttk.Frame(notebook)
        notebook.add(instr_tab, text="Instructor")
        self.i_id, self.i_name, self.i_age, self.i_email = (tk.Entry(instr_tab) for _ in range(4))
        for i, (label, widget) in enumerate(zip(
                ["Instructor ID", "Name", "Age", "Email"], [self.i_id, self.i_name, self.i_age, self.i_email])):
            tk.Label(instr_tab, text=label).grid(row=0, column=2 * i, padx=4, pady=6)
            widget.grid(row=0, column=2 * i + 1, padx=4, pady=6)
        tk.Button(instr_tab, text="Add Instructor", command=self.add_instructor).grid(row=0, column=8, padx=6)

        tk.Label(instr_tab, text="Instructor ID:").grid(row=1, column=0, padx=4)
        self.i_assign_id = tk.Entry(instr_tab)
        self.i_assign_id.grid(row=1, column=1, padx=4)
        tk.Label(instr_tab, text="Course:").grid(row=1, column=2, padx=4)
        self.i_course_dropdown = ttk.Combobox(instr_tab, state="readonly", width=25)
        self.i_course_dropdown.grid(row=1, column=3, padx=4)
        tk.Button(instr_tab, text="Assign", command=self.assign_course).grid(row=1, column=4, padx=6)

        course_tab = ttk.Frame(notebook)
        notebook.add(course_tab, text="Course")
        self.c_id = tk.Entry(course_tab)
        self.c_name = tk.Entry(course_tab)
        for i, (label, widget) in enumerate([("Course ID", self.c_id), ("Course Name", self.c_name)]):
            tk.Label(course_tab, text=label).grid(row=0, column=2 * i, padx=4, pady=6)
            widget.grid(row=0, column=2 * i + 1, padx=4, pady=6)
        tk.Button(course_tab, text="Add Course", command=self.add_course).grid(row=0, column=4, padx=6)

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=10)
        tk.Button(actions, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=4)

    def _build_search(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(frame, text="Search (name / ID / course):").pack(side="left")
        self.search_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=self.search_var, width=30)
        entry.pack(side="left", padx=6)
        entry.bind("<KeyRelease>", lambda e: self.refresh_tree())
        tk.Button(frame, text="Clear", command=lambda: (self.search_var.set(""), self.refresh_tree())).pack(side="left")

    def _build_tree(self):
        columns = ("type", "id", "name", "age_or_instructor", "email_or_students")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        headers = ["Type", "ID", "Name", "Age / Instructor", "Email / Enrolled Students"]
        for col, head in zip(columns, headers):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=160)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _build_backup_bar(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(frame, text="Backup Database", command=self.backup_db).pack(side="left", padx=4)
        tk.Label(frame, text="Restore from:").pack(side="left", padx=(20, 4))
        self.backup_dropdown = ttk.Combobox(frame, state="readonly", width=35)
        self.backup_dropdown.pack(side="left", padx=4)
        tk.Button(frame, text="Refresh List", command=self.refresh_backups).pack(side="left", padx=4)
        tk.Button(frame, text="Restore", command=self.restore_db).pack(side="left", padx=4)
        self.refresh_backups()

    # ------------------------------------------------------------- helpers
    def _on_select(self, _event):
        selection = self.tree.selection()
        self.selected_iid = selection[0] if selection else None

    def refresh_tree(self):
        term = self.search_var.get().strip()
        self.tree.delete(*self.tree.get_children())

        if term:
            students, instructors, courses = self.db.search(term)
        else:
            students, instructors, courses = self.db.get_students(), self.db.get_instructors(), self.db.get_courses()

        for sid, name, age, email in students:
            self.tree.insert("", "end", iid=f"student:{sid}", values=("Student", sid, name, age, email))
        for iid_, name, age, email in instructors:
            self.tree.insert("", "end", iid=f"instructor:{iid_}", values=("Instructor", iid_, name, age, email))
        for row in courses:
            if len(row) == 4:
                cid, cname, instr_id, instr_name = row
            else:
                cid, cname, instr_id = row
                instr_name = None
            students_str = ", ".join(n for _, n in self.db.get_students_for_course(cid)) or "(none)"
            self.tree.insert("", "end", iid=f"course:{cid}", values=(
                "Course", cid, cname, instr_name or "(unassigned)", students_str))

        self._refresh_dropdowns()

    def _refresh_dropdowns(self):
        labels = [f"{cid} - {cname}" for cid, cname, *_ in self.db.get_courses()]
        self.s_course_dropdown["values"] = labels
        self.i_course_dropdown["values"] = labels

    def refresh_backups(self):
        if os.path.isdir(BACKUP_DIR):
            files = sorted(os.listdir(BACKUP_DIR), reverse=True)
        else:
            files = []
        self.backup_dropdown["values"] = files

    def _course_id_from_dropdown(self, dropdown):
        value = dropdown.get()
        return value.split(" - ")[0] if value else None

    # -------------------------------------------------------------- actions
    def add_student(self):
        try:
            self.db.create_student(self.s_id.get().strip(), self.s_name.get().strip(),
                                    int(self.s_age.get()), self.s_email.get().strip())
        except (ValidationError, ValueError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Invalid data", str(e))
            return
        for entry in (self.s_id, self.s_name, self.s_age, self.s_email):
            entry.delete(0, tk.END)
        self.refresh_tree()

    def add_instructor(self):
        try:
            self.db.create_instructor(self.i_id.get().strip(), self.i_name.get().strip(),
                                       int(self.i_age.get()), self.i_email.get().strip())
        except (ValidationError, ValueError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Invalid data", str(e))
            return
        for entry in (self.i_id, self.i_name, self.i_age, self.i_email):
            entry.delete(0, tk.END)
        self.refresh_tree()

    def add_course(self):
        try:
            self.db.create_course(self.c_id.get().strip(), self.c_name.get().strip())
        except (ValidationError, sqlite3.IntegrityError) as e:
            messagebox.showerror("Invalid data", str(e))
            return
        for entry in (self.c_id, self.c_name):
            entry.delete(0, tk.END)
        self.refresh_tree()

    def register_course(self):
        course_id = self._course_id_from_dropdown(self.s_course_dropdown)
        student_id = self.s_reg_id.get().strip()
        if not course_id or not student_id:
            messagebox.showerror("Error", "Pick a valid Student ID and course.")
            return
        self.db.enroll(student_id, course_id)
        self.s_reg_id.delete(0, tk.END)
        self.refresh_tree()

    def assign_course(self):
        course_id = self._course_id_from_dropdown(self.i_course_dropdown)
        instructor_id = self.i_assign_id.get().strip()
        if not course_id or not instructor_id:
            messagebox.showerror("Error", "Pick a valid Instructor ID and course.")
            return
        self.db.assign_instructor(course_id, instructor_id)
        self.i_assign_id.delete(0, tk.END)
        self.refresh_tree()

    def delete_selected(self):
        if not self.selected_iid:
            messagebox.showinfo("Delete", "Select a row first.")
            return
        kind, _, obj_id = self.selected_iid.partition(":")
        if kind == "student":
            self.db.delete_student(obj_id)
        elif kind == "instructor":
            self.db.delete_instructor(obj_id)
        elif kind == "course":
            self.db.delete_course(obj_id)
        self.selected_iid = None
        self.refresh_tree()

    def backup_db(self):
        dest = self.db.backup()
        self.refresh_backups()
        messagebox.showinfo("Backup", f"Database backed up to {dest}")

    def restore_db(self):
        choice = self.backup_dropdown.get()
        if not choice:
            messagebox.showinfo("Restore", "Pick a backup file first.")
            return
        if not messagebox.askyesno("Restore", f"Overwrite current database with {choice}?"):
            return
        self.db.restore(os.path.join(BACKUP_DIR, choice))
        self.refresh_tree()
        messagebox.showinfo("Restore", f"Database restored from {choice}")


if __name__ == "__main__":
    app = SchoolDBApp()
    app.mainloop()
