import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library2.db')

def create_database():
    if os.path.exists(DB_PATH):
        confirm = input(f"library2.db already exists. Overwrite? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.executescript("""

    -- 1. Department
    CREATE TABLE IF NOT EXISTS Department (
        department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        building        TEXT NOT NULL,
        floor           INTEGER NOT NULL,
        head_name       TEXT NOT NULL,
        phone           TEXT,
        email           TEXT,
        established_year INTEGER
    );

    -- 2. Category
    CREATE TABLE IF NOT EXISTS Category (
        category_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT NOT NULL,
        description      TEXT,
        dewey_decimal    TEXT,
        parent_category_id INTEGER REFERENCES Category(category_id)
    );

    -- 3. Publisher
    CREATE TABLE IF NOT EXISTS Publisher (
        publisher_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT NOT NULL,
        country          TEXT NOT NULL,
        city             TEXT NOT NULL,
        website          TEXT,
        email            TEXT,
        phone            TEXT,
        established_year INTEGER
    );

    -- 4. Author
    CREATE TABLE IF NOT EXISTS Author (
        author_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name   TEXT NOT NULL,
        last_name    TEXT NOT NULL,
        nationality  TEXT,
        birth_year   INTEGER,
        email        TEXT,
        bio          TEXT
    );

    -- 5. Shelf
    CREATE TABLE IF NOT EXISTS Shelf (
        shelf_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        shelf_code    TEXT NOT NULL UNIQUE,
        floor         INTEGER NOT NULL,
        section       TEXT NOT NULL,
        row_number    INTEGER NOT NULL,
        capacity      INTEGER NOT NULL,
        current_count INTEGER DEFAULT 0
    );

    -- 6. Book
    CREATE TABLE IF NOT EXISTS Book (
        book_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn             TEXT UNIQUE,
        title            TEXT NOT NULL,
        publisher_id     INTEGER REFERENCES Publisher(publisher_id),
        category_id      INTEGER REFERENCES Category(category_id),
        shelf_id         INTEGER REFERENCES Shelf(shelf_id),
        publication_year INTEGER,
        edition          INTEGER DEFAULT 1,
        language         TEXT DEFAULT 'English',
        total_copies     INTEGER DEFAULT 1,
        available_copies INTEGER DEFAULT 1,
        price            REAL,
        reorder_threshold INTEGER DEFAULT 2
    );

    -- 7. BookAuthor (junction)
    CREATE TABLE IF NOT EXISTS BookAuthor (
        ba_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id   INTEGER NOT NULL REFERENCES Book(book_id),
        author_id INTEGER NOT NULL REFERENCES Author(author_id),
        role      TEXT DEFAULT 'Author'
    );

    -- 8. Journal
    CREATE TABLE IF NOT EXISTS Journal (
        journal_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        title            TEXT NOT NULL,
        issn             TEXT UNIQUE,
        publisher_id     INTEGER REFERENCES Publisher(publisher_id),
        category_id      INTEGER REFERENCES Category(category_id),
        frequency        TEXT,
        impact_factor    REAL,
        available_issues INTEGER DEFAULT 0
    );

    -- 9. Student
    CREATE TABLE IF NOT EXISTS Student (
        student_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name        TEXT NOT NULL,
        last_name         TEXT NOT NULL,
        email             TEXT UNIQUE NOT NULL,
        phone             TEXT,
        department_id     INTEGER REFERENCES Department(department_id),
        enrollment_year   INTEGER,
        program           TEXT,
        student_type      TEXT CHECK(student_type IN ('Undergraduate','Postgraduate','PhD')),
        membership_expiry TEXT
    );

    -- 10. Faculty
    CREATE TABLE IF NOT EXISTS Faculty (
        faculty_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name    TEXT NOT NULL,
        last_name     TEXT NOT NULL,
        email         TEXT UNIQUE NOT NULL,
        phone         TEXT,
        department_id INTEGER REFERENCES Department(department_id),
        designation   TEXT,
        employee_id   TEXT UNIQUE,
        joining_date  TEXT
    );

    -- 11. Loan
    CREATE TABLE IF NOT EXISTS Loan (
        loan_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id        INTEGER NOT NULL REFERENCES Book(book_id),
        borrower_type  TEXT NOT NULL CHECK(borrower_type IN ('Student','Faculty')),
        borrower_id    INTEGER NOT NULL,
        issue_date     TEXT NOT NULL,
        due_date       TEXT NOT NULL,
        return_date    TEXT,
        renewed_count  INTEGER DEFAULT 0,
        issued_by      TEXT
    );

    -- 12. Reservation
    CREATE TABLE IF NOT EXISTS Reservation (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id        INTEGER NOT NULL REFERENCES Book(book_id),
        borrower_type  TEXT NOT NULL CHECK(borrower_type IN ('Student','Faculty')),
        borrower_id    INTEGER NOT NULL,
        reserved_on    TEXT NOT NULL,
        expires_on     TEXT NOT NULL,
        status         TEXT DEFAULT 'Active' CHECK(status IN ('Active','Fulfilled','Expired','Cancelled'))
    );

    -- 13. Fine
    CREATE TABLE IF NOT EXISTS Fine (
        fine_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        loan_id     INTEGER NOT NULL REFERENCES Loan(loan_id),
        fine_amount REAL NOT NULL,
        reason      TEXT NOT NULL,
        issued_date TEXT NOT NULL,
        paid_date   TEXT,
        status      TEXT DEFAULT 'Unpaid' CHECK(status IN ('Unpaid','Paid','Waived'))
    );

    -- 14. Supplier
    CREATE TABLE IF NOT EXISTS Supplier (
        supplier_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        contact_person  TEXT,
        phone           TEXT,
        email           TEXT,
        address         TEXT,
        city            TEXT,
        country         TEXT DEFAULT 'India',
        rating          REAL
    );

    -- 15. PurchaseOrder
    CREATE TABLE IF NOT EXISTS PurchaseOrder (
        po_id             INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id       INTEGER NOT NULL REFERENCES Supplier(supplier_id),
        order_date        TEXT NOT NULL,
        expected_delivery TEXT,
        status            TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Delivered','Cancelled','Partial')),
        total_amount      REAL,
        ordered_by        TEXT
    );

    -- 16. PurchaseOrderItem
    CREATE TABLE IF NOT EXISTS PurchaseOrderItem (
        poi_id             INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id              INTEGER NOT NULL REFERENCES PurchaseOrder(po_id),
        book_id            INTEGER NOT NULL REFERENCES Book(book_id),
        quantity_ordered   INTEGER NOT NULL,
        unit_price         REAL NOT NULL,
        quantity_received  INTEGER DEFAULT 0
    );

    """)

    # ── Sample Data ────────────────────────────────────────────

    cursor.executemany("INSERT INTO Department (name, building, floor, head_name, phone, email, established_year) VALUES (?,?,?,?,?,?,?)", [
        ('Computer Science',    'Block A', 3, 'Dr. Sharma',   '9811001001', 'cs@uni.edu',      1985),
        ('Mathematics',         'Block B', 2, 'Dr. Mehta',    '9811001002', 'math@uni.edu',    1970),
        ('Physics',             'Block B', 1, 'Dr. Kapoor',   '9811001003', 'physics@uni.edu', 1968),
        ('Literature',          'Block C', 2, 'Dr. Nair',     '9811001004', 'lit@uni.edu',     1972),
        ('Business',            'Block D', 4, 'Dr. Gupta',    '9811001005', 'biz@uni.edu',     1990),
        ('Electrical Engg',     'Block A', 2, 'Dr. Singh',    '9811001006', 'ee@uni.edu',      1980),
    ])

    cursor.executemany("INSERT INTO Category (name, description, dewey_decimal, parent_category_id) VALUES (?,?,?,?)", [
        ('Technology',       'Tech and computing books',        '600', None),
        ('Programming',      'Software development',            '005', 1),
        ('Database',         'Database systems',                '005.74', 2),
        ('Science',          'Natural sciences',                '500', None),
        ('Mathematics',      'Pure and applied mathematics',    '510', 4),
        ('Literature',       'Fiction and non-fiction',         '800', None),
        ('Classic Fiction',  'Classic literary works',          '823', 6),
        ('Business',         'Management and economics',        '650', None),
        ('Self Help',        'Personal development',            '158', None),
        ('History',          'World and regional history',      '900', None),
    ])

    cursor.executemany("INSERT INTO Publisher (name, country, city, website, email, phone, established_year) VALUES (?,?,?,?,?,?,?)", [
        ('Pearson Education',   'USA',   'New York',   'pearson.com',    'info@pearson.com',   '+1-800-111', 1844),
        ('O\'Reilly Media',     'USA',   'Sebastopol', 'oreilly.com',    'info@oreilly.com',   '+1-800-222', 1978),
        ('Penguin Books',       'UK',    'London',     'penguin.com',    'info@penguin.com',   '+44-800-333',1935),
        ('McGraw Hill',         'USA',   'New York',   'mcgraw.com',     'info@mcgraw.com',    '+1-800-444', 1888),
        ('Springer',            'Germany','Berlin',    'springer.com',   'info@springer.com',  '+49-800-555',1842),
        ('Oxford Press',        'UK',    'Oxford',     'oup.com',        'info@oup.com',       '+44-800-666',1586),
        ('Wiley',               'USA',   'Hoboken',    'wiley.com',      'info@wiley.com',     '+1-800-777', 1807),
        ('Tata McGraw Hill',    'India', 'New Delhi',  'tatamcgraw.com', 'info@tmh.com',       '011-555-888',1970),
    ])

    cursor.executemany("INSERT INTO Author (first_name, last_name, nationality, birth_year, email, bio) VALUES (?,?,?,?,?,?)", [
        ('Donald',   'Knuth',     'American', 1938, 'knuth@cs.edu',    'Pioneer of algorithm analysis'),
        ('Martin',   'Fowler',    'British',  1963, 'fowler@dev.com',  'Software architect and author'),
        ('Robert',   'Martin',    'American', 1952, 'uncle.bob@dev.com','Agile manifesto signatory'),
        ('Thomas',   'Cormen',    'American', 1956, 'cormen@mit.edu',  'MIT professor, algorithms expert'),
        ('Jane',     'Austen',    'British',  1775, None,              'Classic English novelist'),
        ('Leo',      'Tolstoy',   'Russian',  1828, None,              'Russian literary giant'),
        ('Yuval',    'Harari',    'Israeli',  1976, 'harari@huji.ac.il','Historian and author'),
        ('Andrew',   'Tanenbaum', 'American', 1944, 'ast@cs.vu.nl',   'Operating systems expert'),
        ('Abraham',  'Silberschatz','American',1952, 'silber@yale.edu','DB textbook author'),
        ('Ramez',    'Elmasri',   'Syrian',   1950, 'elmasri@uta.edu', 'DB and systems author'),
        ('Dale',     'Carnegie',  'American', 1888, None,              'Self-help pioneer'),
        ('Agatha',   'Christie',  'British',  1890, None,              'Queen of crime fiction'),
    ])

    cursor.executemany("INSERT INTO Shelf (shelf_code, floor, section, row_number, capacity, current_count) VALUES (?,?,?,?,?,?)", [
        ('A1-01', 1, 'A', 1, 50, 42),
        ('A1-02', 1, 'A', 2, 50, 38),
        ('A2-01', 1, 'A', 3, 40, 35),
        ('B1-01', 2, 'B', 1, 50, 45),
        ('B1-02', 2, 'B', 2, 50, 30),
        ('B2-01', 2, 'B', 3, 40, 28),
        ('C1-01', 3, 'C', 1, 60, 55),
        ('C1-02', 3, 'C', 2, 60, 48),
        ('D1-01', 1, 'D', 1, 45, 20),
        ('D1-02', 1, 'D', 2, 45, 33),
    ])

    cursor.executemany("INSERT INTO Book (isbn, title, publisher_id, category_id, shelf_id, publication_year, edition, language, total_copies, available_copies, price, reorder_threshold) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
        ('978-0-201-89683-1', 'The Art of Computer Programming', 1, 2, 1, 1997, 3, 'English', 4, 2, 2500.00, 2),
        ('978-0-13-235088-4', 'Clean Code',                      2, 2, 1, 2008, 1, 'English', 5, 1, 1800.00, 2),
        ('978-0-201-63361-0', 'Design Patterns',                 1, 2, 2, 1994, 1, 'English', 3, 3, 2200.00, 1),
        ('978-0-262-03384-8', 'Introduction to Algorithms',      4, 2, 2, 2009, 3, 'English', 6, 4, 3000.00, 2),
        ('978-0-07-802215-9', 'Database System Concepts',        4, 3, 3, 2019, 7, 'English', 4, 2, 2800.00, 2),
        ('978-0-13-468599-1', 'Fundamentals of DB Systems',      1, 3, 3, 2015, 7, 'English', 3, 1, 2600.00, 2),
        ('978-0-14-028329-7', 'Pride and Prejudice',             3, 7, 4, 1813, 1, 'English', 5, 5, 400.00,  1),
        ('978-0-14-044913-6', 'War and Peace',                   3, 7, 4, 1869, 1, 'English', 3, 2, 600.00,  1),
        ('978-0-06-231609-7', 'Sapiens',                         3, 10, 5, 2011, 1, 'English', 6, 3, 750.00,  2),
        ('978-0-13-110362-7', 'The C Programming Language',      1, 2, 5, 1988, 2, 'English', 4, 4, 1500.00, 1),
        ('978-0-13-603037-5', 'Operating System Concepts',       7, 1, 6, 2018, 10,'English', 5, 2, 2400.00, 2),
        ('978-0-7432-7356-5', 'How to Win Friends',              6, 9, 7, 1936, 1, 'English', 4, 4, 350.00,  1),
        ('978-0-00-711835-0', 'Murder on the Orient Express',    3, 6, 7, 1934, 1, 'English', 3, 2, 450.00,  1),
        ('978-0-19-953556-9', 'A Brief History of Time',         6, 4, 8, 1988, 1, 'English', 4, 1, 500.00,  2),
        ('978-0-7432-7357-9', 'Atomic Habits',                   6, 9, 8, 2018, 1, 'English', 5, 5, 600.00,  2),
    ])

    cursor.executemany("INSERT INTO BookAuthor (book_id, author_id, role) VALUES (?,?,?)", [
        (1, 1, 'Author'),
        (2, 3, 'Author'),
        (3, 2, 'Author'),
        (4, 4, 'Author'),
        (5, 9, 'Author'),
        (6, 10, 'Author'),
        (6, 9,  'Co-Author'),
        (7, 5, 'Author'),
        (8, 6, 'Author'),
        (9, 7, 'Author'),
        (11, 8, 'Author'),
        (12, 11,'Author'),
        (13, 12,'Author'),
    ])

    cursor.executemany("INSERT INTO Journal (title, issn, publisher_id, category_id, frequency, impact_factor, available_issues) VALUES (?,?,?,?,?,?,?)", [
        ('IEEE Transactions on Computers',         '0018-9340', 7, 1,  'Monthly',   3.1, 12),
        ('ACM Computing Surveys',                  '0360-0300', 4, 2,  'Quarterly', 7.9, 8),
        ('Journal of Machine Learning Research',   '1532-4435', 5, 2,  'Monthly',   4.6, 10),
        ('Nature',                                 '0028-0836', 5, 4,  'Weekly',   42.7, 50),
        ('Physical Review Letters',                '0031-9007', 5, 4,  'Weekly',   9.2, 48),
        ('Journal of Finance',                     '0022-1082', 7, 8,  'Bimonthly', 6.8, 6),
        ('VLDB Journal',                           '1066-8888', 5, 3,  'Quarterly', 4.2, 8),
        ('Software Engineering Notes',             '0163-5948', 4, 2,  'Quarterly', 2.1, 10),
        ('Mathematical Annals',                    '0025-5831', 5, 5,  'Monthly',   3.5, 11),
        ('Harvard Business Review',                '0017-8012', 6, 8,  'Bimonthly', 5.3, 6),
    ])

    cursor.executemany("INSERT INTO Student (first_name, last_name, email, phone, department_id, enrollment_year, program, student_type, membership_expiry) VALUES (?,?,?,?,?,?,?,?,?)", [
        ('Aarav',   'Sharma',   'aarav@uni.edu',   '9900001', 1, 2022, 'B.Tech CSE',   'Undergraduate', '2026-12-31'),
        ('Priya',   'Mehta',    'priya@uni.edu',   '9900002', 1, 2021, 'M.Tech AI',    'Postgraduate',  '2026-12-31'),
        ('Rohan',   'Singh',    'rohan@uni.edu',   '9900003', 2, 2022, 'B.Sc Math',    'Undergraduate', '2026-12-31'),
        ('Sneha',   'Gupta',    'sneha@uni.edu',   '9900004', 4, 2020, 'MA English',   'Postgraduate',  '2026-12-31'),
        ('Vikram',  'Nair',     'vikram@uni.edu',  '9900005', 5, 2023, 'BBA',          'Undergraduate', '2026-12-31'),
        ('Ananya',  'Kapoor',   'ananya@uni.edu',  '9900006', 3, 2021, 'B.Sc Physics', 'Undergraduate', '2026-12-31'),
        ('Rahul',   'Verma',    'rahul@uni.edu',   '9900007', 1, 2019, 'PhD CS',       'PhD',           '2027-12-31'),
        ('Meera',   'Joshi',    'meera@uni.edu',   '9900008', 6, 2022, 'B.Tech EE',    'Undergraduate', '2026-12-31'),
        ('Arjun',   'Patel',    'arjun@uni.edu',   '9900009', 1, 2023, 'B.Tech CSE',   'Undergraduate', '2026-12-31'),
        ('Kavya',   'Rao',      'kavya@uni.edu',   '9900010', 4, 2020, 'PhD English',  'PhD',           '2027-12-31'),
        ('Aditya',  'Kumar',    'aditya@uni.edu',  '9900011', 5, 2021, 'MBA',          'Postgraduate',  '2026-12-31'),
        ('Pooja',   'Iyer',     'pooja@uni.edu',   '9900012', 3, 2022, 'M.Sc Physics', 'Postgraduate',  '2026-12-31'),
    ])

    cursor.executemany("INSERT INTO Faculty (first_name, last_name, email, phone, department_id, designation, employee_id, joining_date) VALUES (?,?,?,?,?,?,?,?)", [
        ('Amit',    'Sharma',  'amit.s@uni.edu',  '9811101', 1, 'Professor',        'FAC001', '2005-07-15'),
        ('Sunita',  'Mehta',   'sunita@uni.edu',  '9811102', 2, 'Associate Prof',   'FAC002', '2010-01-10'),
        ('Rajesh',  'Kapoor',  'rajesh@uni.edu',  '9811103', 3, 'Assistant Prof',   'FAC003', '2015-06-01'),
        ('Deepa',   'Nair',    'deepa@uni.edu',   '9811104', 4, 'Professor',        'FAC004', '2003-08-20'),
        ('Vivek',   'Gupta',   'vivek@uni.edu',   '9811105', 5, 'Associate Prof',   'FAC005', '2012-03-15'),
        ('Priya',   'Singh',   'priya.s@uni.edu', '9811106', 1, 'Assistant Prof',   'FAC006', '2018-07-01'),
        ('Mohan',   'Verma',   'mohan@uni.edu',   '9811107', 6, 'Professor',        'FAC007', '2000-04-10'),
        ('Lalitha', 'Rao',     'lalitha@uni.edu', '9811108', 4, 'Associate Prof',   'FAC008', '2008-09-05'),
        ('Suresh',  'Kumar',   'suresh@uni.edu',  '9811109', 2, 'Assistant Prof',   'FAC009', '2020-01-15'),
        ('Neha',    'Joshi',   'neha@uni.edu',    '9811110', 1, 'Assistant Prof',   'FAC010', '2021-07-01'),
    ])

    cursor.executemany("INSERT INTO Loan (book_id, borrower_type, borrower_id, issue_date, due_date, return_date, renewed_count, issued_by) VALUES (?,?,?,?,?,?,?,?)", [
        (2,  'Student', 1,  '2026-05-01', '2026-05-15', '2026-05-14', 0, 'librarian1'),
        (4,  'Student', 2,  '2026-05-03', '2026-05-17', '2026-05-20', 1, 'librarian1'),
        (9,  'Faculty', 1,  '2026-05-10', '2026-06-10', '2026-06-08', 0, 'librarian2'),
        (5,  'Student', 3,  '2026-05-15', '2026-05-29', None,         0, 'librarian1'),
        (11, 'Student', 4,  '2026-05-18', '2026-06-01', '2026-05-30', 0, 'librarian2'),
        (14, 'Student', 6,  '2026-05-20', '2026-06-03', None,         1, 'librarian1'),
        (1,  'Faculty', 2,  '2026-06-01', '2026-07-01', None,         0, 'librarian2'),
        (7,  'Student', 5,  '2026-06-02', '2026-06-16', '2026-06-15', 0, 'librarian1'),
        (8,  'Student', 7,  '2026-06-05', '2026-06-19', None,         0, 'librarian2'),
        (3,  'Faculty', 3,  '2026-06-07', '2026-07-07', '2026-07-05', 0, 'librarian1'),
        (6,  'Student', 9,  '2026-06-10', '2026-06-24', None,         0, 'librarian2'),
        (13, 'Student', 10, '2026-06-12', '2026-06-26', '2026-06-25', 0, 'librarian1'),
        (15, 'Faculty', 4,  '2026-06-14', '2026-07-14', None,         0, 'librarian2'),
        (10, 'Student', 11, '2026-06-15', '2026-06-29', '2026-06-28', 0, 'librarian1'),
        (12, 'Student', 12, '2026-06-16', '2026-06-30', None,         0, 'librarian2'),
    ])

    cursor.executemany("INSERT INTO Reservation (book_id, borrower_type, borrower_id, reserved_on, expires_on, status) VALUES (?,?,?,?,?,?)", [
        (2,  'Student', 8,  '2026-06-10', '2026-06-17', 'Active'),
        (5,  'Faculty', 5,  '2026-06-11', '2026-06-18', 'Active'),
        (1,  'Student', 3,  '2026-06-12', '2026-06-19', 'Active'),
        (14, 'Student', 2,  '2026-06-01', '2026-06-08', 'Fulfilled'),
        (11, 'Faculty', 2,  '2026-06-05', '2026-06-12', 'Expired'),
        (9,  'Student', 4,  '2026-06-13', '2026-06-20', 'Active'),
        (6,  'Student', 7,  '2026-06-14', '2026-06-21', 'Active'),
        (8,  'Faculty', 1,  '2026-06-02', '2026-06-09', 'Fulfilled'),
        (3,  'Student', 9,  '2026-06-15', '2026-06-22', 'Active'),
        (7,  'Student', 12, '2026-06-16', '2026-06-23', 'Active'),
    ])

    cursor.executemany("INSERT INTO Fine (loan_id, fine_amount, reason, issued_date, paid_date, status) VALUES (?,?,?,?,?,?)", [
        (2,  50.0,  'Returned late by 3 days',     '2026-05-23', '2026-05-25', 'Paid'),
        (6,  20.0,  'Overdue — still not returned', '2026-06-04', None,         'Unpaid'),
        (8,  10.0,  'Minor book damage',            '2026-06-15', '2026-06-16', 'Paid'),
        (11, 30.0,  'Overdue — still not returned', '2026-06-25', None,         'Unpaid'),
        (15, 15.0,  'Overdue — still not returned', '2026-07-01', None,         'Unpaid'),
        (9,  25.0,  'Overdue — still not returned', '2026-06-20', None,         'Unpaid'),
        (4,  40.0,  'Overdue — still not returned', '2026-05-30', None,         'Unpaid'),
        (13, 10.0,  'Page tear reported',           '2026-06-26', None,         'Waived'),
    ])

    cursor.executemany("INSERT INTO Supplier (name, contact_person, phone, email, address, city, country, rating) VALUES (?,?,?,?,?,?,?,?)", [
        ('EduBooks Pvt Ltd',    'Ramesh Shah',    '9810001', 'edu@supplier.com',    '12 Book Market',  'Delhi',   'India', 4.5),
        ('GlobalReads Import',  'Alicia Brown',   '9810002', 'global@supplier.com', '5th Ave Store',   'Mumbai',  'India', 4.2),
        ('TechPrint Solutions', 'Vikram Das',     '9810003', 'tech@supplier.com',   'IT Park Block C', 'Pune',    'India', 4.8),
        ('Classic Books Co',    'Sunita Rao',     '9810004', 'classic@supplier.com','MG Road 45',      'Bangalore','India',4.0),
        ('Science Publishers',  'Dr. James Lee',  '9810005', 'sci@supplier.com',    'Research Park',   'Chennai', 'India', 4.6),
        ('University Supplies', 'Priya Menon',    '9810006', 'uni@supplier.com',    'Campus Road 1',   'Hyderabad','India',4.3),
    ])

    cursor.executemany("INSERT INTO PurchaseOrder (supplier_id, order_date, expected_delivery, status, total_amount, ordered_by) VALUES (?,?,?,?,?,?)", [
        (1, '2026-04-01', '2026-04-15', 'Delivered', 15000.0, 'Head Librarian'),
        (2, '2026-04-10', '2026-04-25', 'Delivered', 22000.0, 'Head Librarian'),
        (3, '2026-05-01', '2026-05-20', 'Delivered', 18500.0, 'Deputy Librarian'),
        (1, '2026-05-15', '2026-06-01', 'Partial',   9000.0,  'Head Librarian'),
        (4, '2026-05-20', '2026-06-05', 'Delivered', 7500.0,  'Deputy Librarian'),
        (5, '2026-06-01', '2026-06-20', 'Pending',   31000.0, 'Head Librarian'),
        (6, '2026-06-05', '2026-06-25', 'Pending',   12000.0, 'Deputy Librarian'),
        (2, '2026-06-10', '2026-06-30', 'Pending',   19500.0, 'Head Librarian'),
        (3, '2026-06-12', '2026-07-02', 'Pending',   25000.0, 'Head Librarian'),
        (5, '2026-06-14', '2026-07-05', 'Cancelled', 8000.0,  'Deputy Librarian'),
    ])

    cursor.executemany("INSERT INTO PurchaseOrderItem (po_id, book_id, quantity_ordered, unit_price, quantity_received) VALUES (?,?,?,?,?)", [
        (1, 2,  5, 1800.0, 5),
        (1, 4,  3, 3000.0, 3),
        (2, 9,  4, 750.0,  4),
        (2, 7,  6, 400.0,  6),
        (3, 1,  2, 2500.0, 2),
        (3, 11, 3, 2400.0, 3),
        (4, 5,  3, 2800.0, 1),
        (4, 6,  2, 2600.0, 2),
        (5, 12, 4, 350.0,  4),
        (5, 13, 3, 450.0,  3),
        (6, 14, 5, 500.0,  0),
        (6, 15, 4, 600.0,  0),
        (7, 3,  3, 2200.0, 0),
        (8, 8,  4, 600.0,  0),
        (9, 10, 5, 1500.0, 0),
    ])

    conn.commit()
    conn.close()
    print("library2.db created successfully!")
    print("16 tables, 10+ rows each.")

if __name__ == '__main__':
    create_database()
