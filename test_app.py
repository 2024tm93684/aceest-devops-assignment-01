import pytest, json
import app as app_module
from app import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "DB", str(tmp_path / "test.db"))
    app_module.init_db()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_index(client):
    assert client.get("/").status_code == 200


def test_health(client):
    assert json.loads(client.get("/health").data)["status"] == "healthy"


def test_programs_list(client):
    data = json.loads(client.get("/programs").data)
    assert len(data["programs"]) == 4
    assert "Fat Loss (FL) – 3 day" in data["programs"]


def test_get_valid_program(client):
    data = json.loads(client.get("/program/Beginner (BG)").data)
    assert "calorie_factor" in data and "desc" in data


def test_get_invalid_program(client):
    assert client.get("/program/Unknown").status_code == 404


def test_calc_fl(client):
    r = client.post(
        "/calculate_calories",
        data=json.dumps({"weight": 70, "program": "Fat Loss (FL) – 3 day"}),
        content_type="application/json",
    )
    assert json.loads(r.data)["calories"] == 1540  # 70×22


def test_calc_mg(client):
    r = client.post(
        "/calculate_calories",
        data=json.dumps({"weight": 80, "program": "Muscle Gain (MG) – PPL"}),
        content_type="application/json",
    )
    assert json.loads(r.data)["calories"] == 2800  # 80×35


def test_calc_missing(client):
    assert (
        client.post(
            "/calculate_calories",
            data=json.dumps({"weight": 70}),
            content_type="application/json",
        ).status_code
        == 400
    )


def test_calc_invalid_weight(client):
    r = client.post(
        "/calculate_calories",
        data=json.dumps({"weight": -5, "program": "Beginner (BG)"}),
        content_type="application/json",
    )
    assert r.status_code == 400


def test_calc_invalid_program(client):
    r = client.post(
        "/calculate_calories",
        data=json.dumps({"weight": 70, "program": "Bad"}),
        content_type="application/json",
    )
    assert r.status_code == 404


def test_save_and_get_client(client):
    client.post(
        "/client",
        data=json.dumps(
            {
                "name": "Arjun",
                "program": "Fat Loss (FL) – 3 day",
                "weight": 75,
                "age": 30,
            }
        ),
        content_type="application/json",
    )
    data = json.loads(client.get("/client/Arjun").data)
    assert data["name"] == "Arjun" and data["calories"] == 1650  # 75×22


def test_get_unknown_client(client):
    assert client.get("/client/Nobody").status_code == 404


def test_list_clients(client):
    client.post(
        "/client",
        data=json.dumps({"name": "Raj", "program": "Beginner (BG)", "weight": 65}),
        content_type="application/json",
    )
    data = json.loads(client.get("/clients").data)
    assert "Raj" in data["clients"]


def test_save_progress(client):
    r = client.post(
        "/progress",
        data=json.dumps({"client_name": "Arjun", "adherence": 85}),
        content_type="application/json",
    )
    assert r.status_code == 200


def test_save_progress_missing(client):
    r = client.post(
        "/progress",
        data=json.dumps({"client_name": "Arjun"}),
        content_type="application/json",
    )
    assert r.status_code == 400


def test_save_client_invalid_program(client):
    r = client.post(
        "/client",
        data=json.dumps({"name": "Raj", "program": "Bad"}),
        content_type="application/json",
    )
    assert r.status_code == 404


def test_export_clients(client):
    client.post(
        "/client",
        data=json.dumps({"name": "Raj", "program": "Beginner (BG)", "weight": 65}),
        content_type="application/json",
    )
    data = json.loads(client.get("/export_clients").data)
    assert "headers" in data and "rows" in data
    assert len(data["rows"]) == 1


def test_site_metrics(client):
    data = json.loads(client.get("/site_metrics").data)
    assert "capacity" in data and data["capacity"] == 150


def test_get_progress(client):
    client.post(
        "/progress",
        data=json.dumps({"client_name": "Raj", "adherence": 80}),
        content_type="application/json",
    )
    data = json.loads(client.get("/progress/Raj").data)
    assert len(data["progress"]) == 1 and data["progress"][0]["adherence"] == 80


