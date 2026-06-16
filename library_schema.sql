-- ============================================================
--  Library Management System — Schema
--  File: library_schema.sql
--  Engine: SQLite
-- ============================================================

-- ------------------------------------------------------------
-- DROP (reverse FK order to avoid constraint errors)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS Issue_Record;
DROP TABLE IF EXISTS Stock_Alert;
DROP TABLE IF EXISTS Book;
DROP TABLE IF EXISTS Supplier_Visit_Schedule;
DROP TABLE IF EXISTS Supplier_Publication;
DROP TABLE IF EXISTS Member;
DROP TABLE IF EXISTS Publication;
DROP TABLE IF EXISTS Supplier;

-- ------------------------------------------------------------
-- 1. Supplier
-- ------------------------------------------------------------
CREATE TABLE Supplier (
    supplier_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    contact_person TEXT,
    phone          TEXT,
    email          TEXT    UNIQUE,
    address        TEXT
);

-- ------------------------------------------------------------
-- 2. Publication
-- ------------------------------------------------------------
CREATE TABLE Publication (
    publication_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT    NOT NULL,
    category       TEXT,
    publisher_name TEXT,
    language       TEXT    DEFAULT 'English'
);

-- ------------------------------------------------------------
-- 3. Member
-- ------------------------------------------------------------
CREATE TABLE Member (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    email     TEXT NOT NULL UNIQUE,
    phone     TEXT
);

-- ------------------------------------------------------------
-- 4. Supplier_Publication  (Junction: Supplier ↔ Publication)
-- ------------------------------------------------------------
CREATE TABLE Supplier_Publication (
    sp_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id    INTEGER NOT NULL,
    publication_id INTEGER NOT NULL,
    price_per_unit REAL,
    lead_time_days INTEGER,
    FOREIGN KEY (supplier_id)    REFERENCES Supplier(supplier_id),
    FOREIGN KEY (publication_id) REFERENCES Publication(publication_id)
);

-- ------------------------------------------------------------
-- 5. Supplier_Visit_Schedule
-- ------------------------------------------------------------
CREATE TABLE Supplier_Visit_Schedule (
    visit_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id  INTEGER NOT NULL,
    visit_month  INTEGER CHECK(visit_month BETWEEN 1 AND 12),
    visit_date   TEXT,
    notes        TEXT,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
);

-- ------------------------------------------------------------
-- 6. Book
-- ------------------------------------------------------------
CREATE TABLE Book (
    book_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    publication_id    INTEGER NOT NULL,
    title             TEXT    NOT NULL,
    author            TEXT,
    available_copies  INTEGER DEFAULT 0,
    reorder_threshold INTEGER DEFAULT 2,
    FOREIGN KEY (publication_id) REFERENCES Publication(publication_id)
);

-- ------------------------------------------------------------
-- 7. Stock_Alert
--    Populated when Book.available_copies <= Book.reorder_threshold
--    expected_arrival_date = next visit_date + lead_time_days
-- ------------------------------------------------------------
CREATE TABLE Stock_Alert (
    alert_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id               INTEGER NOT NULL,
    supplier_id           INTEGER NOT NULL,
    alert_date            TEXT,
    expected_arrival_date TEXT,
    status                TEXT DEFAULT 'Pending',  -- Pending / Notified / Resolved
    notified_user         TEXT,
    FOREIGN KEY (book_id)     REFERENCES Book(book_id),
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
);

-- ------------------------------------------------------------
-- 8. Issue_Record
-- ------------------------------------------------------------
CREATE TABLE Issue_Record (
    issue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id   INTEGER NOT NULL,
    book_id     INTEGER NOT NULL,
    issue_date  TEXT    NOT NULL,
    return_date TEXT,
    FOREIGN KEY (member_id) REFERENCES Member(member_id),
    FOREIGN KEY (book_id)   REFERENCES Book(book_id)
);

-- ------------------------------------------------------------
-- VIEW: vw_stock_alert_trigger
--   Shows all books that are at or below reorder threshold,
--   joined with their supplier and next scheduled visit.
--   expected_arrival = visit_date + lead_time_days
-- ------------------------------------------------------------
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
