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
    if v == "NULL":
        return None
    return v


def get_owner_from_db(c, cur):
    cur.execute("select * from owners where id = %s", (c,))
    return cursor.fetchone()


def prefer_first(val1, val2):
    if val1 is not None:
        return val1
    return val2


cursor = get_db_cursor(db_name, db_user, db_pass, db_host)

row_count = count_csv_rows(input_file)
print("CSV has {} lines".format(row_count))

with open(input_file, newline='', encoding=INPUT_ENCODING) as csvfile:
    omanikudreader = csv.reader(csvfile, delimiter=INPUT_CSV_DELIMITER, quotechar=INPUT_CSV_QUOTE_CHAR)
    new_owner_count = 0
    updated_owner_count = 0
    faulty_codes_count = 0
    for idx, row in enumerate(omanikudreader):
        if idx % 100 == 0:
            print("Progress: {}/{}. New owners: {}, Updated owners: {}. Faulty codes: {}".format(idx, row_count,
                                                                                                 new_owner_count,
                                                                                                 updated_owner_count,
                                                                                                 faulty_codes_count))
        name = trim(row[0])
        email = trim(row[1])
        phone = trim(row[2])
        id_status = trim(row[3]) # ? == 35 -> Sigmarile
        comment = trim(row[4])  # 4 - Comment; logisse
        # address = trim(row[5])  # ID ASSOTS
        code = trim(row[6])
        extra_phones = trim(row[7])  # INFO

        assignee = "autocreated" if id_status == "35" else None

        if code is None or len(code) != 11 or (code[0] != '3' and code[0] != '4' and code[0] != '5' and code[0] != '6'):
            faulty_codes_count += 1
            continue

        owner_from_db = get_owner_from_db(code, cursor)
        if owner_from_db is None:
            new_owner_count += 1
            try:
                cursor.execute(
                    "insert into owners (id, name, phone, type, email, info, caller_id) values (%s,%s,%s,%s,%s,%s,%s)",
                    (code, name, phone, 'ERAISIK', email, extra_phones, assignee))
                if comment:
                    cursor.execute("insert into owner_log (timestamp, owner_id, creator, message) values (NOW(),%s,%s,%s)",
                                   (code, "Mets-IS System", comment))
            except Exception as e:
                print(e)
        else:
            updated_owner_count += 1
            n = prefer_first(name, owner_from_db['name'])
            p = prefer_first(phone, owner_from_db['phone'])
            e = prefer_first(email, owner_from_db['email'])
            i = extra_phones
            try:
                cursor.execute(
                    "update owners set name = %s, phone = %s, email = %s, info = %s, caller_id = %s where id = %s",
                    (n, p, e, i, assignee, code))
                if comment:
                    cursor.execute("insert into owner_log (timestamp, owner_id, creator, message) values (NOW(),%s,%s,%s)",
                                   (code, "Mets-IS System", comment))
            except Exception as e:
                print(e)
    print("Progress: {}/{}. New owners: {}, Updated owners: {}. Faulty codes: {}".format(row_count,
                                                                                       row_count,
                                                                                       new_owner_count,
                                                                                       updated_owner_count,
                                                                                       faulty_codes_count))
