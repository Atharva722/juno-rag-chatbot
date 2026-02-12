import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables, especially for local development
load_dotenv()

# Render provides the DATABASE_URL environment variable
# for connecting to the PostgreSQL database
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def create_tables():
    """Creates the necessary tables if they don't exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Use SERIAL PRIMARY KEY for auto-incrementing IDs in PostgreSQL
    cur.execute('''
        CREATE TABLE IF NOT EXISTS application_logs (
            id SERIAL PRIMARY KEY,
            session_id TEXT,
            user_query TEXT,
            gpt_response TEXT,
            model TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS document_store (
            id SERIAL PRIMARY KEY,
            filename TEXT,
            upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def insert_application_logs(session_id, user_query, gpt_response, model):
    conn = get_db_connection()
    cur = conn.cursor()
    # Use %s for placeholders in psycopg2
    cur.execute(
        'INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (%s, %s, %s, %s)',
        (session_id, user_query, gpt_response, model)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_chat_history(session_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_query, gpt_response FROM application_logs WHERE session_id = %s ORDER BY created_at', (session_id,))
    history = cur.fetchall()
    cur.close()
    conn.close()
    
    messages = []
    for row in history:
        messages.extend([
            {"role": "human", "content": row['user_query']},
            {"role": "ai", "content": row['gpt_response']}
        ])
    return messages

def insert_document_record(filename):
    conn = get_db_connection()
    cur = conn.cursor()
    # The RETURNING id clause is a PostgreSQL feature to get the last inserted ID
    cur.execute('INSERT INTO document_store (filename) VALUES (%s) RETURNING id', (filename,))
    file_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    return file_id

def delete_document_record(file_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM document_store WHERE id = %s', (file_id,))
    conn.commit()
    cur.close()
    conn.close()
    return True

def get_all_documents():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC')
    documents = cur.fetchall()
    cur.close()
    conn.close()
    return documents

# Initialize the tables when the application starts
create_tables()