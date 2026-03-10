import sqlite3
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)
DB = "aceest.db"

PROGRAMS = {
    "Fat Loss (FL) – 3 day": {"calorie_factor": 22, "desc": "3-day full-body fat loss"},
    "Fat Loss (FL) – 5 day": {
        "calorie_factor": 24,
        "desc": "5-day split, higher volume",
    },
    "Muscle Gain (MG) – PPL": {
        "calorie_factor": 35,
        "desc": "Push/Pull/Legs hypertrophy",
    },
    "Beginner (BG)": {"calorie_factor": 26, "desc": "3-day beginner full-body"},
}


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def db_error(e):
    return jsonify({"error": str(e)}), 500


def init_db():
    try:
        conn = get_db()
        conn.execute(
            """CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE,
            age INTEGER, height REAL, weight REAL, program TEXT, calories INTEGER,
            target_weight REAL, target_adherence INTEGER, membership_expiry TEXT)"""
        )
        # Safe ALTER TABLE — adds columns only if they don't exist (existing DB from earlier versions)
        for col, typ in [
            ("height", "REAL"),
            ("target_weight", "REAL"),
            ("target_adherence", "INTEGER"),
            ("membership_expiry", "TEXT"),
        ]:
            try:
                conn.execute(f"ALTER TABLE clients ADD COLUMN {col} {typ}")
            except Exception:
                pass  # column already exists — safe to ignore
        # Add 3 new tables:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT,
            date TEXT, workout_type TEXT, duration_min INTEGER, notes TEXT)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT, workout_id INTEGER,
            name TEXT, sets INTEGER, reps INTEGER, weight REAL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT,
            date TEXT, weight REAL, waist REAL, bodyfat REAL)"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT,
            week TEXT, adherence INTEGER)"""
        )
        conn.commit()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()


init_db()


# --- existing routes from v1.1 (unchanged) ---
@app.route("/")
def index():
    return jsonify({"message": "ACEest Fitness API", "status": "ok"})


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/programs")
def get_programs():
    return jsonify({"programs": list(PROGRAMS.keys())})


@app.route("/program/<name>")
def get_program(name):
    if name not in PROGRAMS:
        return jsonify({"error": "Not found"}), 404
    return jsonify(PROGRAMS[name])


@app.route("/calculate_calories", methods=["POST"])
def calculate_calories():
    data = request.get_json()
    weight = data.get("weight")
    program = data.get("program")
    if not weight or not program:
        return jsonify({"error": "weight and program required"}), 400
    if program not in PROGRAMS:
        return jsonify({"error": "Invalid program"}), 404
    if not isinstance(weight, (int, float)) or weight <= 0:
        return jsonify({"error": "Invalid weight"}), 400
    return jsonify(
        {
            "calories": int(weight * PROGRAMS[program]["calorie_factor"]),
            "program": program,
            "weight": weight,
        }
    )


# --- new routes from Aceestver2_0_1.py ---
@app.route("/client", methods=["POST"])
def save_client():
    data = request.get_json()
    name = data.get("name")
    program = data.get("program")
    if not name or not program:
        return jsonify({"error": "name and program required"}), 400
    if program not in PROGRAMS:
        return jsonify({"error": "Invalid program"}), 404
    weight = data.get("weight", 0)
    age = data.get("age", 0)
    height = data.get("height", 0)
    calories = int(weight * PROGRAMS[program]["calorie_factor"])
    try:
        conn = get_db()
        conn.execute(
            "INSERT OR REPLACE INTO clients (name,age,height,weight,program,calories) VALUES (?,?,?,?,?,?)",
            (name, age, height, weight, program, calories),
        )
        conn.commit()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    return jsonify({"message": "Client saved", "name": name, "calories": calories})


@app.route("/client/<name>")
def get_client(name):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@app.route("/clients")
def list_clients():
    conn = get_db()
    rows = conn.execute("SELECT name FROM clients ORDER BY name").fetchall()
    conn.close()
    return jsonify({"clients": [r["name"] for r in rows]})


@app.route("/progress", methods=["POST"])
def save_progress():
    data = request.get_json()
    name = data.get("client_name")
    adherence = data.get("adherence")
    if not name or adherence is None:
        return jsonify({"error": "client_name and adherence required"}), 400
    week = datetime.now().strftime("Week %U - %Y")
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO progress (client_name,week,adherence) VALUES (?,?,?)",
            (name, week, adherence),
        )
        conn.commit()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    return jsonify({"message": "Progress saved"})


# --- carried forward from v1.1.2 ---
@app.route("/export_clients")
def export_clients():
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT name,age,weight,program,calories FROM clients ORDER BY name"
        ).fetchall()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    headers = ["name", "age", "weight", "program", "calories"]
    return jsonify(
        {"headers": headers, "rows": [[r[h] for h in headers] for r in rows]}
    )


@app.route("/site_metrics")
def site_metrics():
    return jsonify({"capacity": 150, "area_sqft": 10000, "break_even_members": 250})


@app.route("/progress/<client_name>")
def get_progress(client_name):
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id",
            (client_name,),
        ).fetchall()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    if not rows:
        return jsonify({"error": "No progress data found"}), 404
    return jsonify({"client": client_name, "progress": [dict(r) for r in rows]})


@app.route("/workout", methods=["POST"])
def log_workout():
    data = request.get_json()
    client_name = data.get("client_name")
    wtype = data.get("workout_type")
    if not client_name or not wtype:
        return jsonify({"error": "client_name and workout_type required"}), 400
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO workouts (client_name,date,workout_type,duration_min,notes) VALUES (?,?,?,?,?)",
            (
                client_name,
                data.get("date", ""),
                wtype,
                data.get("duration_min", 60),
                data.get("notes", ""),
            ),
        )
        conn.commit()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    return jsonify({"message": "Workout logged"})


@app.route("/metrics", methods=["POST"])
def log_metrics():
    data = request.get_json()
    client_name = data.get("client_name")
    if not client_name:
        return jsonify({"error": "client_name required"}), 400
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO metrics (client_name,date,weight,waist,bodyfat) VALUES (?,?,?,?,?)",
            (
                client_name,
                data.get("date", ""),
                data.get("weight", 0),
                data.get("waist", 0),
                data.get("bodyfat", 0),
            ),
        )
        conn.commit()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    return jsonify({"message": "Metrics logged"})


@app.route("/workouts/<client_name>")
def get_workouts(client_name):
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT date,workout_type,duration_min,notes FROM workouts WHERE client_name=? ORDER BY date DESC",
            (client_name,),
        ).fetchall()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    return jsonify({"client": client_name, "workouts": [dict(r) for r in rows]})


@app.route("/metrics/<client_name>")
def get_metrics(client_name):
    try:
        conn = get_db()
        rows = conn.execute(
            "SELECT date,weight,waist,bodyfat FROM metrics WHERE client_name=? ORDER BY date",
            (client_name,),
        ).fetchall()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    return jsonify({"client": client_name, "metrics": [dict(r) for r in rows]})


@app.route("/bmi/<client_name>")
def get_bmi(client_name):
    try:
        conn = get_db()
        row = conn.execute(
            "SELECT weight, height FROM clients WHERE name=?", (client_name,)
        ).fetchone()
    except Exception as e:
        return db_error(e)
    finally:
        conn.close()
    if not row or not row["height"]:
        return jsonify({"error": "Client or height not found"}), 404
    bmi = round(row["weight"] / ((row["height"] / 100) ** 2), 1)
    return jsonify({"client": client_name, "bmi": bmi})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
