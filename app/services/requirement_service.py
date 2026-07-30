from app.database import get_connection

def save_requirement(filename, file_type, content):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
          INSERT INTO requirements (filename, file_type, content)
          VALUES (%s, %s, %s)
          RETURNING id, created_at \
          """

    cursor.execute(sql, (filename, file_type, content))
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    return row[0], row[1]