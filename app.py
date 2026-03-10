import sqlite3
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)
DB = "aceest.db"

PROGRAMS = {
    "Fat Loss (FL)": {
        "calorie_factor": 22,
        "workout": "Back Squat, Cardio, Bench, Deadlift, Recovery",
        "diet": "Egg Whites, Chicken, Fish Curry",
    },
    "Muscle Gain (MG)": {
        "calorie_factor": 35,
        "workout": "Squat, Bench, Deadlift, Press, Rows",
        "diet": "Eggs, Biryani, Mutton Curry",
    },
    "Beginner (BG)": {
        "calorie_factor": 26,
        "workout": "Air Squats, Ring Rows, Push-ups",
        "diet": "Balanced Tamil Meals",
    },
}


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # Schema from Aceestver2_0_1.py init_db()
    conn = get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE,
        age INTEGER, weight REAL, program TEXT, calories INTEGER)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_name TEXT,
        week TEXT, adherence INTEGER)"""
    )
    conn.commit()
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
    calories = int(weight * PROGRAMS[program]["calorie_factor"])
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO clients (name,age,weight,program,calories) VALUES (?,?,?,?,?)",
        (name, age, weight, program, calories),
    )
    conn.commit()
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
    conn = get_db()
    conn.execute(
        "INSERT INTO progress (client_name,week,adherence) VALUES (?,?,?)",
        (name, week, adherence),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Progress saved"})


# --- carried forward from v1.1.2 ---
@app.route("/export_clients")
def export_clients():
    conn = get_db()
    rows = conn.execute(
        "SELECT name,age,weight,program,calories FROM clients ORDER BY name"
    ).fetchall()
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
    conn = get_db()
    rows = conn.execute(
        "SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id",
        (client_name,),
    ).fetchall()
    conn.close()
    if not rows:
        return jsonify({"error": "No progress data found"}), 404
    return jsonify({"client": client_name, "progress": [dict(r) for r in rows]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
