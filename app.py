from flask import Flask, render_template, request, flash, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps





app = Flask(__name__)
app.secret_key = "dev-secret-key"


# DATABASE
DATABASE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

#home page
@app.route("/")
def home():
    return render_template("home.html")


# Register Page
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

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        voter_id = request.form["voter_id"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE voter_id = ?",
            (voter_id,)
        ).fetchone()
        conn.close()

        if user is None:
            flash("Voter ID not registered")
            return redirect(url_for("login"))

        if not check_password_hash(user["password"], password):
            flash("Incorrect password")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["voter_id"] = user["voter_id"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("voter_dashboard"))

    return render_template("login.html")

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first", "danger")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first", "danger")
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access required", "danger")
            return redirect(url_for("login"))

        return view_func(*args, **kwargs)
    return wrapper



# Admin and Functions
@app.route("/admin")
@admin_required
@login_required
def admin_dashboard():
    return render_template("admin/admin_dashboard.html")


@app.route("/admin/users")
@admin_required
@login_required
def admin_users():
    conn = get_db_connection()
    users = conn.execute("""
        SELECT id, full_name, email, voter_id, role
        FROM users
        WHERE id != ?
    """, (session["user_id"],)).fetchall()
    conn.close()

    return render_template("admin/admin_users.html", users=users)


@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@admin_required
@login_required
def delete_user(user_id):
    conn = get_db_connection()
    
    target_user = conn.execute(
        "SELECT id, voter_id FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    
    if target_user is None:
        conn.close()
        flash("User not found", "danger")
        return redirect(url_for("admin_users"))
    
    if target_user["id"] == session["user_id"]:
        conn.close()
        flash("You cannot delete your own account", "danger")
        return redirect(url_for("admin_users"))
    
    if target_user["voter_id"] == "SUPERADMIN":
        conn.close()
        flash("SUPERADMIN cannot be deleted", "danger")
        return redirect(url_for("admin_users"))
    
    
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("User deleted successfully", "success")
    return redirect(url_for("admin_users"))



@app.route("/admin/update-role/<int:user_id>", methods=["POST"])
@admin_required
@login_required
def update_role(user_id):
    new_role = request.form["role"]

    conn = get_db_connection()
    
    target_user = conn.execute(
        "SELECT id, voter_id, role FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    
    
    if target_user is None:
        conn.close()
        flash("User not found", "danger")
        return redirect(url_for("admin_users"))
    
    if target_user["voter_id"] == "SUPERADMIN":
        conn.close()
        flash("SUPERADMIN role cannot be changed", "danger")
        return redirect(url_for("admin_users"))
    
    if target_user["id"] == session["user_id"]:
        conn.close()
        flash("You cannot change your own role", "danger")
        return redirect(url_for("admin_users"))
    
    
    
    conn.execute(
        "UPDATE users SET role = ? WHERE id = ?",
        (new_role, user_id)
    )
    conn.commit()
    conn.close()

    flash("User role updated", "success")
    return redirect(url_for("admin_users"))


# Super_admin
def create_super_admin():
    conn = get_db_connection()
    admin = conn.execute(
        "SELECT * FROM users WHERE voter_id = ?",
        ("SUPERADMIN",)
    ).fetchone()

    if admin is None:
        conn.execute("""
            INSERT INTO users
            (full_name, email, password, aadhaar_number, voter_id, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Super Admin",
            "superadmin@ovs.com",
            generate_password_hash("admin123"),
            "000000000000",
            "SUPERADMIN",
            "admin"
        ))
        conn.commit()

    conn.close()

# Voters
@app.route("/voter")
@login_required
def voter_dashboard():
    return render_template("voter/voter_dashboard.html")

@app.route("/voter/results/<int:election_id>")
@login_required
def voter_results_alias(election_id):
    return redirect(url_for("public_results", election_id=election_id))

@app.route("/voter/results")
@login_required
def voter_results_list():
    conn = get_db_connection()

    elections = conn.execute("""
        SELECT id, title, status
        FROM elections
        WHERE status = 'closed'
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "voter/results_list.html",
        elections=elections
    )



# Logout
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))


# Election Creation 
@app.route("/admin/create-election", methods=["GET", "POST"])
@login_required
@admin_required
def create_election():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        if not title:
            flash("Election title is required", "danger")
            return redirect(url_for("create_election"))

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO elections (title, description, created_by)
            VALUES (?, ?, ?)
        """, (title, description, session["user_id"]))
        conn.commit()
        conn.close()

        flash("Election created successfully (status: upcoming)", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/create_election.html")

def create_elections_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT CHECK(status IN ('upcoming', 'active', 'closed')) NOT NULL DEFAULT 'upcoming',
            created_by INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    

def create_users_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            aadhaar_number TEXT UNIQUE NOT NULL,
            voter_id TEXT UNIQUE NOT NULL,
            role TEXT CHECK(role IN ('voter', 'admin')) NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_candidates_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            party_or_description TEXT,
            UNIQUE (election_id, user_id)
        )
    """)
    conn.commit()
    conn.close()
    
