"""
Part 3: School Management System - PyQt5 GUI

Reuses the OOP model from part1_oop.py. Lets you add/edit/delete
students, instructors and courses, register/assign via dropdowns,
browse everything in a QTableWidget, search, save/load to JSON,
and export the current view to CSV.
"""

import csv
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QFormLayout, QTabWidget, QMessageBox, QFileDialog, QHeaderView,
)

from part1_oop import SchoolManager, Student, Instructor, Course, ValidationError

DATA_FILE = "school_data.json"


class SchoolWindow(QMainWindow):
    """Main application window for the School Management System GUI.

    Wraps a :class:`part1_oop.SchoolManager` instance and presents it
    through tabbed add/register forms, a search bar, a results table
    and an action bar for delete/save/load/export operations.

    :ivar manager: The underlying data model
    :vartype manager: part1_oop.SchoolManager
    :ivar selected_row_key: ``(kind, id)`` of the currently selected table row, or None
    :vartype selected_row_key: tuple[str, str] or None
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("School Management System")
        self.resize(1000, 650)
        self.manager = SchoolManager()
        self.selected_row_key = None   # (kind, id) of the row selected in the table

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addWidget(self._build_tabs())
        layout.addLayout(self._build_search_bar())
        layout.addWidget(self._build_table())
        layout.addLayout(self._build_action_bar())

        self.refresh_table()

    # ------------------------------------------------------------------ UI
    def _build_tabs(self):
        """Build the Student/Instructor/Course tab widget with its add and
        register/assign forms.

        :return: The fully wired tab widget
        :rtype: PyQt5.QtWidgets.QTabWidget
        """
        tabs = QTabWidget()

        # ---- Student tab ----
        student_tab = QWidget()
        form = QFormLayout(student_tab)
        self.s_id = QLineEdit()
        self.s_name = QLineEdit()
        self.s_age = QLineEdit()
        self.s_email = QLineEdit()
        form.addRow("Student ID:", self.s_id)
        form.addRow("Name:", self.s_name)
        form.addRow("Age:", self.s_age)
        form.addRow("Email:", self.s_email)
        add_student_btn = QPushButton("Add Student")
        add_student_btn.clicked.connect(self.add_student)
        form.addRow(add_student_btn)

        self.s_course_dropdown = QComboBox()
        self.s_reg_id = QLineEdit()
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.register_course)
        reg_row = QHBoxLayout()
        reg_row.addWidget(QLabel("Student ID:"))
        reg_row.addWidget(self.s_reg_id)
        reg_row.addWidget(QLabel("Course:"))
        reg_row.addWidget(self.s_course_dropdown)
        reg_row.addWidget(register_btn)
        form.addRow(reg_row)
        tabs.addTab(student_tab, "Student")

        # ---- Instructor tab ----
        instr_tab = QWidget()
        form = QFormLayout(instr_tab)
        self.i_id = QLineEdit()
        self.i_name = QLineEdit()
        self.i_age = QLineEdit()
        self.i_email = QLineEdit()
        form.addRow("Instructor ID:", self.i_id)
        form.addRow("Name:", self.i_name)
        form.addRow("Age:", self.i_age)
        form.addRow("Email:", self.i_email)
        add_instr_btn = QPushButton("Add Instructor")
        add_instr_btn.clicked.connect(self.add_instructor)
        form.addRow(add_instr_btn)

        self.i_course_dropdown = QComboBox()
        self.i_assign_id = QLineEdit()
        assign_btn = QPushButton("Assign")
        assign_btn.clicked.connect(self.assign_course)
        assign_row = QHBoxLayout()
        assign_row.addWidget(QLabel("Instructor ID:"))
        assign_row.addWidget(self.i_assign_id)
        assign_row.addWidget(QLabel("Course:"))
        assign_row.addWidget(self.i_course_dropdown)
        assign_row.addWidget(assign_btn)
        form.addRow(assign_row)
        tabs.addTab(instr_tab, "Instructor")

        # ---- Course tab ----
        course_tab = QWidget()
        form = QFormLayout(course_tab)
        self.c_id = QLineEdit()
        self.c_name = QLineEdit()
        form.addRow("Course ID:", self.c_id)
        form.addRow("Course Name:", self.c_name)
        add_course_btn = QPushButton("Add Course")
        add_course_btn.clicked.connect(self.add_course)
        form.addRow(add_course_btn)
        tabs.addTab(course_tab, "Course")

        return tabs

    def _build_search_bar(self):
        """Build the search row (search box + clear button) that filters the table.

        :return: The search bar layout
        :rtype: PyQt5.QtWidgets.QHBoxLayout
        """
        row = QHBoxLayout()
        row.addWidget(QLabel("Search (name / ID / course):"))
        self.search_box = QLineEdit()
        self.search_box.textChanged.connect(self.refresh_table)
        row.addWidget(self.search_box)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.search_box.setText(""))
        row.addWidget(clear_btn)
        return row

    def _build_table(self):
        """Build the results table listing students, instructors and courses.

        :return: The configured table widget
        :rtype: PyQt5.QtWidgets.QTableWidget
        """
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Type", "ID", "Name", "Age / Instructor", "Email / Enrolled Students"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_select)
        return self.table

    def _build_action_bar(self):
        """Build the bottom action bar (delete/save/load/export buttons).

        :return: The action bar layout
        :rtype: PyQt5.QtWidgets.QHBoxLayout
        """
        row = QHBoxLayout()
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected)
        save_btn = QPushButton("Save to File")
        save_btn.clicked.connect(self.save_data)
        load_btn = QPushButton("Load from File")
        load_btn.clicked.connect(self.load_data)
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        for btn in (delete_btn, save_btn, load_btn, export_btn):
            row.addWidget(btn)
        return row

    # ------------------------------------------------------------- helpers
    def _on_select(self):
        """Update :attr:`selected_row_key` from the currently selected table row."""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.selected_row_key = None
            return
        row = rows[0].row()
        kind = self.table.item(row, 0).text().lower()
        obj_id = self.table.item(row, 1).text()
        self.selected_row_key = (kind, obj_id)

    def refresh_table(self):
        """Repopulate the table from the manager, applying the current search term,
        and refresh the course dropdowns.
        """
        term = self.search_box.text().strip()
        self.table.setRowCount(0)

        rows = []
        students = self.manager.search_students(term) if term else self.manager.students.values()
        for s in students:
            rows.append(("Student", s.student_id, s.name, str(s.age), s.email))

        instructors = self.manager.search_instructors(term) if term else self.manager.instructors.values()
        for i in instructors:
            rows.append(("Instructor", i.instructor_id, i.name, str(i.age), i.email))

        courses = self.manager.search_courses(term) if term else self.manager.courses.values()
        for c in courses:
            instr_name = c.instructor.name if c.instructor else "(unassigned)"
            students_str = ", ".join(s.name for s in c.enrolled_students) or "(none)"
            rows.append(("Course", c.course_id, c.course_name, instr_name, students_str))

        self.table.setRowCount(len(rows))
        for r, values in enumerate(rows):
            for col, value in enumerate(values):
                self.table.setItem(r, col, QTableWidgetItem(value))

        self._refresh_dropdowns()

    def _refresh_dropdowns(self):
        """Repopulate the student-registration and instructor-assignment course dropdowns."""
        course_labels = [f"{c.course_id} - {c.course_name}" for c in self.manager.courses.values()]
        self.s_course_dropdown.clear()
        self.s_course_dropdown.addItems(course_labels)
        self.i_course_dropdown.clear()
        self.i_course_dropdown.addItems(course_labels)

    def _course_id_from_dropdown(self, dropdown):
        """Extract the course ID from a ``"ID - Name"`` dropdown entry.

        :param dropdown: The combo box to read from
        :type dropdown: PyQt5.QtWidgets.QComboBox
        :return: The course ID, or None if the dropdown is empty
        :rtype: str or None
        """
        value = dropdown.currentText()
        return value.split(" - ")[0] if value else None

    # -------------------------------------------------------------- actions
    def add_student(self):
        """Read the Student tab's form fields, validate and add a new student,
        then clear the form and refresh the table. Shows an error dialog on
        invalid input.
        """
        try:
            student = Student(self.s_name.text().strip(), int(self.s_age.text()), self.s_email.text().strip(), self.s_id.text().strip())
            self.manager.add_student(student)
        except (ValidationError, ValueError) as e:
            QMessageBox.critical(self, "Invalid data", str(e))
            return
        for field in (self.s_id, self.s_name, self.s_age, self.s_email):
            field.clear()
        self.refresh_table()

    def add_instructor(self):
        """Read the Instructor tab's form fields, validate and add a new instructor,
        then clear the form and refresh the table. Shows an error dialog on
        invalid input.
        """
        try:
            instructor = Instructor(self.i_name.text().strip(), int(self.i_age.text()), self.i_email.text().strip(), self.i_id.text().strip())
            self.manager.add_instructor(instructor)
        except (ValidationError, ValueError) as e:
            QMessageBox.critical(self, "Invalid data", str(e))
            return
        for field in (self.i_id, self.i_name, self.i_age, self.i_email):
            field.clear()
        self.refresh_table()

    def add_course(self):
        """Read the Course tab's form fields, validate and add a new course,
        then clear the form and refresh the table. Shows an error dialog on
        invalid input.
        """
        try:
            course = Course(self.c_id.text().strip(), self.c_name.text().strip())
            self.manager.add_course(course)
        except ValidationError as e:
            QMessageBox.critical(self, "Invalid data", str(e))
            return
        for field in (self.c_id, self.c_name):
            field.clear()
        self.refresh_table()

    def register_course(self):
        """Register the student ID typed in the Student tab for the selected course.

        Shows an error dialog if the student ID or course selection is invalid.
        """
        course_id = self._course_id_from_dropdown(self.s_course_dropdown)
        student = self.manager.students.get(self.s_reg_id.text().strip())
        course = self.manager.courses.get(course_id)
        if not student or not course:
            QMessageBox.critical(self, "Error", "Pick a valid Student ID and course.")
            return
        student.register_course(course)
        self.s_reg_id.clear()
        self.refresh_table()

    def assign_course(self):
        """Assign the instructor ID typed in the Instructor tab to the selected course.

        Shows an error dialog if the instructor ID or course selection is invalid.
        """
        course_id = self._course_id_from_dropdown(self.i_course_dropdown)
        instructor = self.manager.instructors.get(self.i_assign_id.text().strip())
        course = self.manager.courses.get(course_id)
        if not instructor or not course:
            QMessageBox.critical(self, "Error", "Pick a valid Instructor ID and course.")
            return
        instructor.assign_course(course)
        self.i_assign_id.clear()
        self.refresh_table()

    def delete_selected(self):
        """Delete the currently selected table row's student/instructor/course
        from the manager, then refresh the table.
        """
        if not self.selected_row_key:
            QMessageBox.information(self, "Delete", "Select a row first.")
            return
        kind, obj_id = self.selected_row_key
        if kind == "student":
            self.manager.remove_student(obj_id)
        elif kind == "instructor":
            self.manager.remove_instructor(obj_id)
        elif kind == "course":
            self.manager.remove_course(obj_id)
        self.selected_row_key = None
        self.refresh_table()

    def save_data(self):
        """Save the current manager state to :data:`DATA_FILE` as JSON."""
        self.manager.save_to_file(DATA_FILE)
        QMessageBox.information(self, "Save", f"Saved to {DATA_FILE}")

    def load_data(self):
        """Replace the current manager with the state loaded from :data:`DATA_FILE`
        and refresh the table. Shows an error dialog if the file doesn't exist.
        """
        try:
            self.manager = SchoolManager.load_from_file(DATA_FILE)
        except FileNotFoundError:
            QMessageBox.critical(self, "Load", f"{DATA_FILE} not found. Save first.")
            return
        self.refresh_table()
        QMessageBox.information(self, "Load", f"Loaded from {DATA_FILE}")

    def export_csv(self):
        """Prompt for a destination file and export the currently visible table
        rows (respecting the active search filter) to CSV.
        """
        path, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "school_export.csv", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
            writer.writerow(headers)
            for r in range(self.table.rowCount()):
                writer.writerow([self.table.item(r, c).text() for c in range(self.table.columnCount())])
        QMessageBox.information(self, "Export", f"Exported to {path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SchoolWindow()
    window.show()
    sys.exit(app.exec_())
