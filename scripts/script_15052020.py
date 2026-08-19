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
            print("Progress: {}/{}. New: {}, Updated: {}. Faults: {}".format(idx, row_count, new_count, updated_count, faults_count))

        cadastre_no = row[0]
        address = row[1]
        municipality = row[2].replace(' vald', '').replace(' linn', '')
        county = row[3].replace(' maakond', '').replace(' linn', '')
        reg_no = row[4]
        type = row[5]
        polygon, centroid = norm_json(row[6])
        area = row[7]
        bulkarea = row[8]
        arable_area = row[9]
        meadow_area = row[10]
        forest_area = row[11]
        yard_area = row[12]
        other_area = row[13]
        underwater_area = 0
        buildings_area = 0

        entity_from_db = get_entity_from_db(cadastre_no, cursor)
        if entity_from_db is None:
            try:
                cursor.execute(
                    """insert into cadastres
                    (
                    id,
                    address,
                    municipality,
                    county,
                    reg_nr,
                    type,
                    polygon,
                    centroid,
                    area,
                    arable_area,
                    yard_area,
                    meadow_area,
                    forest_area,
                    underwater_area,
                    buildings_area,
                    other_area
                    )
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (cadastre_no, address, municipality, county, reg_no, type, polygon, centroid, area, arable_area, yard_area, meadow_area, forest_area, underwater_area, buildings_area, other_area))
                new_count += 1
            except Exception as e:
                faults_count += 1
                print(e)
        else:
            u_address = prefer_first(entity_from_db['address'], address)
            u_municipality = prefer_first(entity_from_db['municipality'], municipality)
            u_county = prefer_first(entity_from_db['county'], county)
            u_reg_no = prefer_first(entity_from_db['reg_nr'], reg_no)
            u_type = prefer_first(entity_from_db['type'], type)
            u_polygon = prefer_first(entity_from_db['polygon'], polygon)
            u_centroid = prefer_first(entity_from_db['centroid'], centroid)
            u_area = prefer_first(entity_from_db['area'], area)
            u_arable_area = prefer_first(entity_from_db['arable_area'], arable_area)
            u_meadow_area = prefer_first(entity_from_db['meadow_area'], meadow_area)
            u_forest_area = prefer_first(entity_from_db['forest_area'], forest_area)
            u_yard_area = prefer_first(entity_from_db['yard_area'], yard_area)
            u_other_area = prefer_first(entity_from_db['other_area'], other_area)
            try:
                cursor.execute(
                    """update cadastres
                    set address = %s,
                    municipality = %s,
                    county = %s,
                    reg_nr = %s,
                    type = %s,
                    polygon = %s,
                    centroid = %s,
                    area = %s,
                    arable_area = %s,
                    meadow_area = %s,
                    forest_area = %s,
                    yard_area = %s,
                    other_area = %s
                    where id = %s
                    """,
                    (u_address, u_municipality, u_county, u_reg_no, u_type, u_polygon, u_centroid, u_area, u_arable_area, u_meadow_area, u_forest_area, u_yard_area, u_other_area, cadastre_no))
                updated_count += 1
            except Exception as e:
                faults_count += 1
                print(e)
    print("Progress: {}/{}. New owners: {}, Updated owners: {}. Faulty codes: {}".format(row_count,
                                                                                       row_count,
                                                                                       new_owner_count,
                                                                                       updated_owner_count,
                                                                                       faulty_codes_count))
