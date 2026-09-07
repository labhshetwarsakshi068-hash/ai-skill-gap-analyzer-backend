import mysql.connector


def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Mysql@12345",
        database="skill_gap_analyzer"
    )

    return connection