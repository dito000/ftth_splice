
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///fiber.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Closure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
