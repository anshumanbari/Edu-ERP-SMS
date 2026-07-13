# EduCore SMS — Domain Architecture

Status: living document. Reflects actual entity relationships in `app/models/` as of 2026-07-13. Documentation only — no code, APIs, or DB schema created or changed by this session. Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md).

## 1. Purpose

Section 3 of the Product Architecture named business domains and module boundaries. This document goes one level deeper: the entities inside each domain, how they relate to each other (including *across* domain boundaries via foreign keys), who owns each entity, and the invariants that make the domain model consistent.

## 2. Domain Map

```
Identity & Access ─┐
                    ├─▶ referenced by nearly every domain (marked_by_id, teacher_id, etc.)
Academic Structure ─┤
  Department        │
   └─ Program        │
       ├─ Semester    │
       │   ├─ Section  │
       │   └─ Course    │
       │       └─ Subject
       └─ Section
Classroom (standalone, referenced by Timetable)

People
  Student
  Teacher

Enrollment ──▶ links Student × AcademicSession × Program × Semester × Section

Scheduling
  Timetable ──▶ Section × Subject × Teacher × Classroom × AcademicSession

Attendance ──▶ Student × Subject × AcademicSession × User(marked_by)

Examination & Results
  Examination ──▶ Subject × AcademicSession
  ExamMark ──▶ Examination × Student × Teacher
  Result ──▶ Student × AcademicSession (aggregate)

Fees
  FeeStructure ──▶ Program × Semester × AcademicSession
  FeePayment ──▶ Student × FeeStructure

Dashboard ──▶ read-only aggregation over all of the above
```

## 3. Entities per Domain

### 3.1 Identity & Access
- **User** — `id, name, email(unique), hashed_password, role`. Root identity for anyone who authenticates (admin/teacher/staff-style accounts — not the same record as a `Student` or `Teacher` profile).
- Owns: authentication and role. Referenced by `Attendance.marked_by_id` today; the natural anchor for `created_by`/`updated_by` audit fields on future write-heavy domains.

### 3.2 Academic Structure
- **Department** — `name(unique), code(unique), is_active`. Root of the academic hierarchy.
- **Program** — belongs to `Department`. E.g., a degree/major.
- **Semester** — belongs to `Program`, has `sequence_number`. A term within a program.
- **Section** — belongs to `Program` **and** `Semester`. A cohort/class group within a semester.
- **Course** — belongs to `Semester`, has `credit_hours`.
- **Subject** — belongs to `Course`.
- **Classroom** — standalone (`room_number, building, capacity`), no FK to the academic hierarchy; it's a physical resource, referenced only by `Timetable`.
- **AcademicSession** — standalone (`session_name, start_date, end_date, status, is_current`). The time-boundary ("2025-26", "Fall 2026") that Enrollment, Attendance, Examination, Timetable, and Fees all pin themselves to.

Hierarchy: `Department → Program → Semester → {Section, Course → Subject}`. `AcademicSession` and `Classroom` sit outside this tree and are composed in by other domains per-transaction (e.g., a Timetable row picks one Section, one Subject, one Teacher, one Classroom, one AcademicSession).

### 3.3 People
- **Student** — `name, email(unique), phone(BigInteger), course, semester`. Note: `Student.course`/`Student.semester` are currently free-form/legacy fields predating the Academic Structure hierarchy (see Section 6, Known Gaps) — the authoritative link to Program/Semester/Section is `Enrollment`, not these columns.
- **Teacher** — `name, email(unique), phone(BigInteger), subject, experience_years`. Similarly, `Teacher.subject` is a legacy free-text field; the authoritative subject/section link is `TeacherAssignment`.

### 3.4 Enrollment
- **Enrollment** — `student_id, academic_session_id, program_id, semester_id, section_id, enrollment_date, status`. The join entity that places a Student into a specific Program/Semester/Section for a specific AcademicSession. This is the domain that should be treated as the source of truth for "what is this student currently studying," not `Student.course`/`Student.semester`.

### 3.5 Scheduling
- **Timetable** — `section_id, subject_id, teacher_id, classroom_id, academic_session_id, day_of_week, start_time, end_time`. A recurring weekly slot; the entity that ties People (Teacher), Academic Structure (Section, Subject), and physical resources (Classroom) together in time.
- **TeacherAssignment** (People/Scheduling boundary) — `teacher_id, subject_id, section_id, academic_session_id, is_active`. Declares which teacher is authorized/assigned to teach a subject to a section in a session; Timetable slots are expected to be consistent with active TeacherAssignments (not currently enforced at the DB level — an application-level invariant).

### 3.6 Attendance
- **Attendance** — `student_id, subject_id, academic_session_id, attendance_date, status, marked_by_id(→User)`. One row per student per subject per date. `marked_by_id` is the only place a `User` (Identity) is referenced from a domain entity today.

