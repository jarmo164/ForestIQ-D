"""
Script for massive data import to MetsisEE.
Run:
python3 scriptname.py db_name db_user db_pass db_host input_file
"""

import csv
import sys
import json

import psycopg2
from psycopg2.extras import RealDictCursor

INPUT_ENCODING = 'UTF-8'
INPUT_CSV_DELIMITER = ','
INPUT_CSV_QUOTE_CHAR = '"'

db_name = sys.argv[1]
db_user = sys.argv[2]
db_pass = sys.argv[3]
db_host = sys.argv[4]
input_file = sys.argv[5]


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


def count_csv_rows(csv_file_name):
    print("Counting CSV rows...")
    with open(csv_file_name, newline='', encoding=INPUT_ENCODING) as csvfile:
        ordr = csv.reader(csvfile, delimiter=INPUT_CSV_DELIMITER, quotechar=INPUT_CSV_QUOTE_CHAR)
        return sum(1 for row in ordr)


def trim(v):
    if v is None:
        return v
    v = v.strip()
    if not v:
        return None
    return v

def norm_json(str):
    a_coord = None
    poly = json.loads(str)
    rr = []
    for x in poly:
        r_i = []
        for x_i in x:
            if a_coord == None:
                a_coord = {'lat': x_i[0], 'lng': x_i[1]}
            r_i.append({'lat': x_i[0], 'lng': x_i[1]})
        rr.append(r_i)
    return json.dumps(rr), json.dumps(a_coord)

def get_entity_from_db(c, cur):
    cur.execute("select * from cadastres where id = %s", (c,))
    return cursor.fetchone()


def prefer_first(val1, val2):
    if val1 is not None:
        return val1
    return val2


cursor = get_db_cursor(db_name, db_user, db_pass, db_host)

row_count = count_csv_rows(input_file)
print("CSV has {} lines".format(row_count))

with open(input_file, newline='', encoding=INPUT_ENCODING) as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=INPUT_CSV_DELIMITER, quotechar=INPUT_CSV_QUOTE_CHAR)
    new_count = 0
    updated_count = 0
    faults_count = 0
    for idx, row in enumerate(csv_reader):
        if idx == 0:
            continue
        if idx % 100 == 0:
            None
            #print("Progress: {}/{}. New: {}, Updated: {}. Faults: {}".format(idx, row_count, new_count, updated_count, faults_count))

        owner_id = row[0]
        name = row[2]
        phone = None
        try:
            phone = ','.join(map(str, json.loads(row[1].replace("\"", "").replace("'", "").replace("-", "").replace(" ", ""))))
        except Exception as e:
            print("Fail: " + row[1])
        cadastres = json.loads(row[3].replace("'", "\"").replace(", nan", ""))

        try:
            cursor.execute("""insert into owners
                            (
                            id,
                            name,
                            type,
                            phone
                            )
                            values (%s,%s, 'ERAISIK', %s)""",
                            (owner_id, name, phone))
            for c in cadastres:
                try:
                    cursor.execute("""insert into owner_cadastres
                                                (
                                                owner_id,
                                                cadastre_id
                                                )
                                                values (%s,%s)""",
                                                (owner_id, cadastre_id))
                except Exception as e:
                    print("Failed to insert OC: " + row[0] + " - " + c)
        except Exception as e:
             print("Failed to insert owner: " + row[0])
             print(e)



        #print(json.dumps(cadastres))
