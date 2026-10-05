"""
Part 2: School Management System - Tkinter GUI

Reuses the OOP model from part1_oop.py. Lets you add/edit/delete
students, instructors and courses, register/assign via dropdowns,
browse everything in a Treeview, search, and save/load to JSON.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from part1_oop import SchoolManager, Student, Instructor, Course, ValidationError

DATA_FILE = "school_data.json"


class SchoolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("School Management System")
        self.geometry("900x600")
        self.manager = SchoolManager()
        self.selected_iid = None   # (kind, id) of the row selected in the tree

        self._build_menu()
        self._build_forms()
        self._build_tree()
        self._build_search()
        self.refresh_tree()

    # ------------------------------------------------------------------ UI
    def _build_menu(self):
        bar = tk.Menu(self)
        filemenu = tk.Menu(bar, tearoff=0)
        filemenu.add_command(label="Save", command=self.save_data)
        filemenu.add_command(label="Load", command=self.load_data)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        bar.add_cascade(label="File", menu=filemenu)
        self.config(menu=bar)

    def _build_forms(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="x", padx=10, pady=10)

        # ---- Student tab ----
        student_tab = ttk.Frame(notebook)
        notebook.add(student_tab, text="Student")
        self.s_id = tk.Entry(student_tab)
        self.s_name = tk.Entry(student_tab)
        self.s_age = tk.Entry(student_tab)
        self.s_email = tk.Entry(student_tab)
        for i, (label, widget) in enumerate([
            ("Student ID", self.s_id), ("Name", self.s_name),
            ("Age", self.s_age), ("Email", self.s_email)
        ]):
            tk.Label(student_tab, text=label).grid(row=0, column=2 * i, padx=4, pady=6)
            widget.grid(row=0, column=2 * i + 1, padx=4, pady=6)
        tk.Button(student_tab, text="Add Student", command=self.add_student).grid(row=0, column=8, padx=6)

        tk.Label(student_tab, text="Register in course:").grid(row=1, column=0, padx=4, pady=6)
        self.s_course_dropdown = ttk.Combobox(student_tab, state="readonly", width=25)
        self.s_course_dropdown.grid(row=1, column=1, padx=4, pady=6)
        tk.Label(student_tab, text="Student ID:").grid(row=1, column=2, padx=4)
        self.s_reg_id = tk.Entry(student_tab)
        self.s_reg_id.grid(row=1, column=3, padx=4)
        tk.Button(student_tab, text="Register", command=self.register_course).grid(row=1, column=4, padx=6)

        # ---- Instructor tab ----
        instr_tab = ttk.Frame(notebook)
        notebook.add(instr_tab, text="Instructor")
        self.i_id = tk.Entry(instr_tab)
        self.i_name = tk.Entry(instr_tab)
        self.i_age = tk.Entry(instr_tab)
        self.i_email = tk.Entry(instr_tab)
        for i, (label, widget) in enumerate([
            ("Instructor ID", self.i_id), ("Name", self.i_name),
            ("Age", self.i_age), ("Email", self.i_email)
        ]):
            tk.Label(instr_tab, text=label).grid(row=0, column=2 * i, padx=4, pady=6)
            widget.grid(row=0, column=2 * i + 1, padx=4, pady=6)
        tk.Button(instr_tab, text="Add Instructor", command=self.add_instructor).grid(row=0, column=8, padx=6)

        tk.Label(instr_tab, text="Assign course:").grid(row=1, column=0, padx=4, pady=6)
        self.i_course_dropdown = ttk.Combobox(instr_tab, state="readonly", width=25)
        self.i_course_dropdown.grid(row=1, column=1, padx=4, pady=6)
        tk.Label(instr_tab, text="Instructor ID:").grid(row=1, column=2, padx=4)
        self.i_assign_id = tk.Entry(instr_tab)
        self.i_assign_id.grid(row=1, column=3, padx=4)
        tk.Button(instr_tab, text="Assign", command=self.assign_course).grid(row=1, column=4, padx=6)

        # ---- Course tab ----
        course_tab = ttk.Frame(notebook)
        notebook.add(course_tab, text="Course")
        self.c_id = tk.Entry(course_tab)
        self.c_name = tk.Entry(course_tab)
        for i, (label, widget) in enumerate([("Course ID", self.c_id), ("Course Name", self.c_name)]):
            tk.Label(course_tab, text=label).grid(row=0, column=2 * i, padx=4, pady=6)
            widget.grid(row=0, column=2 * i + 1, padx=4, pady=6)
        tk.Button(course_tab, text="Add Course", command=self.add_course).grid(row=0, column=4, padx=6)

        # ---- Edit/Delete ----
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=10)
        tk.Button(action_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=4)
        tk.Button(action_frame, text="Save to File", command=self.save_data).pack(side="left", padx=4)
        tk.Button(action_frame, text="Load from File", command=self.load_data).pack(side="left", padx=4)

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
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        headers = ["Type", "ID", "Name", "Age / Instructor", "Email / Enrolled Students"]
        for col, head in zip(columns, headers):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=160)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    # ------------------------------------------------------------- helpers
    def _on_select(self, _event):
        selection = self.tree.selection()
        self.selected_iid = selection[0] if selection else None

    def refresh_tree(self):
        term = self.search_var.get().strip()
        self.tree.delete(*self.tree.get_children())

        students = self.manager.search_students(term) if term else self.manager.students.values()
        for s in students:
            self.tree.insert("", "end", iid=f"student:{s.student_id}", values=(
                "Student", s.student_id, s.name, s.age, s.email))

        instructors = self.manager.search_instructors(term) if term else self.manager.instructors.values()
        for i in instructors:
            self.tree.insert("", "end", iid=f"instructor:{i.instructor_id}", values=(
                "Instructor", i.instructor_id, i.name, i.age, i.email))

        courses = self.manager.search_courses(term) if term else self.manager.courses.values()
        for c in courses:
            instr_name = c.instructor.name if c.instructor else "(unassigned)"
            students_str = ", ".join(s.name for s in c.enrolled_students) or "(none)"
            self.tree.insert("", "end", iid=f"course:{c.course_id}", values=(
                "Course", c.course_id, c.course_name, instr_name, students_str))

        self._refresh_dropdowns()

    def _refresh_dropdowns(self):
        course_labels = [f"{c.course_id} - {c.course_name}" for c in self.manager.courses.values()]
        self.s_course_dropdown["values"] = course_labels
        self.i_course_dropdown["values"] = course_labels

    def _course_id_from_dropdown(self, dropdown):
        value = dropdown.get()
        return value.split(" - ")[0] if value else None

    # -------------------------------------------------------------- actions
    def add_student(self):
        try:
            student = Student(self.s_name.get().strip(), int(self.s_age.get()), self.s_email.get().strip(), self.s_id.get().strip())
            self.manager.add_student(student)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Invalid data", str(e))
            return
        for entry in (self.s_id, self.s_name, self.s_age, self.s_email):
            entry.delete(0, tk.END)
        self.refresh_tree()

    def add_instructor(self):
        try:
            instructor = Instructor(self.i_name.get().strip(), int(self.i_age.get()), self.i_email.get().strip(), self.i_id.get().strip())
            self.manager.add_instructor(instructor)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Invalid data", str(e))
            return
        for entry in (self.i_id, self.i_name, self.i_age, self.i_email):
            entry.delete(0, tk.END)
        self.refresh_tree()

    def add_course(self):
        try:
            course = Course(self.c_id.get().strip(), self.c_name.get().strip())
            self.manager.add_course(course)
        except ValidationError as e:
            messagebox.showerror("Invalid data", str(e))
            return
        for entry in (self.c_id, self.c_name):
            entry.delete(0, tk.END)
        self.refresh_tree()

    def register_course(self):
        course_id = self._course_id_from_dropdown(self.s_course_dropdown)
        student = self.manager.students.get(self.s_reg_id.get().strip())
        course = self.manager.courses.get(course_id)
        if not student or not course:
            messagebox.showerror("Error", "Pick a valid Student ID and course.")
            return
        student.register_course(course)
        self.s_reg_id.delete(0, tk.END)
        self.refresh_tree()

    def assign_course(self):
        course_id = self._course_id_from_dropdown(self.i_course_dropdown)
        instructor = self.manager.instructors.get(self.i_assign_id.get().strip())
        course = self.manager.courses.get(course_id)
        if not instructor or not course:
            messagebox.showerror("Error", "Pick a valid Instructor ID and course.")
            return
        instructor.assign_course(course)
        self.i_assign_id.delete(0, tk.END)
        self.refresh_tree()

    def delete_selected(self):
        if not self.selected_iid:
            messagebox.showinfo("Delete", "Select a row first.")
            return
        kind, _, obj_id = self.selected_iid.partition(":")
        if kind == "student":
            self.manager.remove_student(obj_id)
        elif kind == "instructor":
            self.manager.remove_instructor(obj_id)
        elif kind == "course":
            self.manager.remove_course(obj_id)
        self.selected_iid = None
        self.refresh_tree()

    def save_data(self):
        self.manager.save_to_file(DATA_FILE)
        messagebox.showinfo("Save", f"Saved to {DATA_FILE}")

    def load_data(self):
        try:
            self.manager = SchoolManager.load_from_file(DATA_FILE)
        except FileNotFoundError:
            messagebox.showerror("Load", f"{DATA_FILE} not found. Save first.")
            return
        self.refresh_tree()
        messagebox.showinfo("Load", f"Loaded from {DATA_FILE}")


if __name__ == "__main__":
    app = SchoolApp()
    app.mainloop()
