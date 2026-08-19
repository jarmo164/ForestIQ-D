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
        print(connect_str)
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

def str_or_substr(inp):
    if inp == None:
        return None
    if len(inp) <= 100:
        return inp
    return inp[:100]

def parse_phones(inp):
    inp = inp.replace("\"", "").replace("'", "\"").replace("-", "").replace(" ", "")
    return str_or_substr(trim(','.join(map(str, json.loads(inp)))))

def parse_cadastres(inp):
    inp = inp.replace("'", "\"").replace(", nan", "").replace("nan, ", "").replace("nan", "")
    return json.loads(inp)

def get_owner_from_db(c, cur):
    cur.execute("select * from owners where id = %s", (c,))
    return cursor.fetchone()

def insert_owner_cadastre(o, c, cur):
    cur.execute("insert into owner_cadastre(owner_id, cadastre_id) values (%s,%s)", (o,c,))

def insert_owner(id, name, type, phone, cur):
    cur.execute("insert into owners(id, name, type, phone) values (%s,%s,%s,%s)", (id,name,type,phone,))

def update_owner(id, name, type, phone, cur):
    if type == "ERAISIK" or type == "FIRMA":
        cur.execute("update owners set name=%s, type=%s, phone=%s where id = %s", (name,type,phone,id,))

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
            print("Progress: {}/{}. New: {}, Updated: {}.".format(idx, row_count, new_count, updated_count))

        owner_id = row[0]
        name = row[1]
        cadastres = parse_cadastres(row[2])
        type = "ERAISIK"
        phone = parse_phones(row[3])

        owner = get_owner_from_db(owner_id, cursor)
        if (owner is None):
            insert_owner(owner_id, name, type, phone, cursor)
            new_count += 1
        else:
            update_owner(
                owner_id,
                prefer_first(owner['name'], name),
                prefer_first(owner['type'], type),
                prefer_first(phone, owner['phone']),
                cursor
            )
            updated_count += 1
        for cadastre in cadastres:
            try:
                insert_owner_cadastre(owner_id, cadastre, cursor)
            except Exception as e:
                print("Failed to insert owner_cadastre. Owner_id="+owner_id+",Cadastre="+cadastre)
                print(e)
