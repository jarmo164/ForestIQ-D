"""
Script for data import to MetsisEE.
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

def entity_exists(c, cur):
    cur.execute("select count(*) as cnt from owners where id = %s", (c,))
    return cursor.fetchone()['cnt'] == 1

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
            print("Progress: {}/{}. New entities: {}, Updated entities: {}. Faulty entities: {}".format(idx, row_count, new_count, updated_count, faults_count))

        owner_id = row[0]
        if entity_exists(owner_id, cursor):
            try:
                phone = row[1]
                mail = row[2]
                if phone != None and phone != "":
                    cursor.execute("update owners set phone = '" + str(phone) + "' where id = '" + str(owner_id) + "'")
                if mail != None and mail != "":
                    cursor.execute("update owners set email = '" + str(mail) + "' where id = '" + str(owner_id) + "'")
                updated_count += 1
            except Exception as e:
                faults_count += 1
                print(e)

print("Progress: {}/{}. New entities: {}, Updated entities: {}. Faulty entities: {}".format(row_count,
                                                                                   row_count,
                                                                                   new_count,
                                                                                   updated_count,
                                                                                   faults_count))