def create_votes_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            election_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, election_id)
        )
    """)
    conn.commit()
    conn.close()


# Add Candidates
@app.route("/admin/add-candidate/<int:election_id>", methods=["GET", "POST"])
@login_required
@admin_required
def add_candidate(election_id):
    conn = get_db_connection()

    election = conn.execute(
        "SELECT * FROM elections WHERE id = ?",
        (election_id,)
    ).fetchone()

    if election is None:
        conn.close()
        flash("Election not found", "danger")
        return redirect(url_for("admin_dashboard"))

    if election["status"] == "closed":
        conn.close()
        flash("Cannot add candidates to a closed election", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        user_id = request.form.get("user_id")
        display_name = request.form.get("display_name")
        description = request.form.get("party_or_description")

        user = conn.execute(
            "SELECT id, role FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if user is None:
            conn.close()
            flash("User does not exist", "danger")
            return redirect(request.url)

        if user["role"] == "admin":
            conn.close()
            flash("Admin cannot be a candidate", "danger")
            return redirect(request.url)

        try:
            conn.execute("""
                INSERT INTO candidates
                (election_id, user_id, display_name, party_or_description)
                VALUES (?, ?, ?, ?)
            """, (election_id, user_id, display_name, description))
            conn.commit()
            flash("Candidate added successfully", "success")
        except sqlite3.IntegrityError:
            flash("Candidate already added to this election", "warning")

        conn.close()
        return redirect(request.url)

    users = conn.execute(
        "SELECT id, full_name, voter_id FROM users WHERE role != 'admin'"
    ).fetchall()

    print("USERS DATA:", users)
    
    conn.close()
    return render_template(
        "admin/add_candidate.html",
        election=election,
        users=users
    )

@app.route("/admin/elections")
@login_required
@admin_required
def admin_elections():
    conn = get_db_connection()
    elections = conn.execute(
        "SELECT * FROM elections ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("admin/manage_elections.html", elections=elections)


@app.route("/debug/elections")
@login_required
@admin_required
def debug_elections():
    conn = get_db_connection()
    elections = conn.execute(
        "SELECT id, title FROM elections"
    ).fetchall()
    conn.close()
    return str([dict(e) for e in elections])


# View Candidates
@app.route("/admin/election/<int:election_id>/candidates")
@login_required
@admin_required
def admin_view_candidates(election_id):
    conn = get_db_connection()

    election = conn.execute(
        "SELECT * FROM elections WHERE id = ?",
        (election_id,)
    ).fetchone()

    if election is None:
        conn.close()
        flash("Election not found", "danger")
        return redirect(url_for("admin_elections"))

    candidates = conn.execute("""
        SELECT 
            c.display_name,
            c.party_or_description,
            u.full_name,
            u.voter_id
        FROM candidates c
        JOIN users u ON c.user_id = u.id
        WHERE c.election_id = ?
    """, (election_id,)).fetchall()

    conn.close()
    return render_template(
        "admin/view_candidates.html",
        election=election,
        candidates=candidates
    )
    
@app.route("/admin/close-election/<int:election_id>", methods=["POST"])
@login_required
@admin_required
def close_election(election_id):
    conn = get_db_connection()

    election = conn.execute(
        "SELECT status FROM elections WHERE id = ?",
        (election_id,)
    ).fetchone()

    if election is None:
        conn.close()
        flash("Election not found", "danger")
        return redirect(url_for("admin_elections"))

    if election["status"] != "active":
        conn.close()
        flash("Only active elections can be closed", "warning")
        return redirect(url_for("admin_elections"))

    conn.execute(
        "UPDATE elections SET status = 'closed' WHERE id = ?",
        (election_id,)
    )
    conn.commit()
    conn.close()

    flash("Election closed successfully", "success")
    return redirect(url_for("admin_elections"))


@app.route("/debug/votes")
@login_required
@admin_required
def debug_votes():
    conn = get_db_connection()
    votes = conn.execute("SELECT * FROM votes").fetchall()
    conn.close()
    return str([dict(v) for v in votes])

# Activation of Election
@app.route("/admin/activate-election/<int:election_id>", methods=["POST"])
@login_required
@admin_required
def activate_election(election_id):
    conn = get_db_connection()

    election = conn.execute(
        "SELECT status FROM elections WHERE id = ?",
        (election_id,)
    ).fetchone()

    if election is None:
        conn.close()
        flash("Election not found", "danger")
        return redirect(url_for("admin_elections"))

    if election["status"] != "upcoming":
        conn.close()
        flash("Only upcoming elections can be activated", "warning")
        return redirect(url_for("admin_elections"))

    conn.execute(
        "UPDATE elections SET status = 'active' WHERE id = ?",
        (election_id,)
    )
    conn.commit()
    conn.close()

    flash("Election activated successfully", "success")
    return redirect(url_for("admin_elections"))

@app.route("/admin/results/<int:election_id>")
@admin_required
def admin_results(election_id):
    conn = get_db_connection()

    results = []
    winners = []
    max_votes = 0

    # 1. Fetch election
    election = conn.execute(
        "SELECT * FROM elections WHERE id = ?",
        (election_id,)
    ).fetchone()

    if election is None:
        conn.close()
        abort(404)

    # 2. Ensure election is closed
    if election["status"] != "closed":
        conn.close()
        abort(403)

    # 3. Fetch candidates with vote counts  ✅ NOW CORRECT
    results = conn.execute("""
        SELECT 
            c.id AS candidate_id,
            c.display_name AS candidate_name,
            c.party_or_description AS party,
            COUNT(v.id) AS vote_count
        FROM candidates c
        LEFT JOIN votes v 
            ON c.id = v.candidate_id 
            AND v.election_id = ?
        WHERE c.election_id = ?
        GROUP BY c.id
        ORDER BY vote_count DESC
    """, (election_id, election_id)).fetchall()

    conn.close()

    # 4. Determine winner(s)
    if results:
        max_votes = max(row["vote_count"] for row in results)
        winners = [row["candidate_id"] for row in results if row["vote_count"] == max_votes]

    return render_template(
        "admin/admin_results.html",
        election=election,
        results=results,
        winners=winners,
        max_votes=max_votes
    )



@app.route("/voter/elections")
@login_required
def voter_elections():
    conn = get_db_connection()
    elections = conn.execute("""
        SELECT id, title, description
        FROM elections
        WHERE status = 'active'
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    return render_template(
        "voter/elections.html",
        elections=elections
    )

