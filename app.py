from flask import Flask, render_template, request, flash, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash,check_password_hash
from functools import wraps





app = Flask(__name__)
app.secret_key = "dev-secret-key"


# DATABASE
DATABASE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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
    return "Welcome Voter! Session active."

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



if __name__ == "__main__":
    create_super_admin()
    app.run(debug=True)
