"""
PostgreSQL migration script.

Usage:
    DATABASE_URL=postgresql://user:pass@host:5432/dbname python app3/migrate_postgres.py

Creates all 24 tables (23 library tables + QueryLog) with proper PostgreSQL types.
Run once against an empty PostgreSQL database.
"""

import os
import sys

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL environment variable is required.")
    print("Example: postgresql://postgres:password@localhost:5432/library")
    sys.exit(1)

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS Publisher (
    publisher_id  SERIAL PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    city          VARCHAR(100) NOT NULL,
    website       TEXT,
    email         VARCHAR(255),
    phone         VARCHAR(20),
    established_year INTEGER
);

CREATE TABLE IF NOT EXISTS Category (
    category_id       SERIAL PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    description       TEXT,
    dewey_decimal     VARCHAR(20),
    parent_category_id INTEGER REFERENCES Category(category_id)
);

CREATE TABLE IF NOT EXISTS Shelf (
    shelf_id      SERIAL PRIMARY KEY,
    shelf_code    VARCHAR(20) NOT NULL,
    floor         INTEGER NOT NULL,
    section       VARCHAR(50) NOT NULL,
    row_number    INTEGER NOT NULL,
    capacity      INTEGER NOT NULL,
    current_count INTEGER
);

CREATE TABLE IF NOT EXISTS Department (
    department_id    SERIAL PRIMARY KEY,
    name             VARCHAR(200) NOT NULL,
    building         VARCHAR(100) NOT NULL,
    floor            INTEGER NOT NULL,
    head_name        VARCHAR(200) NOT NULL,
    phone            VARCHAR(20),
    email            VARCHAR(255),
    established_year INTEGER
);

CREATE TABLE IF NOT EXISTS Author (
    author_id   SERIAL PRIMARY KEY,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    nationality VARCHAR(100),
    birth_year  INTEGER,
    email       VARCHAR(255),
    bio         TEXT
);

CREATE TABLE IF NOT EXISTS Supplier (
    supplier_id    SERIAL PRIMARY KEY,
    name           VARCHAR(200) NOT NULL,
    contact_person VARCHAR(200),
    phone          VARCHAR(20),
    email          VARCHAR(255),
    address        TEXT,
    city           VARCHAR(100),
    country        VARCHAR(100),
    rating         NUMERIC(3,2)
);

