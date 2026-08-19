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

def update_owner(id, name, cur):
    cur.execute("update owners set name=%s where id = %s", (name,id,))

cursor = get_db_cursor(db_name, db_user, db_pass, db_host)

row_count = count_csv_rows(input_file)
print("CSV has {} lines".format(row_count))

with open(input_file, newline='', encoding=INPUT_ENCODING) as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=INPUT_CSV_DELIMITER, quotechar=INPUT_CSV_QUOTE_CHAR)
    new_count = 0
    updated_count = 0
    faults_count = 0
    for idx, row in enumerate(csv_reader):
        if idx % 100 == 0:
            print("Progress: {}/{}. New: {}, Updated: {}.".format(idx, row_count, new_count, updated_count))

        owner_id = row[0]
        name = row[1]
        update_owner(owner_id, name, cursor)
