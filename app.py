
from flask import Flask, render_template, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json
import uuid

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///fiber.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

ODF_FILE = "odfs.json"

class Closure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def load_odfs():

    if not os.path.exists(ODF_FILE):

        return []

    with open(ODF_FILE, "r") as f:

        return json.load(f)


def save_odfs(data):

    with open(ODF_FILE, "w") as f:

        json.dump(data, f, indent=2)



@app.route("/")
def dashboard():
    closures = Closure.query.order_by(Closure.created_at.desc()).all()
    return render_template("dashboard.html", closures=closures)

@app.route("/closure/new")
def closure_new():
    return render_template("closure_edit.html", closure=None)

@app.route("/closure/<int:id>")
def closure_view(id):
    closure = Closure.query.get_or_404(id)
    return render_template("closure_view.html", closure=closure)

@app.route("/closure/<int:id>/edit")
def closure_edit(id):
    closure = Closure.query.get_or_404(id)
    return render_template("closure_edit.html", closure=closure)


@app.route("/odfs")
def odf_dashboard():

    odfs = load_odfs()

    return render_template(
        "odf_dashboard.html",
        odfs=odfs
    )

@app.route(
    "/odf/create",
    methods=["POST"]
)
def create_odf():

    odfs = load_odfs()

    odf_id = str(uuid.uuid4())

    odf = {

        "id":odf_id,

        "odfName":"New ODF",

        "location":"",

        "totalPorts":144,

        "ports":[]
    }

    odfs.append(odf)

    save_odfs(odfs)

    return redirect(
        f"/odf/{odf_id}/edit"
    )



@app.route("/odf/<odf_id>/edit")
def edit_odf(odf_id):

    odfs = load_odfs()

    odf = next(
        (
            o for o in odfs
            if o["id"] == odf_id
        ),
        None
    )

    if not odf:

        return "ODF not found", 404

    closures = load_closures()

    cable_registry = []

    for closure in closures:

        for cable in closure.get(
            "cableRegistry",
            []
        ):

            existing = next(
                (
                    c for c in cable_registry
                    if c["cableName"] ==
                    cable["cableName"]
                ),
                None
            )

            if not existing:

                cable_registry.append(
                    cable
                )

    return render_template(
        "odf_edit.html",
        odf=odf,
        cable_registry=cable_registry
    )

def save_odf_route(odf_id):

    odfs = load_odfs()

    payload = request.json

    for i, odf in enumerate(odfs):

        if odf["id"] == odf_id:

            odfs[i] = payload

            break

    save_odfs(odfs)

    return {"success":True}

@app.route("/api/closure/save", methods=["POST"])
def save_closure():
    payload = request.json
    cid = payload.get("id")

    if cid:
        closure = Closure.query.get(cid)
        closure.name = payload["closureName"]
        closure.data = payload
    else:
        closure = Closure(
            name=payload["closureName"],
            data=payload
        )
        db.session.add(closure)

    db.session.commit()

    return jsonify({
        "status":"ok",
        "id":closure.id
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=8001,
        debug=True
    )
