from flask import Flask, request, jsonify, render_template
import sqlite3, time, uuid, os

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "pins.db")   # the file where pins are saved
LIFETIME = 24 * 60 * 60                                   # a pin lasts 24 hours
HAZARDS = {"flood", "surge", "landslide", "earthquake", "volcano",
           "sinkhole", "wildfire", "erosion", "downed_Lightpole"}

def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

# create the pins table the first time the app starts
with get_db() as con:
    con.execute("""CREATE TABLE IF NOT EXISTS pins (
        id TEXT PRIMARY KEY, country TEXT, type TEXT, note TEXT,
        lat REAL, lng REAL, created REAL, expires REAL)""")

@app.route("/")
def home():
    return render_template("index.html")

@app.get("/api/pins")                       # "give me the active pins"
def list_pins():
    country = request.args.get("country")
    with get_db() as con:
        rows = con.execute("SELECT * FROM pins WHERE country = ? AND expires > ?",
                           (country, time.time())).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/pins")                      # "save this new pin"
def add_pin():
    d = request.get_json()
    if d.get("type") not in HAZARDS:
        return jsonify({"error": "unknown hazard type"}), 400
    now = time.time()
    pin_id = str(uuid.uuid4())
    with get_db() as con:
        con.execute("INSERT INTO pins VALUES (?,?,?,?,?,?,?,?)",
                    (pin_id, d["country"], d["type"], d.get("note", "")[:100],
                     float(d["lat"]), float(d["lng"]), now, now + LIFETIME))
    return jsonify({"id": pin_id}), 201

@app.delete("/api/pins/<pin_id>")           # "remove this pin"
def delete_pin(pin_id):
    with get_db() as con:
        con.execute("DELETE FROM pins WHERE id = ?", (pin_id,))
    return jsonify({"deleted": pin_id})

if __name__ == "__main__":
    app.run(debug=True)