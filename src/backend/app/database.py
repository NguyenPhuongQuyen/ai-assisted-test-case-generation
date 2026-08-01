import os, psycopg2

from dotenv import load_dotenv
load_dotenv()

def get_connection():
    connection = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return connection

def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        return True, f"Kết nối thành công! PostgreSQL: {version[0]}"

    except Exception as e:
        return False, f"Kết nối thất bại: {str(e)}"