"""
Script for massive data import to MetsisEE.
Run:
python3 db_name db_user db_pass db_host input_file
"""

import csv
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

INPUT_ENCODING = 'Windows-1252'
INPUT_CSV_DELIMITER = ';'
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


cursor = get_db_cursor(db_name, db_user, db_pass, db_host)

row_count = count_csv_rows(input_file)
print("CSV has {} lines".format(row_count))

with open(input_file, newline='', encoding=INPUT_ENCODING) as csvfile:
    dump_reader = csv.reader(csvfile, delimiter=INPUT_CSV_DELIMITER, quotechar=INPUT_CSV_QUOTE_CHAR)
    faulty_rows = 0
    for idx, row in enumerate(dump_reader):
        if idx % 100 == 0:
            print("Progress: {}/{}. Faulty rows: {}".format(idx, row_count, faulty_rows))
        source = trim(row[3])
        name = trim(row[0])
        phone = trim(row[2])
        address = trim(row[1])
        code = trim(row[4])
        try:
            cursor.execute(
                "insert into persons_dump (source, name, phone, address, code) "
                "values (%s,%s,%s,%s,%s)",
                (source, name, phone, address, code))
        except Exception as e:
            print(e)
            faulty_rows += 1
    print("Progress: {}/{}. Faulty rows: {}".format(row_count, row_count, faulty_rows))
