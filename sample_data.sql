-- ============================================================
--  Library Management System — Sample Data
--  File: sample_data.sql
--  Run AFTER library_schema.sql
-- ============================================================

-- ------------------------------------------------------------
-- Supplier (5 rows)
-- ------------------------------------------------------------
INSERT INTO Supplier (name, contact_person, phone, email, address) VALUES
('PaperBridge Distributors', 'Raj Mehta',    '555-1001', 'raj@paperbridge.com',  '12 Nehru Road, Delhi'),
('BookSource India',          'Priya Sharma', '555-1002', 'priya@booksource.com', '45 MG Road, Bangalore'),
('EduSupply Co.',             'Amit Verma',   '555-1003', 'amit@edusupply.com',   '7 Park Street, Kolkata'),
('GlobalReads Ltd.',          'Sara Khan',    '555-1004', 'sara@globalreads.com', '22 Anna Salai, Chennai'),
('PrintWorld',                'Vikram Singh', '555-1005', 'vikram@printworld.com','9 FC Road, Pune');

-- ------------------------------------------------------------
-- Publication (5 rows)
-- ------------------------------------------------------------
INSERT INTO Publication (title, category, publisher_name, language) VALUES
('Modern Fiction Series',      'Fiction',    'Penguin Books',  'English'),
('Science Discoveries',        'Science',    'Oxford Press',   'English'),
('Tech Mastery',               'Technology', 'O''Reilly',      'English'),
('World History Collection',   'History',    'Harper Collins', 'English'),
('Programming Essentials',     'Technology', 'Apress',         'English');

-- ------------------------------------------------------------
-- Member (5 rows)
-- ------------------------------------------------------------
INSERT INTO Member (name, email, phone) VALUES
('John Doe',    'john@mail.com',  '555-0101'),
('Jane Roe',    'jane@mail.com',  '555-0102'),
('Sam Patel',   'sam@mail.com',   '555-0103'),
('Lisa Chen',   'lisa@mail.com',  '555-0104'),
('Mark Okafor', 'mark@mail.com',  '555-0105');

-- ------------------------------------------------------------
-- Supplier_Publication (5 rows)
-- Each supplier supplies one publication with price + lead time
-- ------------------------------------------------------------
INSERT INTO Supplier_Publication (supplier_id, publication_id, price_per_unit, lead_time_days) VALUES
(1, 1, 450.00,  7),   -- PaperBridge   → Modern Fiction Series,    7 days
(2, 2, 380.00,  5),   -- BookSource    → Science Discoveries,       5 days
(3, 3, 520.00, 10),   -- EduSupply     → Tech Mastery,             10 days
(4, 4, 290.00,  6),   -- GlobalReads   → World History Collection,  6 days
(5, 5, 610.00,  8);   -- PrintWorld    → Programming Essentials,    8 days

-- ------------------------------------------------------------
-- Supplier_Visit_Schedule (5 rows)
-- Visit dates in July–September 2026
-- ------------------------------------------------------------
INSERT INTO Supplier_Visit_Schedule (supplier_id, visit_month, visit_date, notes) VALUES
(1, 7, '2026-07-15', 'Monthly fiction restock visit'),
(2, 8, '2026-08-10', 'Science books quarterly visit'),
(3, 7, '2026-07-20', 'Tech books scheduled visit'),
(4, 9, '2026-09-05', 'History collection annual visit'),
(5, 8, '2026-08-25', 'Programming books restock visit');

-- ------------------------------------------------------------
-- Book (5 rows)
-- Books 1, 2, 3 → available_copies <= reorder_threshold (triggers VIEW)
-- Books 4, 5    → stock is fine
-- ------------------------------------------------------------
INSERT INTO Book (publication_id, title, author, available_copies, reorder_threshold) VALUES
(1, 'The Great Gatsby',         'F. Scott Fitzgerald', 1, 2),  -- 1 <= 2 → ALERT
(2, 'A Brief History of Time',  'Stephen Hawking',     2, 2),  -- 2 <= 2 → ALERT
(3, 'Clean Code',               'Robert C. Martin',    1, 3),  -- 1 <= 3 → ALERT
(4, 'Sapiens',                  'Yuval Noah Harari',   5, 2),  -- 5 > 2  → OK
(5, 'The Pragmatic Programmer', 'Andrew Hunt',         4, 2);  -- 4 > 2  → OK

-- ------------------------------------------------------------
-- Stock_Alert (5 rows)
-- Derived logic:
--   Book 1 → pub_id=1 → supplier_id=1 → visit='2026-07-15' + 7 days = '2026-07-22'
--   Book 2 → pub_id=2 → supplier_id=2 → visit='2026-08-10' + 5 days = '2026-08-15'
--   Book 3 → pub_id=3 → supplier_id=3 → visit='2026-07-20' + 10 days= '2026-07-30'
--   Rows 4 & 5 are older resolved alerts for the same books
-- ------------------------------------------------------------
INSERT INTO Stock_Alert (book_id, supplier_id, alert_date, expected_arrival_date, status, notified_user) VALUES
(1, 1, '2026-06-16', '2026-07-22', 'Pending',  'Alice Johnson'),
(2, 2, '2026-06-16', '2026-08-15', 'Pending',  'Bob Smith'),
(3, 3, '2026-06-16', '2026-07-30', 'Notified', 'Carol White'),
(1, 1, '2026-05-01', '2026-05-22', 'Resolved', 'David Lee'),
(2, 2, '2026-04-15', '2026-05-10', 'Resolved', 'Eva Martinez');

-- ------------------------------------------------------------
-- Issue_Record (5 rows)
-- ------------------------------------------------------------
INSERT INTO Issue_Record (member_id, book_id, issue_date, return_date) VALUES
(1, 3, '2026-06-01', '2026-06-15'),
(2, 1, '2026-06-03', NULL),
(3, 5, '2026-06-05', '2026-06-12'),
(4, 2, '2026-06-08', NULL),
(5, 4, '2026-06-10', '2026-06-14');

-- ------------------------------------------------------------
-- Quick verification queries
-- ------------------------------------------------------------
-- SELECT * FROM vw_stock_alert_trigger;
-- SELECT * FROM Stock_Alert WHERE status = 'Pending';
-- SELECT * FROM Book WHERE available_copies <= reorder_threshold;
