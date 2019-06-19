# Mock for database access; use sqlite3 in memory rather than MySQL

import sqlite3


class MockCursor(object):
    def __init__(self, sql, db):
        self.sql, self.db = sql, db
        self.dbcursor = db.cursor()

    def execute(self, statement):
        self.sql.append(statement)
        # sqlite uses ? as a placeholder; MySQL uses %s
        self.dbcursor.execute(statement.replace('%s', '?'))

    def __iter__(self):
        fa = self.dbcursor.fetchall()
        return fa.__iter__()


class MockConnection(object):
    def __init__(self, db, *args, **keys):
        self.args = args
        self.keys = keys
        self.db = sqlite3.connect(":memory:")
        self.sql = []
        # Use the database 'name' argument as a set of sqlite3 statements
        # to initialize it
        c = self.db.cursor()
        for d in db:
            c.execute(d)

    def cursor(self):
        return MockCursor(self.sql, self.db)

    def close(self):
        self.db.close()


def connect(*args, **keys):
    return MockConnection(*args, **keys)
