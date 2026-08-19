"""
Script for massive data import to MetsisEE Workers.
Run:
python3 api_db_name api_db_user api_db_pass api_db_host workers_db_name workers_db_user workers_db_pass workers_db_host
"""

import sys

import psycopg2
from psycopg2.extras import RealDictCursor

db1_name = sys.argv[1]
db1_user = sys.argv[2]
db1_pass = sys.argv[3]
db1_host = sys.argv[4]

db2_name = sys.argv[5]
db2_user = sys.argv[6]
db2_pass = sys.argv[7]
db2_host = sys.argv[8]

def get_db_cursor(dbname, user, password, host):
    try:
        print("Establishing database connection...")
        connect_str = "dbname='" + dbname + "' user='" + user + "' host='" + host + "' password='" + password + "'"
        conn = psycopg2.connect(connect_str)
        conn.autocommit = True
        return conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        print("Can't connect to database. Invalid dbname, user or password?")
        print(e)

cursor1 = get_db_cursor(db1_name, db1_user, db1_pass, db1_host)

cursor2 = get_db_cursor(db2_name, db2_user, db2_pass, db2_host)

cursor1.execute("""select ow.id as id, ow.name as name, ow.type as type, oc.obj_count as obj_count from owners ow join
    (select o.owner_id, count(o.cadastre_id) obj_count from owner_cadastre o group by o.owner_id) oc on oc.owner_id = ow.id
  where ow.type = 'ERAISIK' or ow.type = 'FIRMAD'""")

print("Starting fetch")
owners = cursor1.fetchall()

print("Fetched. Starting insert")

i = 0
j = len(owners)
for owner in owners:
    i += 1
    print(str(i) + "/" + str(j))
    cursor2.execute("insert into owners (id, name, type, number_of_cadastres) values (%s,%s,%s,%s)",
                    (owner['id'], owner['name'], owner['type'], owner['obj_count']))

print("Finished")
