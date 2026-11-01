
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)
import sqlite3
import os
from contextlib import contextmanager
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "food-bridge-dev-key"
)

DATABASE = os.path.join(app.root_path, "food_bridge.db")


# ---------------- DATABASE CONNECTION ----------------

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------- CREATE DATABASE TABLES ----------------

def init_db():
    with get_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_name TEXT NOT NULL,
                quantity TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL DEFAULT '',
                donor_id INTEGER,
                FOREIGN KEY (donor_id) REFERENCES users(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS donation_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donation_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(donation_id, receiver_id),
                FOREIGN KEY (donation_id) REFERENCES donations(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        """)

        # Add missing columns without deleting existing records
        user_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(users)")
        }

        donation_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(donations)")
        }

        if "role" not in user_columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'receiver'"
            )

        if "contact" not in donation_columns:
            conn.execute(
                "ALTER TABLE donations ADD COLUMN contact TEXT NOT NULL DEFAULT ''"
            )

        if "donor_id" not in donation_columns:
            conn.execute(
                "ALTER TABLE donations ADD COLUMN donor_id INTEGER"
            )


init_db()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip().lower()

        if not name or not email or not password or not role:
            flash("Please fill in all the details.", "error")
            return redirect(url_for("register"))

        if role not in ["donor", "receiver"]:
            flash("Please select Donor or Receiver.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return redirect(url_for("register"))

        try:
            with get_db() as conn:

                existing_user = conn.execute(
                    "SELECT id FROM users WHERE LOWER(email) = ?",
                    (email,)
                ).fetchone()

                if existing_user:
                    flash("Account already exists! Please login.", "error")
                    return redirect(url_for("login"))

                hashed_password = generate_password_hash(password)

                conn.execute("""
                    INSERT INTO users (name, email, password, role)
                    VALUES (?, ?, ?, ?)
                """, (
                    name,
                    email,
                    hashed_password,
                    role
                ))

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

        except sqlite3.Error as error:
            print("Registration database error:", error)
            flash("Registration failed. Please check the terminal error.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as conn:

            user = conn.execute(
                "SELECT * FROM users WHERE LOWER(email) = ?",
                (email,)
            ).fetchone()

            valid_password = False

            if user:
                stored_password = user["password"]

                try:
                    valid_password = check_password_hash(
                        stored_password, password
                    )
                except (ValueError, TypeError):
                    valid_password = False

                # Support accounts created earlier with plain-text passwords
                if not valid_password and stored_password == password:
                    valid_password = True

                    conn.execute("""
                        UPDATE users
                        SET password = ?
                        WHERE id = ?
                    """, (
                        generate_password_hash(password),
                        user["id"]
                    ))

            if user and valid_password:

                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["role"] = user["role"].lower()

                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        role=session.get("role")
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()
    flash("You have logged out.", "success")

    return redirect(url_for("home"))


# ---------------- DONATE FOOD ----------------

@app.route("/donate", methods=["GET", "POST"])
def donate():

    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") != "donor":
        flash("Only donors can donate food.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        food_name = request.form.get("food_name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        location = request.form.get("location", "").strip()
        contact = request.form.get("contact", "").strip()

        if not all([food_name, quantity, location, contact]):
            flash("Please fill in all donation details.", "error")
            return redirect(url_for("donate"))

        with get_db() as conn:

            conn.execute("""
                INSERT INTO donations
                (food_name, quantity, location, contact, donor_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                food_name,
                quantity,
                location,
                contact,
                session["user_id"]
            ))

        flash("Food donation submitted successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("donate.html")


# ---------------- AVAILABLE FOOD ----------------

@app.route("/available-food")
def available_food():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "receiver":
        flash("Please log in with a receiver account.", "error")
        return redirect(url_for("dashboard"))

    with get_db() as conn:

        donations = conn.execute("""
            SELECT
                donations.*,
                users.name AS donor_name
            FROM donations
            LEFT JOIN users
                ON donations.donor_id = users.id
            ORDER BY donations.id DESC
        """).fetchall()

    return render_template(
        "available_food.html",
        donations=donations
    )


# ---------------- REQUEST FOOD ----------------

@app.route("/request-food/<int:donation_id>", methods=["POST"])
def request_food(donation_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "receiver":
        flash("Only receivers can request food.", "error")
        return redirect(url_for("dashboard"))

    with get_db() as conn:

        donation = conn.execute(
            "SELECT id FROM donations WHERE id = ?",
            (donation_id,)
        ).fetchone()

        if donation is None:
            flash("Food donation not found.", "error")
            return redirect(url_for("available_food"))

        try:
            conn.execute("""
                INSERT INTO donation_requests
                (donation_id, receiver_id)
                VALUES (?, ?)
            """, (
                donation_id,
                session["user_id"]
            ))

            flash("Food request submitted successfully!", "success")

        except sqlite3.IntegrityError:
            flash("You have already requested this donation.", "error")

    return redirect(url_for("available_food"))

# ---------------- RECEIVER MY REQUESTS ----------------

@app.route("/my-requests")
def my_requests():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "receiver":
        flash("Only receivers can view their requests.", "error")
        return redirect(url_for("dashboard"))

    with get_db() as conn:

        requests_list = conn.execute("""
    SELECT
        donation_requests.id,
        donation_requests.status,
        donation_requests.created_at,
        donations.food_name,
        donations.quantity,
        donations.location,
        donations.contact,
        users.name AS donor_name
    FROM donation_requests
    JOIN donations
        ON donation_requests.donation_id = donations.id
    LEFT JOIN users
        ON donations.donor_id = users.id
    WHERE donation_requests.receiver_id = ?
    ORDER BY donation_requests.id DESC
""", (session["user_id"],)).fetchall()
    return render_template(
        "my_requests.html",
        requests_list=requests_list
    )#----------------  DONOR REQUESTS ----------------

# ---------------- DONOR REQUESTS ----------------

@app.route("/donor-requests")
def donor_requests():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "donor":
        flash("Only donors can view incoming requests.", "error")
        return redirect(url_for("dashboard"))

    with get_db() as conn:

        donor_id = session["user_id"]

        # Debug information
        print("\n----- DONOR REQUEST DEBUG -----")
        print("Logged-in Donor ID:", donor_id)

        all_donations = conn.execute("""
            SELECT id, food_name, donor_id
            FROM donations
        """).fetchall()

        print("All Donations:")
        for donation in all_donations:
            print(dict(donation))

        all_requests = conn.execute("""
            SELECT id, donation_id, receiver_id, status
            FROM donation_requests
        """).fetchall()

        print("All Requests:")
        for req in all_requests:
            print(dict(req))

        # Fetch requests belonging to this donor
        requests_list = conn.execute("""
            SELECT
                donation_requests.id AS id,
                donation_requests.status,
                donation_requests.created_at,
                donations.food_name,
                donations.quantity,
                donations.location,
                users.name AS receiver_name
            FROM donation_requests
            JOIN donations
                ON donation_requests.donation_id = donations.id
            JOIN users
                ON donation_requests.receiver_id = users.id
            WHERE donations.donor_id = ?
            ORDER BY donation_requests.id DESC
        """, (donor_id,)).fetchall()

        print("Requests for this donor:", len(requests_list))
        print("-------------------------------\n")

    return render_template(
        "donor_requests.html",
        requests_list=requests_list
    )

# ---------------- APPROVE / REJECT REQUEST ----------------

@app.route("/update-request/<int:request_id>", methods=["POST"])
def update_request(request_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "donor":
        flash("Only donors can update requests.", "error")
        return redirect(url_for("dashboard"))

    new_status = (
        request.form.get("status")
        or request.args.get("status")
    )

    if new_status not in ("Approved", "Rejected"):
        flash("Invalid request status.", "error")
        return redirect(url_for("donor_requests"))

    with get_db() as conn:

        result = conn.execute("""
            UPDATE donation_requests
            SET status = ?
            WHERE id = ?
              AND status = 'Pending'
              AND donation_id IN (
                  SELECT id
                  FROM donations
                  WHERE donor_id = ?
              )
        """, (
            new_status,
            request_id,
            session["user_id"]
        ))

        if result.rowcount:
            flash(
                f"Request {new_status.lower()} successfully.",
                "success"
            )
        else:
            flash(
                "Request not found or already processed.",
                "error"
            )

    return redirect(url_for("donor_requests"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)
