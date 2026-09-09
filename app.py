from flask import Flask, render_template, request, redirect
import psycopg
from psycopg.rows import dict_row
import os

app = Flask(__name__)


def get_connection():
    return psycopg.connect(
        os.environ["DATABASE_URL"],
        row_factory=dict_row
    )


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catches (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            date TEXT,
            time TEXT,
            location TEXT,
            weather TEXT,
            species TEXT,
            weight REAL,
            length REAL,
            bait TEXT,
            notes TEXT
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/statistics")
def statistics():
    connection = get_connection()
    cursor = connection.cursor()

    # Total number of catches
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM catches
    """)
    total_catches = cursor.fetchone()["total"]

    # Number of different fish species
    cursor.execute("""
        SELECT COUNT(DISTINCT species) AS species_count
        FROM catches
        WHERE species IS NOT NULL
          AND species <> ''
    """)
    species_count = cursor.fetchone()["species_count"]

    # Average fish weight
    cursor.execute("""
        SELECT AVG(weight) AS average_weight
        FROM catches
        WHERE weight IS NOT NULL
    """)
    average_weight = cursor.fetchone()["average_weight"]

    # Heaviest fish
    cursor.execute("""
        SELECT species, weight
        FROM catches
        WHERE weight IS NOT NULL
        ORDER BY weight DESC
        LIMIT 1
    """)
    biggest_fish = cursor.fetchone()

    # Number of catches for each species
    cursor.execute("""
        SELECT species, COUNT(*) AS count
        FROM catches
        WHERE species IS NOT NULL
          AND species <> ''
        GROUP BY species
        ORDER BY count DESC, species ASC
    """)
    species_stats = cursor.fetchall()

    # Number of catches at each location
    cursor.execute("""
        SELECT location, COUNT(*) AS count
        FROM catches
        WHERE location IS NOT NULL
          AND location <> ''
        GROUP BY location
        ORDER BY count DESC, location ASC
    """)
    location_stats = cursor.fetchall()

    # Number of catches in each weather condition
    cursor.execute("""
        SELECT weather, COUNT(*) AS count
        FROM catches
        WHERE weather IS NOT NULL
          AND weather <> ''
        GROUP BY weather
        ORDER BY count DESC, weather ASC
    """)
    weather_stats = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "statistics.html",
        total_catches=total_catches,
        species_count=species_count,
        average_weight=average_weight,
        biggest_fish=biggest_fish,
        species_stats=species_stats,
        location_stats=location_stats,
        weather_stats=weather_stats
    )


@app.route("/log", methods=["GET", "POST"])
def log_catch():

    if request.method == "POST":

        date = request.form["date"]
        time = request.form["time"]
        location = request.form["location"]
        weather = request.form["weather"]
        species = request.form["species"]
        weight = request.form["weight"] or None
        length = request.form["length"] or None
        bait = request.form["bait"]
        notes = request.form["notes"]

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO catches
            (date, time, location, weather, species, weight, length, bait, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (date, time, location, weather, species, weight, length, bait, notes))

        connection.commit()
        cursor.close()
        connection.close()

        return """
        <h1>Your catch has been saved</h1>

        <a href="/log">
            <button>Log another fish</button>
        </a>

        <a href="/statistics">
            <button>View Statistics</button>
        </a>

        <a href="/">
            <button>Back to Home</button>
        </a>
        """

    return render_template("log.html")


@app.route("/catches")
def catches():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM catches")
    catches = cursor.fetchall()

    connection.close()

    return render_template("catches.html", catches=catches)


@app.route("/catches/delete/<int:id>")
def delete_catch(id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM catches WHERE id = %s", (id,))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect("/catches")


@app.route("/catches/edit/<int:id>", methods=["GET", "POST"])
def edit_catch(id):

    connection = get_connection()
    cursor = connection.cursor()

    if request.method == "POST":

        date = request.form["date"]
        time = request.form["time"]
        location = request.form["location"]
        weather = request.form["weather"]
        species = request.form["species"]
        weight = request.form["weight"] or None
        length = request.form["length"] or None
        bait = request.form["bait"]
        notes = request.form["notes"]

        cursor.execute("""
            UPDATE catches
            SET date = %s, time = %s, location = %s, weather = %s,
                species = %s, weight = %s, length = %s, bait = %s, notes = %s
            WHERE id = %s
        """, (date, time, location, weather, species, weight, length, bait, notes, id))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect("/catches")

    cursor.execute("SELECT * FROM catches WHERE id = %s", (id,))
    catch = cursor.fetchone()

    connection.close()

    return render_template("edit.html", catch=catch)


init_db()


if __name__ == "__main__":
    app.run(debug=True)