def test_get_progress_no_data(client):
    assert client.get("/progress/Nobody").status_code == 404


def test_programs_now_4(client):
    data = json.loads(client.get("/programs").data)
    assert len(data["programs"]) == 4
    assert "Fat Loss (FL) – 5 day" in data["programs"]


def test_calc_fl5day(client):
    r = client.post(
        "/calculate_calories",
        data=json.dumps({"weight": 70, "program": "Fat Loss (FL) – 5 day"}),
        content_type="application/json",
    )
    assert json.loads(r.data)["calories"] == 1680  # 70×24


def test_log_workout(client):
    r = client.post(
        "/workout",
        data=json.dumps(
            {"client_name": "Raj", "workout_type": "Strength", "duration_min": 60}
        ),
        content_type="application/json",
    )
    assert r.status_code == 200


def test_log_workout_missing(client):
    assert (
        client.post(
            "/workout",
            data=json.dumps({"client_name": "Raj"}),
            content_type="application/json",
        ).status_code
        == 400
    )


def test_log_metrics(client):
    r = client.post(
        "/metrics",
        data=json.dumps(
            {"client_name": "Raj", "weight": 75, "waist": 82, "bodyfat": 18}
        ),
        content_type="application/json",
    )
    assert r.status_code == 200


def test_get_workouts(client):
    client.post(
        "/workout",
        data=json.dumps(
            {"client_name": "Raj", "workout_type": "Strength", "duration_min": 60}
        ),
        content_type="application/json",
    )
    r = client.get("/workouts/Raj")
    assert r.status_code == 200 and len(json.loads(r.data)["workouts"]) == 1


def test_get_metrics_history(client):
    client.post(
        "/metrics",
        data=json.dumps(
            {"client_name": "Raj", "weight": 75, "waist": 82, "bodyfat": 18}
        ),
        content_type="application/json",
    )
    r = client.get("/metrics/Raj")
    assert r.status_code == 200 and len(json.loads(r.data)["metrics"]) == 1


def test_bmi(client):
    client.post(
        "/client",
        data=json.dumps(
            {"name": "Raj", "program": "Beginner (BG)", "weight": 70, "height": 175}
        ),
        content_type="application/json",
    )
    r = client.get("/bmi/Raj")
    assert r.status_code == 200 and "bmi" in json.loads(r.data)


def test_status(client):
    r = client.get("/status")
    assert r.status_code == 200
    assert "total_clients" in json.loads(r.data)


def test_login_valid(client):
    r = client.post(
        "/login",
        data=json.dumps({"username": "admin", "password": "admin"}),
        content_type="application/json",
    )
    assert r.status_code == 200 and json.loads(r.data)["role"] == "Admin"


def test_login_invalid(client):
    r = client.post(
        "/login",
        data=json.dumps({"username": "hacker", "password": "wrong"}),
        content_type="application/json",
    )
    assert r.status_code == 401


def test_list_users(client):
    data = json.loads(client.get("/users").data)
    assert len(data["users"]) >= 1


def test_generate_program(client):
    client.post(
        "/client",
        data=json.dumps({"name": "Priya", "program": "Beginner (BG)", "weight": 55}),
        content_type="application/json",
    )
    r = client.get("/generate_program/Priya")
    assert r.status_code == 200 and "generated_program" in json.loads(r.data)


def test_generate_pdf(client):
    client.post(
        "/client",
        data=json.dumps({"name": "Priya", "program": "Beginner (BG)", "weight": 55}),
        content_type="application/json",
    )
    r = client.get("/generate_pdf/Priya")
    assert r.status_code == 200 and "PDF generated" in json.loads(r.data)["message"]


def test_membership(client):
    client.post(
        "/client",
        data=json.dumps({"name": "Priya", "program": "Beginner (BG)", "weight": 55}),
        content_type="application/json",
    )
    assert client.get("/membership/Priya").status_code == 200


def test_membership_not_found(client):
    assert client.get("/membership/Ghost").status_code == 404
