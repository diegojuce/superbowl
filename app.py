from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    # Crear tabla de equipos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            yardas INTEGER DEFAULT 0,
            puntos INTEGER DEFAULT 0
        )
    """)

    # Crear tabla de historial
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER,
            yardas INTEGER DEFAULT 0,
            puntos INTEGER DEFAULT 0,
            fecha TEXT,
            FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE
        )
    """)

    # Insertar equipos iniciales si no existen
    cursor.execute("SELECT COUNT(*) FROM equipos")
    if cursor.fetchone()[0] == 0:
        equipos = [("Equipo 1",), ("Equipo 2",), ("Equipo 3",), ("Equipo 4",), ("Equipo 5",)]
        cursor.executemany("INSERT INTO equipos (nombre) VALUES (?)", equipos)
    conn.commit()
    conn.close()

init_db()

# Ruta principal
@app.route("/")
def index():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipos")
    equipos = cursor.fetchall()
    conn.close()
    return render_template("index.html", equipos=equipos)

# Ruta para sumar yardas
@app.route("/sumar", methods=["POST"])
def sumar_yardas():
    equipo_id = int(request.form["equipo_id"])
    yardas = int(request.form["yardas"])
    
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT yardas FROM equipos WHERE id = ?", (equipo_id,))
    actual_yardas = cursor.fetchone()[0]
    nueva_yarda = actual_yardas + yardas

    if nueva_yarda >= 100:
        puntos_extra = nueva_yarda // 100
        sobrante_yarda = nueva_yarda % 100
        cursor.execute("UPDATE equipos SET yardas = ?, puntos = puntos + ? WHERE id = ?",
                       (sobrante_yarda, puntos_extra * 7, equipo_id))
    else:
        cursor.execute("UPDATE equipos SET yardas = ? WHERE id = ?", (nueva_yarda, equipo_id))

    # Registrar en historial
    cursor.execute("INSERT INTO historial (equipo_id, yardas, puntos, fecha) VALUES (?, ?, 0, ?)",
                   (equipo_id, yardas, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# Ruta para editar el nombre del equipo
@app.route("/editar_nombre", methods=["POST"])
def editar_nombre():
    equipo_id = int(request.form["equipo_id"])
    nuevo_nombre = request.form["nuevo_nombre"]
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE equipos SET nombre = ? WHERE id = ?", (nuevo_nombre, equipo_id))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# Ruta para agregar un nuevo equipo
@app.route("/agregar_equipo", methods=["POST"])
def agregar_equipo():
    nombre_equipo = request.form.get("nombre_equipo")
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO equipos (nombre) VALUES (?)", (nombre_equipo,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# Ruta para eliminar un equipo
@app.route("/eliminar_equipo/<int:equipo_id>", methods=["POST"])
def eliminar_equipo(equipo_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM equipos WHERE id = ?", (equipo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# Ruta para restar yardas
@app.route("/restar_yardas", methods=["POST"])
def restar_yardas():
    equipo_id = int(request.form["equipo_id"])
    yardas = int(request.form["yardas"])

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT yardas FROM equipos WHERE id = ?", (equipo_id,))
    actual_yardas = cursor.fetchone()[0]
    nueva_yarda = max(actual_yardas - yardas, 0)
    cursor.execute("UPDATE equipos SET yardas = ? WHERE id = ?", (nueva_yarda, equipo_id))

    # Registrar en historial
    cursor.execute("INSERT INTO historial (equipo_id, yardas, puntos, fecha) VALUES (?, ?, 0, ?)",
                   (equipo_id, -yardas, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    return redirect(url_for("historial"))

# Ruta para restar puntos
@app.route("/restar_puntos", methods=["POST"])
def restar_puntos():
    equipo_id = int(request.form["equipo_id"])
    puntos = int(request.form["puntos"])

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT puntos FROM equipos WHERE id = ?", (equipo_id,))
    actual_puntos = cursor.fetchone()[0]
    nueva_puntos = max(actual_puntos - puntos, 0)
    cursor.execute("UPDATE equipos SET puntos = ? WHERE id = ?", (nueva_puntos, equipo_id))

    # Registrar en historial
    cursor.execute("INSERT INTO historial (equipo_id, yardas, puntos, fecha) VALUES (?, 0, ?, ?)",
                   (equipo_id, -puntos, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    return redirect(url_for("historial"))

# Ruta para ver el historial
@app.route("/historial")
def historial():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT historial.fecha, equipos.nombre, historial.yardas, historial.puntos
        FROM historial
        INNER JOIN equipos ON historial.equipo_id = equipos.id
        ORDER BY historial.fecha DESC
    """)
    registros = cursor.fetchall()
    cursor.execute("SELECT id, nombre FROM equipos")
    equipos = cursor.fetchall()
    conn.close()
    return render_template("historial.html", registros=registros, equipos=equipos)

# Iniciar el servidor Flask
if __name__ == "__main__":
    app.run(debug=True)
