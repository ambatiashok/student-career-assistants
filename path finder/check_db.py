import sqlite3
conn = sqlite3.connect('instance/career.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print('TABLES:', tables)
for t in tables:
    c.execute("PRAGMA table_info(%s)" % t)
    cols = c.fetchall()
    print('--- %s ---' % t)
    for col in cols:
        print('  %s (%s)' % (col[1], col[2]))
conn.close()
