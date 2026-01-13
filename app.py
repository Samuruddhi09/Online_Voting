from flask import Flask
import sqlite3

app = Flask(__name__)

DATABASE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return "Online Voting System is running!"

@app.route("/init-db")
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            aadhaar TEXT UNIQUE NOT NULL,
            voter_id TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            is_active INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            election_id INTEGER,
            FOREIGN KEY (election_id) REFERENCES elections(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            election_id INTEGER,
            candidate_id INTEGER,
            UNIQUE(user_id, election_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (election_id) REFERENCES elections(id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    """)

    conn.commit()
    conn.close()

    return "Database tables created successfully!"


@app.route("/add-sample-data")
def add_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert admin
    cursor.execute("""
        INSERT INTO users (name, aadhaar, voter_id)
        VALUES (?, ?, ?)
    """, ("Admin User", "111122223333", "ADMIN001"))

    # Insert voter
    cursor.execute("""
        INSERT INTO users (name, aadhaar, voter_id)
        VALUES (?, ?, ?)
    """, ("Voter One", "444455556666", "VOTER001"))

    # Insert election
    cursor.execute("""
        INSERT INTO elections (title, is_active)
        VALUES (?, ?)
    """, ("Student Council Election", 1))

    # Insert candidate
    cursor.execute("""
        INSERT INTO candidates (name, election_id)
        VALUES (?, ?)
    """, ("Candidate A", 1))

    conn.commit()
    conn.close()

    return "Sample data inserted successfully!"


@app.route("/view-users")
def view_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    result = ""
    for user in users:
        result += f"ID: {user['id']}, Name: {user['name']}, Aadhaar: {user['aadhaar']}<br>"

    return result


@app.route("/view-elections")
def view_elections():
    conn = get_db_connection()
    elections = conn.execute("SELECT * FROM elections").fetchall()
    conn.close()

    result = ""
    for election in elections:
        result += f"ID: {election['id']}, Title: {election['title']}, Active: {election['is_active']}<br>"

    return result


@app.route("/view-candidates")
def view_candidates():
    conn = get_db_connection()
    candidates = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close()

    result = ""
    for candidate in candidates:
        result += f"ID: {candidate['id']}, Name: {candidate['name']}, Election ID: {candidate['election_id']}<br>"

    return result


if __name__ == "__main__":
    app.run(debug=True)
