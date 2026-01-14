from flask import Flask, render_template, request, flash, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.secret_key = "dev-secret-key"

DATABASE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        aadhaar_number = request.form.get("aadhaar_number")
        voter_id = request.form.get("voter_id")
        email = request.form.get("email")
        password = request.form.get("password")
        


        # print("Full Name:", full_name)
        # print("aadhaar_number:", aadhaar_number)
        # print("voter_id:", voter_id)
        # print("Email:", email)
        # print("password:", password)
        # print("Hashed Password:", hashed_password)

        if not full_name or not email or not voter_id or not password:
            flash("All fields are required", "danger")
            return redirect(url_for("register"))
        
        
        if not aadhaar_number or len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            flash("Invalid Aadhaar number (must be exactly 12 digits)", "danger")
            return redirect(url_for("register"))
        
        
        # flash("Password hashing successful", "success")
        # return redirect(url_for("register"))
        
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        existing_user = cursor.execute(""" 
           SELECT * FROM users
           WHERE email = ? OR aadhaar_number = ? OR voter_id = ?                            
        
        """, (email, aadhaar_number, voter_id)).fetchone()
        
        
        if existing_user:
            conn.close()
            flash("User alredy exist", "danger")
            return redirect(url_for("register"))
        
        cursor.execute("""
            INSERT INTO users (full_name, email, password, aadhaar_number, voter_id, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (full_name, email, hashed_password, aadhaar_number, voter_id, "voter"))
    
        conn.commit()
        conn.close()
        
        flash("You have registered successfully!", "success")
        return redirect(url_for("register"))

    return render_template("registration.html")



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
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            aadhaar_number TEXT UNIQUE NOT NULL,
            voter_id TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL
);

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


# @app.route("/add-sample-data")
# def add_sample_data():
#     conn = get_db_connection()
#     cursor = conn.cursor()

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
        result += (
    f"ID: {user['id']}, "
    f"Name: {user['full_name']}, "
    f"Email: {user['email']}, "
    f"Aadhaar: {user['aadhaar_number']}, "
    f"Voter ID: {user['voter_id']}, "
    f"Role: {user['role']}<br>"
)


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
