import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library.db')

def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS Issue_Record;
        DROP TABLE IF EXISTS Stock_Alert;
        DROP TABLE IF EXISTS Book;
        DROP TABLE IF EXISTS Supplier_Visit_Schedule;
        DROP TABLE IF EXISTS Supplier_Publication;
        DROP TABLE IF EXISTS Member;
        DROP TABLE IF EXISTS Publication;
        DROP TABLE IF EXISTS Supplier;

        CREATE TABLE Supplier (
            supplier_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT NOT NULL,
            contact_person TEXT,
            phone          TEXT,
            email          TEXT UNIQUE,
            address        TEXT
        );

        CREATE TABLE Publication (
            publication_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title          TEXT NOT NULL,
            category       TEXT,
            publisher_name TEXT,
            language       TEXT DEFAULT 'English'
        );

        CREATE TABLE Member (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT NOT NULL,
            email     TEXT NOT NULL UNIQUE,
            phone     TEXT
        );

        CREATE TABLE Supplier_Publication (
            sp_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id    INTEGER NOT NULL,
            publication_id INTEGER NOT NULL,
            price_per_unit REAL,
            lead_time_days INTEGER,
            FOREIGN KEY (supplier_id)    REFERENCES Supplier(supplier_id),
            FOREIGN KEY (publication_id) REFERENCES Publication(publication_id)
        );

        CREATE TABLE Supplier_Visit_Schedule (
            visit_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            visit_month INTEGER CHECK(visit_month BETWEEN 1 AND 12),
            visit_date  TEXT,
            notes       TEXT,
            FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
        );

        CREATE TABLE Book (
            book_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            publication_id    INTEGER NOT NULL,
            title             TEXT NOT NULL,
            author            TEXT,
            available_copies  INTEGER DEFAULT 0,
            reorder_threshold INTEGER DEFAULT 2,
            FOREIGN KEY (publication_id) REFERENCES Publication(publication_id)
        );

        CREATE TABLE Stock_Alert (
            alert_id              INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id               INTEGER NOT NULL,
            supplier_id           INTEGER NOT NULL,
            alert_date            TEXT,
            expected_arrival_date TEXT,
            status                TEXT DEFAULT 'Pending',
            notified_user         TEXT,
            FOREIGN KEY (book_id)     REFERENCES Book(book_id),
            FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
        );

        CREATE TABLE Issue_Record (
            issue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id   INTEGER NOT NULL,
            book_id     INTEGER NOT NULL,
            issue_date  TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (member_id) REFERENCES Member(member_id),
            FOREIGN KEY (book_id)   REFERENCES Book(book_id)
        );

        CREATE VIEW IF NOT EXISTS vw_stock_alert_trigger AS
        SELECT
            b.title                AS book_title,
            b.available_copies,
            b.reorder_threshold,
            s.name                 AS supplier_name,
            svs.visit_date         AS next_visit,
            sp.lead_time_days,
            DATE(svs.visit_date, '+' || sp.lead_time_days || ' days') AS expected_arrival
        FROM Book b
        JOIN Publication           p   ON b.publication_id  = p.publication_id
        JOIN Supplier_Publication  sp  ON p.publication_id  = sp.publication_id
        JOIN Supplier              s   ON sp.supplier_id    = s.supplier_id
        JOIN Supplier_Visit_Schedule svs ON s.supplier_id   = svs.supplier_id
        WHERE b.available_copies <= b.reorder_threshold
        ORDER BY expected_arrival ASC;

        -- Sample Data
        INSERT INTO Supplier (name, contact_person, phone, email, address) VALUES
        ('PaperBridge Distributors', 'Raj Mehta',    '555-1001', 'raj@paperbridge.com',  '12 Nehru Road, Delhi'),
        ('BookSource India',          'Priya Sharma', '555-1002', 'priya@booksource.com', '45 MG Road, Bangalore'),
        ('EduSupply Co.',             'Amit Verma',   '555-1003', 'amit@edusupply.com',   '7 Park Street, Kolkata'),
        ('GlobalReads Ltd.',          'Sara Khan',    '555-1004', 'sara@globalreads.com', '22 Anna Salai, Chennai'),
        ('PrintWorld',                'Vikram Singh', '555-1005', 'vikram@printworld.com','9 FC Road, Pune');

        INSERT INTO Publication (title, category, publisher_name, language) VALUES
        ('Modern Fiction Series',    'Fiction',    'Penguin Books',  'English'),
        ('Science Discoveries',      'Science',    'Oxford Press',   'English'),
        ('Tech Mastery',             'Technology', 'O''Reilly',      'English'),
        ('World History Collection', 'History',    'Harper Collins', 'English'),
        ('Programming Essentials',   'Technology', 'Apress',         'English');

        INSERT INTO Member (name, email, phone) VALUES
        ('John Doe',    'john@mail.com',  '555-0101'),
        ('Jane Roe',    'jane@mail.com',  '555-0102'),
        ('Sam Patel',   'sam@mail.com',   '555-0103'),
        ('Lisa Chen',   'lisa@mail.com',  '555-0104'),
        ('Mark Okafor', 'mark@mail.com',  '555-0105');

        INSERT INTO Supplier_Publication (supplier_id, publication_id, price_per_unit, lead_time_days) VALUES
        (1, 1, 450.00,  7),
        (2, 2, 380.00,  5),
        (3, 3, 520.00, 10),
        (4, 4, 290.00,  6),
        (5, 5, 610.00,  8);

        INSERT INTO Supplier_Visit_Schedule (supplier_id, visit_month, visit_date, notes) VALUES
        (1, 7, '2026-07-15', 'Monthly fiction restock visit'),
        (2, 8, '2026-08-10', 'Science books quarterly visit'),
        (3, 7, '2026-07-20', 'Tech books scheduled visit'),
        (4, 9, '2026-09-05', 'History collection annual visit'),
        (5, 8, '2026-08-25', 'Programming books restock visit');

        INSERT INTO Book (publication_id, title, author, available_copies, reorder_threshold) VALUES
        (1, 'The Great Gatsby',         'F. Scott Fitzgerald', 1, 2),
        (2, 'A Brief History of Time',  'Stephen Hawking',     2, 2),
        (3, 'Clean Code',               'Robert C. Martin',    1, 3),
        (4, 'Sapiens',                  'Yuval Noah Harari',   5, 2),
        (5, 'The Pragmatic Programmer', 'Andrew Hunt',         4, 2);

        INSERT INTO Stock_Alert (book_id, supplier_id, alert_date, expected_arrival_date, status, notified_user) VALUES
        (1, 1, '2026-06-16', '2026-07-22', 'Pending',  'Alice Johnson'),
        (2, 2, '2026-06-16', '2026-08-15', 'Pending',  'Bob Smith'),
        (3, 3, '2026-06-16', '2026-07-30', 'Notified', 'Carol White'),
        (1, 1, '2026-05-01', '2026-05-22', 'Resolved', 'David Lee'),
        (2, 2, '2026-04-15', '2026-05-10', 'Resolved', 'Eva Martinez');

        INSERT INTO Issue_Record (member_id, book_id, issue_date, return_date) VALUES
        (1, 3, '2026-06-01', '2026-06-15'),
        (2, 1, '2026-06-03', NULL),
        (3, 5, '2026-06-05', '2026-06-12'),
        (4, 2, '2026-06-08', NULL),
        (5, 4, '2026-06-10', '2026-06-14');
    """)
    conn.commit()
    conn.close()
    print("library.db created successfully!")

if __name__ == "__main__":
    create_database()