### 3.7 Examination & Results
- **Examination** — `name, subject_id, academic_session_id, exam_date, max_marks, passing_marks`. A single exam event for one subject.
- **ExamMark** — `examination_id, student_id, teacher_id, marks_obtained`. One row per student per examination — the raw score.
- **Result** — `student_id, academic_session_id, total_marks_obtained, total_max_marks, percentage, status, is_published, published_at`. A computed/aggregated rollup per student per session — **not** per-examination. Result is derived from ExamMark data (aggregated across a session's examinations), not a parent of ExamMark. This is a one-way derivation: Result depends on ExamMark, never the reverse.

### 3.8 Fees
- **FeeStructure** — `name, program_id, semester_id, academic_session_id, amount, due_date, is_active`. Defines what's owed for a Program/Semester/Session combination.
- **FeePayment** — `student_id, fee_structure_id, amount_paid, payment_date`. Records what a specific student paid against a FeeStructure. A student's outstanding balance is a derived value (`FeeStructure.amount − Σ FeePayment.amount_paid`), not a stored column.

### 3.9 Dashboard
No entities of its own. Composes read views by calling into the CRUD of the domains above (per `services/<area>_service.py`), shaped by `schemas/<area>.py` aggregate response models. Never writes.

## 4. Cross-Domain Relationships (Foreign Key Graph)

| Entity | FKs to | Relationship meaning |
|---|---|---|
| Program | Department | Program belongs to a Department |
| Semester | Program | Semester belongs to a Program |
| Section | Program, Semester | Section belongs to a Program and a Semester |
| Course | Semester | Course belongs to a Semester |
| Subject | Course | Subject belongs to a Course |
| Enrollment | Student, AcademicSession, Program, Semester, Section | Places a Student in the academic hierarchy for a session |
| TeacherAssignment | Teacher, Subject, Section, AcademicSession | Assigns a Teacher to teach a Subject to a Section in a session |
| Timetable | Section, Subject, Teacher, Classroom, AcademicSession | A scheduled weekly slot |
| Attendance | Student, Subject, AcademicSession, User(marked_by) | Attendance record for a student, subject, date, session |
| Examination | Subject, AcademicSession | An exam event |
| ExamMark | Examination, Student, Teacher | A student's score on an exam |
| Result | Student, AcademicSession | A computed rollup |
| FeeStructure | Program, Semester, AcademicSession | What's owed |
| FeePayment | Student, FeeStructure | What was paid |

**AcademicSession is the most heavily-referenced entity outside the core hierarchy** — Enrollment, TeacherAssignment, Timetable, Attendance, Examination, FeeStructure all pin to it. It functions as the system's time-partitioning key: nearly every transactional domain scopes its records to "which session was this in."

## 5. Domain Ownership & Write Authority

Each entity has exactly one owning domain/module responsible for writing it (per Product Architecture §3's CRUD-per-domain pattern):

- Academic Structure owns Department/Program/Semester/Section/Course/Subject/Classroom/AcademicSession.
- People owns Student/Teacher.
- Enrollment owns Enrollment (reads People + Academic Structure, writes only its own join table).
- Scheduling owns Timetable and TeacherAssignment.
- Attendance owns Attendance.
- Examination & Results owns Examination, ExamMark, and Result — Result is written by this domain's own aggregation logic (or a future batch job), never by Dashboard.
- Fees owns FeeStructure and FeePayment.
- Dashboard owns nothing; read-only.

No domain writes another domain's table. Where one entity needs data from another domain's hierarchy (e.g., Enrollment needing a valid `program_id`), that's expressed as a foreign key, validated at the application layer in that entity's own `crud` module — not by reaching into the other domain's CRUD internals to mutate its data.

## 6. Known Gaps / Legacy Inconsistencies (documented, not fixed in this session)

- `Student.course` (string) and `Student.semester` (int) predate the Academic Structure hierarchy and Enrollment. They are not kept in sync with `Enrollment`/`Program`/`Semester` today. Any new feature should treat `Enrollment` as authoritative and treat these two columns as legacy/display-only.
- `Teacher.subject` (string) is similarly legacy relative to `TeacherAssignment`.
- TeacherAssignment↔Timetable consistency (a Timetable slot's teacher/subject/section should match an active TeacherAssignment) is not DB-enforced — it's an application invariant only.
- `Result` aggregation logic (how ExamMark rows roll up into a Result row) lives in the Examination & Results domain's responsibility but its computation trigger (on-demand vs. batch vs. on-publish) is not specified by the current model layer alone.

These are noted for future architecture/decision sessions (see `docs/06_DECISIONS/` per the Product Architecture's recommended doc structure) — no remediation is scoped here.

## 7. Domain Invariants Worth Naming

- A `Section` is always scoped to exactly one `Program` and one `Semester` — it cannot span programs.
- An `Enrollment` row's `program_id`/`semester_id`/`section_id` should be mutually consistent (the Section must belong to the given Program/Semester) — an application-level invariant, not currently a DB constraint.
- `Result.status`/`is_published` gate visibility: a Result existing does not imply it's visible to the student — `is_published` is the authorization gate, separate from the data being computed.
- `FeePayment` rows are additive-only against a `FeeStructure` (partial payments accumulate); there's no "void/refund" entity yet — a payment correction would currently require a negative-amount row or a new domain concept, not covered by the current model.