CREATE TABLE IF NOT EXISTS Librarian (
    librarian_id SERIAL PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    email        VARCHAR(255) NOT NULL,
    phone        VARCHAR(20),
    role         VARCHAR(50) NOT NULL,
    shift        VARCHAR(20),
    joining_date DATE,
    salary       NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS Student (
    student_id        SERIAL PRIMARY KEY,
    first_name        VARCHAR(100) NOT NULL,
    last_name         VARCHAR(100) NOT NULL,
    email             VARCHAR(255) NOT NULL,
    phone             VARCHAR(20),
    department_id     INTEGER REFERENCES Department(department_id),
    enrollment_year   INTEGER,
    program           VARCHAR(100),
    student_type      VARCHAR(20),
    membership_expiry DATE
);

CREATE TABLE IF NOT EXISTS Faculty (
    faculty_id    SERIAL PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL,
    phone         VARCHAR(20),
    department_id INTEGER REFERENCES Department(department_id),
    designation   VARCHAR(100),
    employee_id   VARCHAR(50),
    joining_date  DATE
);

CREATE TABLE IF NOT EXISTS Book (
    book_id          SERIAL PRIMARY KEY,
    isbn             VARCHAR(20),
    title            VARCHAR(500) NOT NULL,
    publisher_id     INTEGER REFERENCES Publisher(publisher_id),
    category_id      INTEGER REFERENCES Category(category_id),
    shelf_id         INTEGER REFERENCES Shelf(shelf_id),
    publication_year INTEGER,
    edition          INTEGER,
    language         VARCHAR(50),
    total_copies     INTEGER,
    available_copies INTEGER,
    price            NUMERIC(10,2),
    reorder_threshold INTEGER
);

CREATE TABLE IF NOT EXISTS BookAuthor (
    ba_id     SERIAL PRIMARY KEY,
    book_id   INTEGER NOT NULL REFERENCES Book(book_id),
    author_id INTEGER NOT NULL REFERENCES Author(author_id),
    role      VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS Journal (
    journal_id      SERIAL PRIMARY KEY,
    title           VARCHAR(500) NOT NULL,
    issn            VARCHAR(20),
    publisher_id    INTEGER REFERENCES Publisher(publisher_id),
    category_id     INTEGER REFERENCES Category(category_id),
    frequency       VARCHAR(50),
    impact_factor   NUMERIC(5,3),
    available_issues INTEGER
);

CREATE TABLE IF NOT EXISTS DigitalResource (
    resource_id         SERIAL PRIMARY KEY,
    title               VARCHAR(500) NOT NULL,
    resource_type       VARCHAR(50),
    url                 TEXT,
    category_id         INTEGER REFERENCES Category(category_id),
    publisher_id        INTEGER REFERENCES Publisher(publisher_id),
    access_type         VARCHAR(20),
    subscription_start  DATE,
    subscription_expiry DATE,
    cost_per_year       NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS Loan (
    loan_id       SERIAL PRIMARY KEY,
    book_id       INTEGER NOT NULL REFERENCES Book(book_id),
    borrower_type VARCHAR(10) NOT NULL,
    borrower_id   INTEGER NOT NULL,
    issue_date    DATE NOT NULL,
    due_date      DATE NOT NULL,
    return_date   DATE,
    renewed_count INTEGER,
    issued_by     VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Fine (
    fine_id     SERIAL PRIMARY KEY,
    loan_id     INTEGER NOT NULL REFERENCES Loan(loan_id),
    fine_amount NUMERIC(10,2) NOT NULL,
    reason      TEXT NOT NULL,
    issued_date DATE NOT NULL,
    paid_date   DATE,
    status      VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS Reservation (
    reservation_id SERIAL PRIMARY KEY,
    book_id        INTEGER NOT NULL REFERENCES Book(book_id),
    borrower_type  VARCHAR(10) NOT NULL,
    borrower_id    INTEGER NOT NULL,
    reserved_on    DATE NOT NULL,
    expires_on     DATE NOT NULL,
    status         VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS BookReview (
    review_id     SERIAL PRIMARY KEY,
    book_id       INTEGER NOT NULL REFERENCES Book(book_id),
    reviewer_type VARCHAR(10) NOT NULL,
    reviewer_id   INTEGER NOT NULL,
    rating        SMALLINT,
    review_text   TEXT,
    review_date   DATE NOT NULL,
    helpful_count INTEGER
);

CREATE TABLE IF NOT EXISTS BookRequest (
    request_id  SERIAL PRIMARY KEY,
    student_id  INTEGER NOT NULL REFERENCES Student(student_id),
    book_title  VARCHAR(500) NOT NULL,
    author_name VARCHAR(200),
    category_id INTEGER REFERENCES Category(category_id),
    reason      TEXT,
    request_date DATE NOT NULL,
    status      VARCHAR(20),
    handled_by  INTEGER REFERENCES Librarian(librarian_id)
);

CREATE TABLE IF NOT EXISTS LibraryEvent (
    event_id      SERIAL PRIMARY KEY,
    title         VARCHAR(500) NOT NULL,
    description   TEXT,
    event_date    DATE NOT NULL,
    event_time    TIME,
    venue         VARCHAR(200),
    organizer_id  INTEGER REFERENCES Librarian(librarian_id),
    department_id INTEGER REFERENCES Department(department_id),
    capacity      INTEGER,
    fee           NUMERIC(10,2),
    status        VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS EventRegistration (
    reg_id            SERIAL PRIMARY KEY,
    event_id          INTEGER NOT NULL REFERENCES LibraryEvent(event_id),
    student_id        INTEGER NOT NULL REFERENCES Student(student_id),
    registration_date DATE NOT NULL,
    attendance_status VARCHAR(20),
    payment_status    VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS DigitalAccess (
    access_id        SERIAL PRIMARY KEY,
    resource_id      INTEGER NOT NULL REFERENCES DigitalResource(resource_id),
    student_id       INTEGER NOT NULL REFERENCES Student(student_id),
    access_date      DATE NOT NULL,
    duration_minutes INTEGER,
    device_type      VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS PurchaseOrder (
    po_id             SERIAL PRIMARY KEY,
    supplier_id       INTEGER NOT NULL REFERENCES Supplier(supplier_id),
    order_date        DATE NOT NULL,
    expected_delivery DATE,
    status            VARCHAR(20),
    total_amount      NUMERIC(12,2),
    ordered_by        VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS PurchaseOrderItem (
    poi_id            SERIAL PRIMARY KEY,
    po_id             INTEGER NOT NULL REFERENCES PurchaseOrder(po_id),
    book_id           INTEGER NOT NULL REFERENCES Book(book_id),
    quantity_ordered  INTEGER NOT NULL,
    unit_price        NUMERIC(10,2) NOT NULL,
    quantity_received INTEGER
);

CREATE TABLE IF NOT EXISTS QueryLog (
    query_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_question     TEXT NOT NULL,
    generated_sql     TEXT,
    sql_execution_time FLOAT,
    sql_success       BOOLEAN NOT NULL,
    error_message     TEXT,
    response_text     TEXT,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_book_isbn ON Book(isbn);
CREATE INDEX IF NOT EXISTS idx_book_title ON Book(title);
CREATE INDEX IF NOT EXISTS idx_book_category ON Book(category_id);
CREATE INDEX IF NOT EXISTS idx_bookauthor_book ON BookAuthor(book_id);
CREATE INDEX IF NOT EXISTS idx_bookauthor_author ON BookAuthor(author_id);
CREATE INDEX IF NOT EXISTS idx_loan_book ON Loan(book_id);
CREATE INDEX IF NOT EXISTS idx_loan_borrower ON Loan(borrower_id);
CREATE INDEX IF NOT EXISTS idx_loan_due ON Loan(due_date);
CREATE INDEX IF NOT EXISTS idx_loan_return ON Loan(return_date);
CREATE INDEX IF NOT EXISTS idx_fine_loan ON Fine(loan_id);
CREATE INDEX IF NOT EXISTS idx_fine_status ON Fine(status);
CREATE INDEX IF NOT EXISTS idx_reservation_book ON Reservation(book_id);
CREATE INDEX IF NOT EXISTS idx_reservation_borrower ON Reservation(borrower_id);
CREATE INDEX IF NOT EXISTS idx_reservation_status ON Reservation(status);
CREATE INDEX IF NOT EXISTS idx_student_dept ON Student(department_id);
CREATE INDEX IF NOT EXISTS idx_student_email ON Student(email);
CREATE INDEX IF NOT EXISTS idx_faculty_dept ON Faculty(department_id);
CREATE INDEX IF NOT EXISTS idx_faculty_email ON Faculty(email);
CREATE INDEX IF NOT EXISTS idx_digitalaccess_student ON DigitalAccess(student_id);
CREATE INDEX IF NOT EXISTS idx_digitalaccess_date ON DigitalAccess(access_date);
CREATE INDEX IF NOT EXISTS idx_eventregistration_event ON EventRegistration(event_id);
CREATE INDEX IF NOT EXISTS idx_eventregistration_student ON EventRegistration(student_id);
CREATE INDEX IF NOT EXISTS idx_libraryevent_date ON LibraryEvent(event_date);
CREATE INDEX IF NOT EXISTS idx_purchaseorder_supplier ON PurchaseOrder(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchaseorder_status ON PurchaseOrder(status);
CREATE INDEX IF NOT EXISTS idx_purchaseorderitem_po ON PurchaseOrderItem(po_id);
CREATE INDEX IF NOT EXISTS idx_bookreview_book ON BookReview(book_id);
CREATE INDEX IF NOT EXISTS idx_bookrequest_student ON BookRequest(student_id);
CREATE INDEX IF NOT EXISTS idx_bookrequest_status ON BookRequest(status);
CREATE INDEX IF NOT EXISTS idx_querylog_created ON QueryLog(created_at);
"""


def main():
    print(f"Connecting to: {DATABASE_URL[:DATABASE_URL.rfind('@') + 1]}***")
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    print("Running migration...")
    cur.execute(SCHEMA_SQL)

    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\nTables created ({len(tables)}):")
    for t in tables:
        print(f"  {t}")

    cur.close()
    conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
