"""
expand_db2.py — Adds 7 new tables + more rows to existing tables in library2.db
Run AFTER create_db2.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library2.db')

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# ══════════════════════════════════════════════════════════════════
# NEW TABLE 1 — Librarian (library staff)
# ══════════════════════════════════════════════════════════════════
cursor.execute("""
CREATE TABLE IF NOT EXISTS Librarian (
    librarian_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    phone         TEXT,
    role          TEXT NOT NULL,
    shift         TEXT CHECK(shift IN ('Morning','Afternoon','Evening')),
    joining_date  TEXT,
    salary        REAL
)""")

cursor.executemany("INSERT OR IGNORE INTO Librarian (name, email, phone, role, shift, joining_date, salary) VALUES (?,?,?,?,?,?,?)", [
    ('Ravi Kumar',    'ravi@lib.edu',    '9900101', 'Head Librarian',    'Morning',   '2010-06-01', 75000),
    ('Sita Devi',     'sita@lib.edu',    '9900102', 'Deputy Librarian',  'Morning',   '2014-03-15', 55000),
    ('Anil Sharma',   'anil@lib.edu',    '9900103', 'Catalogue Staff',   'Afternoon', '2018-09-01', 35000),
    ('Bindu Nair',    'bindu@lib.edu',   '9900104', 'Circulation Desk',  'Morning',   '2019-01-10', 32000),
    ('Chetan Rao',    'chetan@lib.edu',  '9900105', 'Circulation Desk',  'Afternoon', '2020-07-01', 32000),
    ('Divya Menon',   'divya@lib.edu',   '9900106', 'Digital Resources', 'Evening',   '2021-04-15', 38000),
    ('Eswar Pillai',  'eswar@lib.edu',   '9900107', 'Acquisition',       'Morning',   '2016-11-20', 42000),
    ('Falguni Shah',  'falguni@lib.edu', '9900108', 'Catalogue Staff',   'Evening',   '2022-01-05', 34000),
    ('Ganesh Iyyer',  'ganesh@lib.edu',  '9900109', 'Reference Desk',    'Afternoon', '2017-08-12', 36000),
    ('Hema Reddy',    'hema@lib.edu',    '9900110', 'Reference Desk',    'Evening',   '2023-03-01', 33000),
])

# ══════════════════════════════════════════════════════════════════
# NEW TABLE 2 — LibraryEvent
# ══════════════════════════════════════════════════════════════════
cursor.execute("""
CREATE TABLE IF NOT EXISTS LibraryEvent (
    event_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL,
    description    TEXT,
    event_date     TEXT NOT NULL,
    event_time     TEXT,
    venue          TEXT,
    organizer_id   INTEGER REFERENCES Librarian(librarian_id),
    department_id  INTEGER REFERENCES Department(department_id),
    capacity       INTEGER,
    fee            REAL DEFAULT 0,
    status         TEXT DEFAULT 'Upcoming' CHECK(status IN ('Upcoming','Completed','Cancelled'))
)""")

cursor.executemany("INSERT OR IGNORE INTO LibraryEvent (title, description, event_date, event_time, venue, organizer_id, department_id, capacity, fee, status) VALUES (?,?,?,?,?,?,?,?,?,?)", [
    ('Book Fair 2026',          'Annual book exhibition',      '2026-07-10', '10:00', 'Main Hall',      1, None, 200, 0,   'Upcoming'),
    ('Research Writing Workshop','Academic writing skills',    '2026-07-15', '14:00', 'Seminar Room A', 2, 1,   30,  50,  'Upcoming'),
    ('Python for Data Science', 'Intro to Python',             '2026-06-20', '10:00', 'Lab 1',          6, 1,   40,  0,   'Completed'),
    ('History Talk',            'World history seminar',       '2026-06-05', '15:00', 'Seminar Room B', 9, 4,   50,  0,   'Completed'),
    ('Career Guidance Session', 'MBA career workshop',         '2026-07-20', '11:00', 'Conference Hall',2, 5,   60,  100, 'Upcoming'),
    ('Science Quiz',            'Inter-dept science quiz',     '2026-06-12', '13:00', 'Auditorium',     9, 3,   100, 0,   'Completed'),
    ('Author Meet: Yuval Harari','Discussion on Sapiens book', '2026-08-01', '16:00', 'Main Hall',      1, None, 150, 200, 'Upcoming'),
    ('Journal Citation Workshop','How to cite research papers','2026-07-25', '14:00', 'Seminar Room A', 6, None, 35,  0,   'Upcoming'),
    ('New Member Orientation',  'Library tour for freshers',   '2026-07-05', '09:00', 'Library Lobby',  4, None, 80,  0,   'Upcoming'),
    ('Photography Exhibition',  'Campus life through lens',    '2026-05-30', '11:00', 'Gallery Room',   3, None, 100, 0,   'Completed'),
])

# ══════════════════════════════════════════════════════════════════
# NEW TABLE 3 — EventRegistration
# ══════════════════════════════════════════════════════════════════
cursor.execute("""
CREATE TABLE IF NOT EXISTS EventRegistration (
    reg_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id          INTEGER NOT NULL REFERENCES LibraryEvent(event_id),
    student_id        INTEGER NOT NULL REFERENCES Student(student_id),
    registration_date TEXT NOT NULL,
    attendance_status TEXT DEFAULT 'Registered' CHECK(attendance_status IN ('Registered','Attended','Absent')),
    payment_status    TEXT DEFAULT 'NA' CHECK(payment_status IN ('NA','Paid','Pending'))
)""")

cursor.executemany("INSERT OR IGNORE INTO EventRegistration (event_id, student_id, registration_date, attendance_status, payment_status) VALUES (?,?,?,?,?)", [
    (3,  1,  '2026-06-18', 'Attended',    'NA'),
    (3,  2,  '2026-06-18', 'Attended',    'NA'),
    (3,  7,  '2026-06-18', 'Absent',      'NA'),
    (4,  4,  '2026-06-04', 'Attended',    'NA'),
    (4,  10, '2026-06-04', 'Attended',    'NA'),
    (6,  6,  '2026-06-11', 'Attended',    'NA'),
    (6,  12, '2026-06-11', 'Attended',    'NA'),
    (6,  3,  '2026-06-11', 'Absent',      'NA'),
    (10, 5,  '2026-05-29', 'Attended',    'NA'),
    (10, 8,  '2026-05-29', 'Attended',    'NA'),
    (1,  1,  '2026-07-01', 'Registered',  'NA'),
    (1,  9,  '2026-07-02', 'Registered',  'NA'),
    (2,  2,  '2026-07-05', 'Registered',  'Paid'),
    (5,  11, '2026-07-10', 'Registered',  'Paid'),
    (7,  4,  '2026-07-15', 'Registered',  'Pending'),
])

# ══════════════════════════════════════════════════════════════════
# NEW TABLE 4 — BookReview
# ══════════════════════════════════════════════════════════════════
cursor.execute("""
CREATE TABLE IF NOT EXISTS BookReview (
    review_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id       INTEGER NOT NULL REFERENCES Book(book_id),
    reviewer_type TEXT NOT NULL CHECK(reviewer_type IN ('Student','Faculty')),
    reviewer_id   INTEGER NOT NULL,
    rating        INTEGER CHECK(rating BETWEEN 1 AND 5),
    review_text   TEXT,
    review_date   TEXT NOT NULL,
    helpful_count INTEGER DEFAULT 0
)""")

cursor.executemany("INSERT OR IGNORE INTO BookReview (book_id, reviewer_type, reviewer_id, rating, review_text, review_date, helpful_count) VALUES (?,?,?,?,?,?,?)", [
    (2,  'Student', 1,  5, 'Best book on clean coding practices!',       '2026-05-15', 12),
    (4,  'Faculty', 1,  5, 'Must-read for every CS student.',            '2026-05-20', 20),
    (9,  'Faculty', 3,  4, 'Eye-opening perspective on human history.',  '2026-06-09', 8),
    (7,  'Student', 5,  4, 'Timeless classic, beautifully written.',     '2026-06-16', 5),
    (14, 'Student', 6,  5, 'Explains complex physics very simply.',      '2026-06-04', 9),
    (12, 'Student', 1,  4, 'Great self-help book, very practical.',      '2026-05-02', 6),
    (5,  'Faculty', 2,  5, 'Gold standard DB textbook.',                 '2026-06-11', 15),
    (11, 'Faculty', 7,  4, 'Comprehensive OS reference.',                '2026-06-20', 7),
    (15, 'Student', 8,  5, 'Changed the way I think about habits.',      '2026-06-17', 11),
    (3,  'Faculty', 3,  5, 'Design Patterns is essential for developers.','2026-07-06', 18),
    (8,  'Student', 7,  3, 'Dense read but historically important.',     '2026-06-06', 3),
    (13, 'Student', 10, 4, 'Classic mystery, kept me hooked.',           '2026-06-26', 4),
])

# ══════════════════════════════════════════════════════════════════
# NEW TABLE 5 — DigitalResource
# ══════════════════════════════════════════════════════════════════
cursor.execute("""
CREATE TABLE IF NOT EXISTS DigitalResource (
    resource_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title               TEXT NOT NULL,
    resource_type       TEXT CHECK(resource_type IN ('E-Book','Online Journal','Video Course','Database')),
    url                 TEXT,
    category_id         INTEGER REFERENCES Category(category_id),
    publisher_id        INTEGER REFERENCES Publisher(publisher_id),
    access_type         TEXT DEFAULT 'Restricted' CHECK(access_type IN ('Open','Restricted')),
    subscription_start  TEXT,
    subscription_expiry TEXT,
    cost_per_year       REAL
)""")

cursor.executemany("INSERT OR IGNORE INTO DigitalResource (title, resource_type, url, category_id, publisher_id, access_type, subscription_start, subscription_expiry, cost_per_year) VALUES (?,?,?,?,?,?,?,?,?)", [
    ('IEEE Xplore Digital Library',  'Database',      'ieeexplore.ieee.org', 1, 7, 'Restricted', '2026-01-01', '2026-12-31', 150000),
    ('ACM Digital Library',          'Database',      'dl.acm.org',          2, 4, 'Restricted', '2026-01-01', '2026-12-31', 120000),
    ('JSTOR',                        'Database',      'jstor.org',           6, 6, 'Restricted', '2026-01-01', '2026-12-31', 80000),
    ('Coursera ML Course',           'Video Course',  'coursera.org/ml',     2, None, 'Restricted','2026-01-01','2026-12-31', 50000),
    ('Khan Academy Physics',         'Video Course',  'khanacademy.org',     4, None, 'Open',     None,         None,         0),
    ('O\'Reilly Learning Platform',  'E-Book',        'learning.oreilly.com',2, 2, 'Restricted', '2026-01-01', '2026-12-31', 95000),
    ('Springer eBooks CS',           'E-Book',        'link.springer.com',   1, 5, 'Restricted', '2026-01-01', '2026-12-31', 110000),
    ('HBR Online',                   'Online Journal','hbr.org',             8, 6, 'Restricted', '2026-01-01', '2026-12-31', 45000),
    ('arXiv Preprints',              'Database',      'arxiv.org',           4, None,'Open',      None,         None,         0),
    ('ScienceDirect',                'Database',      'sciencedirect.com',   4, 5, 'Restricted', '2026-01-01', '2026-12-31', 200000),
])

# ══════════════════════════════════════════════════════════════════
# NEW TABLE 6 — DigitalAccess
# ══════════════════════════════════════════════════════════════════
cursor.execute("""
CREATE TABLE IF NOT EXISTS DigitalAccess (
    access_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id      INTEGER NOT NULL REFERENCES DigitalResource(resource_id),
    student_id       INTEGER NOT NULL REFERENCES Student(student_id),
    access_date      TEXT NOT NULL,
    duration_minutes INTEGER,
    device_type      TEXT CHECK(device_type IN ('Desktop','Laptop','Mobile','Tablet'))
)""")

cursor.executemany("INSERT OR IGNORE INTO DigitalAccess (resource_id, student_id, access_date, duration_minutes, device_type) VALUES (?,?,?,?,?)", [
    (1, 1,  '2026-06-01', 45,  'Laptop'),
    (1, 2,  '2026-06-02', 90,  'Desktop'),
    (2, 7,  '2026-06-03', 120, 'Laptop'),
    (4, 1,  '2026-06-04', 60,  'Laptop'),
    (4, 2,  '2026-06-05', 75,  'Mobile'),
    (6, 7,  '2026-06-06', 30,  'Desktop'),
    (3, 4,  '2026-06-07', 50,  'Laptop'),
    (5, 6,  '2026-06-08', 40,  'Mobile'),
    (7, 2,  '2026-06-09', 110, 'Laptop'),
    (8, 11, '2026-06-10', 25,  'Desktop'),
    (1, 9,  '2026-06-11', 80,  'Laptop'),
    (2, 1,  '2026-06-12', 95,  'Desktop'),
    (10,7,  '2026-06-13', 150, 'Laptop'),
    (4, 12, '2026-06-14', 55,  'Tablet'),
    (6, 3,  '2026-06-15', 35,  'Laptop'),
])

# ══════════════════════════════════════════════════════════════════
# NEW TABLE 7 — BookRequest
# ══════════════════════════════════════════════════════════════════
cursor.execute("""
CREATE TABLE IF NOT EXISTS BookRequest (
    request_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   INTEGER NOT NULL REFERENCES Student(student_id),
    book_title   TEXT NOT NULL,
    author_name  TEXT,
    category_id  INTEGER REFERENCES Category(category_id),
    reason       TEXT,
    request_date TEXT NOT NULL,
    status       TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Approved','Rejected','Ordered')),
    handled_by   INTEGER REFERENCES Librarian(librarian_id)
)""")

cursor.executemany("INSERT OR IGNORE INTO BookRequest (student_id, book_title, author_name, category_id, reason, request_date, status, handled_by) VALUES (?,?,?,?,?,?,?,?)", [
    (1,  'Cracking the Coding Interview', 'Gayle McDowell',   2, 'Placement preparation',    '2026-05-10', 'Ordered',  1),
    (2,  'Deep Learning',                 'Goodfellow et al', 2, 'Research requirement',      '2026-05-12', 'Approved', 1),
    (7,  'Distributed Systems',           'Tanenbaum',        1, 'PhD coursework',            '2026-05-15', 'Ordered',  7),
    (4,  'The Great Gatsby',              'Fitzgerald',       7, 'Literature course',         '2026-05-18', 'Rejected', 2),
    (11, 'Good to Great',                 'Jim Collins',      8, 'MBA elective reading',      '2026-05-20', 'Approved', 2),
    (3,  'Linear Algebra Done Right',     'Sheldon Axler',    5, 'Advanced math course',      '2026-06-01', 'Pending',  None),
    (6,  'University Physics',            'Young & Freedman', 4, 'Lab reference',             '2026-06-03', 'Pending',  None),
    (9,  'System Design Interview',       'Alex Xu',          2, 'Internship preparation',    '2026-06-05', 'Approved', 7),
    (12, 'Quantum Mechanics',             'Griffiths',        4, 'M.Sc Physics project',      '2026-06-08', 'Pending',  None),
    (5,  'Competitive Strategy',          'Michael Porter',   8, 'BBA strategy course',       '2026-06-10', 'Pending',  None),
    (8,  'Electric Circuits',             'Nilsson',          1, 'EE core subject',           '2026-06-12', 'Ordered',  7),
    (10, 'Modern Literary Theory',        'Raman Selden',     6, 'PhD research',              '2026-06-14', 'Approved', 2),
])

# ══════════════════════════════════════════════════════════════════
# MORE ROWS in existing tables
# ══════════════════════════════════════════════════════════════════

# 5 more Books
cursor.executemany("INSERT OR IGNORE INTO Book (isbn, title, publisher_id, category_id, shelf_id, publication_year, edition, language, total_copies, available_copies, price, reorder_threshold) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
    ('978-0-13-468609-7', 'Cracking the Coding Interview', 1, 2, 1, 2015, 6, 'English', 3, 2, 1200, 2),
    ('978-0-262-03561-2', 'Deep Learning',                 5, 2, 2, 2016, 1, 'English', 2, 1, 3500, 1),
    ('978-0-13-294594-7', 'Computer Networks',             1, 1, 6, 2010, 5, 'English', 4, 3, 2200, 2),
    ('978-0-19-964769-6', 'Oxford English Dictionary',     6, 6, 7, 2010, 2, 'English', 2, 2, 4500, 1),
    ('978-0-06-112008-4', 'To Kill a Mockingbird',         3, 7, 4, 1960, 1, 'English', 3, 3, 380,  1),
])

# 5 more Students
cursor.executemany("INSERT OR IGNORE INTO Student (first_name, last_name, email, phone, department_id, enrollment_year, program, student_type, membership_expiry) VALUES (?,?,?,?,?,?,?,?,?)", [
    ('Ishaan',  'Bose',     'ishaan@uni.edu',   '9900013', 1, 2023, 'B.Tech CSE',   'Undergraduate', '2026-12-31'),
    ('Jayanti', 'Das',      'jayanti@uni.edu',  '9900014', 2, 2022, 'M.Sc Math',    'Postgraduate',  '2026-12-31'),
    ('Karan',   'Malhotra', 'karan@uni.edu',    '9900015', 5, 2021, 'MBA',          'Postgraduate',  '2026-12-31'),
    ('Lakshmi', 'Pillai',   'lakshmi@uni.edu',  '9900016', 3, 2023, 'B.Sc Physics', 'Undergraduate', '2026-12-31'),
    ('Manish',  'Tiwari',   'manish@uni.edu',   '9900017', 6, 2022, 'B.Tech EE',    'Undergraduate', '2026-12-31'),
])

# 5 more Loans
cursor.executemany("INSERT OR IGNORE INTO Loan (book_id, borrower_type, borrower_id, issue_date, due_date, return_date, renewed_count, issued_by) VALUES (?,?,?,?,?,?,?,?)", [
    (16, 'Student', 1,  '2026-06-17', '2026-07-01', None,         0, 'librarian1'),
    (17, 'Student', 7,  '2026-06-18', '2026-07-02', None,         0, 'librarian2'),
    (20, 'Student', 13, '2026-06-18', '2026-07-02', None,         0, 'librarian1'),
    (18, 'Faculty', 6,  '2026-06-19', '2026-07-19', None,         0, 'librarian2'),
    (19, 'Student', 14, '2026-06-19', '2026-07-03', None,         0, 'librarian1'),
])

conn.commit()
conn.close()

# Summary
conn2 = sqlite3.connect(DB_PATH)
cursor2 = conn2.cursor()
cursor2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
tables = cursor2.fetchall()
print(f"\nlibrary2.db updated successfully!")
print(f"Total tables: {len(tables)}")
print()
for t in tables:
    cursor2.execute(f"SELECT COUNT(*) FROM {t[0]}")
    count = cursor2.fetchone()[0]
    cursor2.execute(f"PRAGMA table_info({t[0]})")
    cols = len(cursor2.fetchall())
    print(f"  {t[0]:25s}: {cols:2d} columns, {count:3d} rows")
conn2.close()
