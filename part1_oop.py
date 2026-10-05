"""
Part 1: School Management System - Pure Python OOP

Classes: Person, Student, Instructor, Course
Includes validation (email format, non-negative age) and JSON
serialization so the same data model can be reused by the Tkinter
and PyQt5 GUIs in Part 2 / Part 3.
"""

import json
import re
from datetime import datetime

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    """Raised when Person/Course data fails validation."""
    pass


class Person:
    """Base class for anyone in the school (encapsulation + abstraction).

    :param name: Full name of the person
    :type name: str
    :param age: Age in years; must be a non-negative integer
    :type age: int
    :param email: Email address; validated against a basic email pattern
    :type email: str
    :raises ValidationError: If ``age`` or ``email`` fail validation
    """

    def __init__(self, name, age, email):
        self.name = name
        self.age = age          # goes through the age.setter -> validated
        self._email = None
        self.email = email      # goes through the email.setter -> validated

    @property
    def age(self):
        """int: The person's age. Setting it validates it is a non-negative integer."""
        return self._age

    @age.setter
    def age(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValidationError(f"Age must be a non-negative integer, got {value!r}")
        self._age = value

    @property
    def email(self):
        """str: The person's email. Setting it validates the address format."""
        return self._email

    @email.setter
    def email(self, value):
        if not EMAIL_PATTERN.match(value or ""):
            raise ValidationError(f"Invalid email format: {value!r}")
        self._email = value

    def introduce(self):
        """Build a short human-readable introduction for this person.

        :return: A sentence with the person's name, age and email
        :rtype: str
        """
        return f"Hi, I'm {self.name}, {self.age} years old ({self._email})."

    def to_dict(self):
        """Serialize this person to a plain dict (for JSON export).

        :return: Dict with ``name``, ``age`` and ``email`` keys
        :rtype: dict
        """
        return {"name": self.name, "age": self.age, "email": self._email}


class Student(Person):
    """A student enrolled at the school.

    :param name: Full name of the student
    :type name: str
    :param age: Age in years
    :type age: int
    :param email: Email address
    :type email: str
    :param student_id: Unique student identifier
    :type student_id: str
    :ivar registered_courses: Courses this student is currently registered in
    :vartype registered_courses: list[Course]
    """

    def __init__(self, name, age, email, student_id):
        super().__init__(name, age, email)
        self.student_id = student_id
        self.registered_courses = []   # list[Course]

    def register_course(self, course):
        """Enroll this student in a course (keeps both sides in sync).

        :param course: The course to register for
        :type course: Course
        """
        course.add_student(self)

    def introduce(self):
        """Build an introduction including the student ID and registered courses.

        :return: A sentence describing this student
        :rtype: str
        """
        courses = ", ".join(c.course_name for c in self.registered_courses) or "none"
        return f"{super().introduce()} I'm a student (ID {self.student_id}), registered in: {courses}."

    def to_dict(self):
        """Serialize this student, including type marker and registered course IDs.

        :return: Dict representation suitable for JSON export
        :rtype: dict
        """
        data = super().to_dict()
        data.update({
            "type": "Student",
            "student_id": self.student_id,
            "registered_courses": [c.course_id for c in self.registered_courses],
        })
        return data

    @classmethod
    def from_dict(cls, data):
        """Rebuild a :class:`Student` from a dict produced by :meth:`to_dict`.

        :param data: Dict with ``name``, ``age``, ``email`` and ``student_id`` keys
        :type data: dict
        :return: The reconstructed student
        :rtype: Student
        """
        return cls(data["name"], data["age"], data["email"], data["student_id"])


class Instructor(Person):
    """An instructor who can be assigned to teach courses.

    :param name: Full name of the instructor
    :type name: str
    :param age: Age in years
    :type age: int
    :param email: Email address
    :type email: str
    :param instructor_id: Unique instructor identifier
    :type instructor_id: str
    :ivar assigned_courses: Courses this instructor currently teaches
    :vartype assigned_courses: list[Course]
    """

    def __init__(self, name, age, email, instructor_id):
        super().__init__(name, age, email)
        self.instructor_id = instructor_id
        self.assigned_courses = []     # list[Course]

    def assign_course(self, course):
        """Assign this instructor to teach a course.

        :param course: The course to teach
        :type course: Course
        """
        course.instructor = self
        if course not in self.assigned_courses:
            self.assigned_courses.append(course)

    def introduce(self):
        """Build an introduction including the instructor ID and taught courses.

        :return: A sentence describing this instructor
        :rtype: str
        """
        courses = ", ".join(c.course_name for c in self.assigned_courses) or "none"
        return f"{super().introduce()} I'm an instructor (ID {self.instructor_id}), teaching: {courses}."

    def to_dict(self):
        """Serialize this instructor, including type marker and taught course IDs.

        :return: Dict representation suitable for JSON export
        :rtype: dict
        """
        data = super().to_dict()
        data.update({
            "type": "Instructor",
            "instructor_id": self.instructor_id,
            "assigned_courses": [c.course_id for c in self.assigned_courses],
        })
        return data

    @classmethod
    def from_dict(cls, data):
        """Rebuild an :class:`Instructor` from a dict produced by :meth:`to_dict`.

        :param data: Dict with ``name``, ``age``, ``email`` and ``instructor_id`` keys
        :type data: dict
        :return: The reconstructed instructor
        :rtype: Instructor
        """
        return cls(data["name"], data["age"], data["email"], data["instructor_id"])


class Course:
    """A course, optionally taught by an instructor and enrolling students.

    :param course_id: Unique course identifier
    :type course_id: str
    :param course_name: Human-readable course name
    :type course_name: str
    :param instructor: Instructor teaching the course, defaults to None
    :type instructor: Instructor, optional
    :ivar enrolled_students: Students currently enrolled in the course
    :vartype enrolled_students: list[Student]
    """

    def __init__(self, course_id, course_name, instructor=None):
        self.course_id = course_id
        self.course_name = course_name
        self.instructor = instructor
        self.enrolled_students = []    # list[Student]

    def add_student(self, student):
        """Enroll a student, keeping Course <-> Student in sync.

        :param student: The student to enroll
        :type student: Student
        """
        if student not in self.enrolled_students:
            self.enrolled_students.append(student)
        if self not in student.registered_courses:
            student.registered_courses.append(self)

    def remove_student(self, student):
        """Unenroll a student, keeping Course <-> Student in sync.

        :param student: The student to remove
        :type student: Student
        """
        if student in self.enrolled_students:
            self.enrolled_students.remove(student)
        if self in student.registered_courses:
            student.registered_courses.remove(self)

    def to_dict(self):
        """Serialize this course to a plain dict (for JSON export).

        :return: Dict with course id/name, instructor id and enrolled student ids
        :rtype: dict
        """
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "instructor_id": self.instructor.instructor_id if self.instructor else None,
            "enrolled_students": [s.student_id for s in self.enrolled_students],
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a :class:`Course` from a dict produced by :meth:`to_dict`.

        Instructor/student relationships are re-linked separately by
        :meth:`SchoolManager.load_from_file`, not by this constructor.

        :param data: Dict with ``course_id`` and ``course_name`` keys
        :type data: dict
        :return: The reconstructed course (without relationships)
        :rtype: Course
        """
        return cls(data["course_id"], data["course_name"])

    def __repr__(self):
        return f"Course({self.course_id}, {self.course_name!r})"


class SchoolManager:
    """Owns all Students/Instructors/Courses; handles lookup + JSON persistence.

    :ivar students: All students, keyed by ``student_id``
    :vartype students: dict[str, Student]
    :ivar instructors: All instructors, keyed by ``instructor_id``
    :vartype instructors: dict[str, Instructor]
    :ivar courses: All courses, keyed by ``course_id``
    :vartype courses: dict[str, Course]
    """

    def __init__(self):
        self.students = {}      # student_id -> Student
        self.instructors = {}   # instructor_id -> Instructor
        self.courses = {}       # course_id -> Course

    # ---- add ----
    def add_student(self, student):
        """Register a new student.

        :param student: The student to add
        :type student: Student
        :raises ValidationError: If the student ID is already in use
        :return: The same student, for convenient chaining
        :rtype: Student
        """
        if student.student_id in self.students:
            raise ValidationError(f"Student ID {student.student_id} already exists")
        self.students[student.student_id] = student
        return student

    def add_instructor(self, instructor):
        """Register a new instructor.

        :param instructor: The instructor to add
        :type instructor: Instructor
        :raises ValidationError: If the instructor ID is already in use
        :return: The same instructor, for convenient chaining
        :rtype: Instructor
        """
        if instructor.instructor_id in self.instructors:
            raise ValidationError(f"Instructor ID {instructor.instructor_id} already exists")
        self.instructors[instructor.instructor_id] = instructor
        return instructor

    def add_course(self, course):
        """Register a new course.

        :param course: The course to add
        :type course: Course
        :raises ValidationError: If the course ID is already in use
        :return: The same course, for convenient chaining
        :rtype: Course
        """
        if course.course_id in self.courses:
            raise ValidationError(f"Course ID {course.course_id} already exists")
        self.courses[course.course_id] = course
        return course

    # ---- remove ----
    def remove_student(self, student_id):
        """Remove a student and unenroll them from every registered course.

        :param student_id: ID of the student to remove
        :type student_id: str
        """
        student = self.students.pop(student_id, None)
        if student:
            for course in list(student.registered_courses):
                course.remove_student(student)

    def remove_instructor(self, instructor_id):
        """Remove an instructor and unassign them from every taught course.

        :param instructor_id: ID of the instructor to remove
        :type instructor_id: str
        """
        instructor = self.instructors.pop(instructor_id, None)
        if instructor:
            for course in self.courses.values():
                if course.instructor is instructor:
                    course.instructor = None

    def remove_course(self, course_id):
        """Remove a course and unlink it from its students and instructor.

        :param course_id: ID of the course to remove
        :type course_id: str
        """
        course = self.courses.pop(course_id, None)
        if course:
            for student in list(course.enrolled_students):
                course.remove_student(student)
            if course.instructor and course in course.instructor.assigned_courses:
                course.instructor.assigned_courses.remove(course)

    # ---- search ----
    def search_students(self, term):
        """Find students whose name or ID contains ``term`` (case-insensitive).

        :param term: Search text
        :type term: str
        :return: Matching students
        :rtype: list[Student]
        """
        term = term.lower()
        return [s for s in self.students.values()
                if term in s.name.lower() or term in s.student_id.lower()]

    def search_instructors(self, term):
        """Find instructors whose name or ID contains ``term`` (case-insensitive).

        :param term: Search text
        :type term: str
        :return: Matching instructors
        :rtype: list[Instructor]
        """
        term = term.lower()
        return [i for i in self.instructors.values()
                if term in i.name.lower() or term in i.instructor_id.lower()]

    def search_courses(self, term):
        """Find courses whose name or ID contains ``term`` (case-insensitive).

        :param term: Search text
        :type term: str
        :return: Matching courses
        :rtype: list[Course]
        """
        term = term.lower()
        return [c for c in self.courses.values()
                if term in c.course_name.lower() or term in c.course_id.lower()]

    # ---- persistence ----
    def save_to_file(self, path):
        """Serialize all students, instructors and courses to a JSON file.

        :param path: Destination file path
        :type path: str
        """
        data = {
            "students": [s.to_dict() for s in self.students.values()],
            "instructors": [i.to_dict() for i in self.instructors.values()],
            "courses": [c.to_dict() for c in self.courses.values()],
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, path):
        """Load a :class:`SchoolManager` from a JSON file written by :meth:`save_to_file`.

        Re-links instructor/student/course relationships after all objects
        have been reconstructed.

        :param path: Source file path
        :type path: str
        :return: A populated manager
        :rtype: SchoolManager
        """
        with open(path) as f:
            data = json.load(f)

        manager = cls()

        for item in data.get("instructors", []):
            manager.add_instructor(Instructor.from_dict(item))
        for item in data.get("students", []):
            manager.add_student(Student.from_dict(item))
        for item in data.get("courses", []):
            manager.add_course(Course.from_dict(item))

        # Re-link relationships now that every object exists
        for item in data.get("courses", []):
            course = manager.courses[item["course_id"]]
            if item.get("instructor_id"):
                instructor = manager.instructors.get(item["instructor_id"])
                if instructor:
                    instructor.assign_course(course)
            for sid in item.get("enrolled_students", []):
                student = manager.students.get(sid)
                if student:
                    course.add_student(student)

        return manager


def _demo():
    """Console walkthrough of the OOP concepts (Part 1 deliverable)."""
    manager = SchoolManager()

    prof = manager.add_instructor(Instructor("Dr. Alice Karam", 45, "alice.karam@aub.edu.lb", "I001"))
    student1 = manager.add_student(Student("Tarek Fares", 20, "tarek.fares@mail.aub.edu", "S001"))
    student2 = manager.add_student(Student("Mia Chahine", 21, "mia.chahine@mail.aub.edu", "S002"))
    course = manager.add_course(Course("C001", "Software Tools Lab"))

    prof.assign_course(course)
    student1.register_course(course)
    student2.register_course(course)

    print("=== Inheritance & Polymorphism (same introduce() call, different output) ===")
    for person in [prof, student1, student2]:
        print(person.introduce())

    print("\n=== Encapsulation (private _email via property) ===")
    print("student1 raw email property:", student1.email)

    print("\n=== Validation ===")
    try:
        Student("Bad Age", -5, "bad@mail.com", "S999")
    except ValidationError as e:
        print("Caught expected error:", e)
    try:
        Student("Bad Email", 20, "not-an-email", "S998")
    except ValidationError as e:
        print("Caught expected error:", e)

    print("\n=== Serialization (save/load) ===")
    manager.save_to_file("school_data.json")
    print("Saved to school_data.json")
    reloaded = SchoolManager.load_from_file("school_data.json")
    print("Reloaded students:", [s.introduce() for s in reloaded.students.values()])


if __name__ == "__main__":
    _demo()