@app.route("/voter/vote/<int:election_id>", methods=["GET", "POST"])
@login_required
def vote(election_id):
    conn = get_db_connection()

    # 1. Check election
    election = conn.execute(
        "SELECT * FROM elections WHERE id = ?",
        (election_id,)
    ).fetchone()

    if election is None:
        conn.close()
        flash("Election not found", "danger")
        return redirect(url_for("voter_elections"))

    if election["status"] != "active":
        conn.close()
        flash("Voting is not allowed for this election", "warning")
        return redirect(url_for("voter_elections"))

    # 2. Check if user already voted
    existing_vote = conn.execute(
        "SELECT id FROM votes WHERE user_id = ? AND election_id = ?",
        (session["user_id"], election_id)
    ).fetchone()

    if existing_vote:
        conn.close()
        flash("You have already voted in this election", "info")
        return redirect(url_for("voter_elections"))

    # 3. Handle vote submission
    if request.method == "POST":
        candidate_id = request.form.get("candidate_id")

        candidate = conn.execute(
            "SELECT id FROM candidates WHERE id = ? AND election_id = ?",
            (candidate_id, election_id)
        ).fetchone()

        if candidate is None:
            conn.close()
            flash("Invalid candidate selection", "danger")
            return redirect(request.url)

        try:
            conn.execute("""
                INSERT INTO votes (user_id, election_id, candidate_id)
                VALUES (?, ?, ?)
            """, (session["user_id"], election_id, candidate_id))
            conn.commit()
            flash("Your vote has been recorded successfully", "success")
        except sqlite3.IntegrityError:
            flash("Duplicate vote attempt blocked", "warning")

        conn.close()
        return redirect(url_for("voter_elections"))

    # 4. Show candidates
    candidates = conn.execute("""
        SELECT 
            c.id,
            c.display_name,
            c.party_or_description,
            u.full_name
        FROM candidates c
        JOIN users u ON c.user_id = u.id
        WHERE c.election_id = ?
    """, (election_id,)).fetchall()

    conn.close()
    return render_template(
        "voter/vote.html",
        election=election,
        candidates=candidates
    )

@app.route("/results/<int:election_id>")
@login_required
def public_results(election_id):
    conn = get_db_connection()

    # 1. Fetch election
    election = conn.execute(
        "SELECT * FROM elections WHERE id = ?",
        (election_id,)
    ).fetchone()

    if election is None:
        conn.close()
        abort(404)

    # 2. Election must be closed
    if election["status"] != "closed":
        conn.close()
        abort(403)

    # 3. Fetch results
    results = conn.execute("""
    SELECT 
        c.id AS candidate_id,
        c.display_name AS candidate_name,
        c.party_or_description AS party,
        COUNT(v.id) AS vote_count
    FROM candidates c
    LEFT JOIN votes v 
        ON c.id = v.candidate_id 
        AND v.election_id = ?
    WHERE c.election_id = ?
    GROUP BY c.id
    ORDER BY vote_count DESC
""", (election_id, election_id)).fetchall()



    conn.close()

    max_votes = 0
    winners = []

    if results:
        max_votes = max(row["vote_count"] for row in results)
        winners = [row["candidate_id"] for row in results if row["vote_count"] == max_votes]

    return render_template(
        "voter/results.html",
        election=election,
        results=results,
        winners=winners,
        max_votes=max_votes
    )


if __name__ == "__main__":
    create_users_table()
    create_elections_table()
    create_candidates_table()
    create_votes_table()
    create_super_admin()
    app.run(debug=True)

