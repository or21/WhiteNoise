import psycopg2


def db_connect():
    try:
        conn_string = "host='localhost' dbname='WhiteNoise' user='postgres' password='Aa123456' port=5000"
        print("Connecting to database\n	{}".format(conn_string))
        return psycopg2.connect(conn_string)

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

db = db_connect()


def select_keywords_from_db(keyword_id):
    command = "SELECT (last_change) FROM keywords where kw_id = '{}'".format(keyword_id)
    db_cursor = db.cursor()
    db_cursor.execute(command)
    rows = db_cursor.fetchall()
    return rows


def write_keyword_to_db(kw_data, campaign_name, date):
    db_cursor = db.cursor()
    command = "INSERT INTO keywords(kw_id, kw_name, campaign_name, last_change) " \
              "VALUES('{}', '{}', '{}', '{}') " \
              "ON CONFLICT (kw_id) DO UPDATE SET last_change = excluded.last_change" \
        .format(kw_data.id, kw_data.name.replace("'", "''"), campaign_name.replace("'", "''"), date)
    db_cursor.execute(command)
    db.commit()
