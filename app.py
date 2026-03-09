from flask import Flask, jsonify, request

app = Flask(__name__)

# Data extracted from Aceestver-1_0.py
PROGRAMS = {
    "Fat Loss (FL)": {
        "calorie_factor": 22,
        "workout": "Mon: 5x5 Back Squat + AMRAP, Tue: EMOM 20min Assault Bike, Wed: Bench Press + 21-15-9, Thu: 10RFT Deadlifts/Box Jumps, Fri: 30min Active Recovery",
        "diet": "Breakfast: 3 Egg Whites + Oats Idli, Lunch: Grilled Chicken + Brown Rice, Dinner: Fish Curry + Millet Roti",
    },
    "Muscle Gain (MG)": {
        "calorie_factor": 35,
        "workout": "Mon: Squat 5x5, Tue: Bench 5x5, Wed: Deadlift 4x6, Thu: Front Squat 4x8, Fri: Incline Press 4x10, Sat: Barbell Rows 4x10",
        "diet": "Breakfast: 4 Eggs + PB Oats, Lunch: Chicken Biryani 250g, Dinner: Mutton Curry + Jeera Rice",
    },
    "Beginner (BG)": {
        "calorie_factor": 26,
        "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups. Focus: Technique Mastery and Form",
        "diet": "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati. Protein: 120g/day",
    },
}

clients_store = []


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
        return jsonify({"error": "Program not found"}), 404
    return jsonify(PROGRAMS[name])


@app.route("/calculate_calories", methods=["POST"])
def calculate_calories():
    data = request.get_json()
    weight = data.get("weight")
    program = data.get("program")
    name = data.get("name", "")
    age = data.get("age", 0)
    if not weight or not program:
        return jsonify({"error": "weight and program required"}), 400
    if program not in PROGRAMS:
        return jsonify({"error": "Invalid program"}), 404
    if not isinstance(weight, (int, float)) or weight <= 0:
        return jsonify({"error": "Invalid weight"}), 400
    calories = int(weight * PROGRAMS[program]["calorie_factor"])
    return jsonify(
        {
            "name": name,
            "age": age,
            "weight": weight,
            "program": program,
            "calories": calories,
        }
    )


@app.route("/site_metrics")
def site_metrics():
    return jsonify({"capacity": 150, "area_sqft": 10000, "break_even_members": 250})


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
    calories = int(weight * PROGRAMS[program]["calorie_factor"])
    client = {
        "name": name,
        "age": data.get("age", 0),
        "weight": weight,
        "program": program,
        "adherence": data.get("adherence", 0),
        "notes": data.get("notes", ""),
        "calories": calories,
    }
    clients_store.append(client)
    return jsonify({"message": "Client saved", "client": client})


@app.route("/clients")
def list_clients():
    return jsonify({"clients": clients_store, "count": len(clients_store)})


@app.route("/export_clients")
def export_clients():
    # Mirrors export_csv() from Aceestver1_1_2.py — returns CSV-ready data
    headers = ["name", "age", "weight", "program", "adherence", "notes"]
    return jsonify(
        {"headers": headers, "rows": [[c[h] for h in headers] for c in clients_store]}
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
