import psycopg2

def get_connection():
    conn = psycopg2.connect(
        host="137.184.122.9",
        database="TestDb",
        user="hwnuser",
        password="HWNActive@$%!22")

    cur = conn.cursor()
    return cur, conn