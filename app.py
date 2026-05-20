
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

def build_topology_edges():

    closures = Closure.query.all()

    odfs = load_odfs()

    edges = []

    #
    # ODF → feeder cable
    #

    for odf in odfs:

        for port in (
            odf.get("ports") or []
        ):

            feeder = port.get(
                "feederCable"
            )

            if feeder:

                edges.append({

                    "from":
                        f"ODF:{odf.get('odfName')}:{port.get('pon','')}",

                    "to":
                        feeder,

                    "type":"odf-feeder"
                })

    #
    # Closure topology
    #

    for closure in closures:

        data = closure.data or {}

        closure_name = data.get(
            "closureName",
            "UNKNOWN"
        )

        closure_node = (
            f"Closure:{closure_name}"
        )

        in_cable = (
            data.get(
                "inCable"
            ) or {}
        ).get(
            "cableName"
        )

        if in_cable:

            edges.append({

                "from":
                    in_cable,

                "to":
                    closure_node,

                "type":"incoming-cable"
            })

        #
        # THROUGH continuity
        #

        for cable in (
            data.get(
                "throughCables"
            ) or []
        ):

            cable_name = cable.get(
                "cableName"
            )

            if not cable_name:
                continue

            edges.append({

                "from":
                    closure_node,

                "to":
                    cable_name,

                "type":"through-cable"
            })

            if cable.get(
                "toClosure"
            ):

                edges.append({

                    "from":
                        cable_name,

                    "to":

                        f"Closure:{cable.get('toClosure')}",

                    "type":"through-next-closure"
                })

        #
        # OUT branch continuity
        #

        for cable in (
            data.get(
                "outCables"
            ) or []
        ):

            cable_name = cable.get(
                "cableName"
            )

            if not cable_name:
                continue

            edges.append({

                "from":
                    closure_node,

                "to":
                    cable_name,

                "type":"branch-cable"
            })

            if cable.get(
                "toClosure"
            ):

                edges.append({

                    "from":
                        cable_name,

                    "to":

                        f"Closure:{cable.get('toClosure')}",

                    "type":"branch-next-closure"
                })

        #
        # Splitters
        #

        for splitter in (
            data.get(
                "splitters"
            ) or []
        ):

            splitter_id = splitter.get(
                "id"
            )

            if not splitter_id:
                continue

            splitter_node = (
                f"Splitter:{splitter_id}"
            )

            #
            # closure → splitter
            #

            edges.append({

                "from":
                    closure_node,

                "to":
                    splitter_node,

                "type":"closure-splitter"
            })

            #
            # splitter → input strand
            #

            edges.append({

                "from":
                    splitter_node,

                "to":

                    f"{closure_name}"
                    f":B{splitter.get('buffer')}"
                    f":S{splitter.get('strand')}",

                "type":"splitter-input"
            })

            #
            # splitter → ports
            #

            for p in range(1,9):

                edges.append({

                    "from":
                        splitter_node,

                    "to":
                        f"{splitter_node}:P{p}",

                    "type":"splitter-port"
                })

        #
        # Strand mappings
        #

        for mapping in (
            data.get(
                "mappings"
            ) or []
        ):

            mapping_type = mapping.get(
                "mappingType"
            )

            #
            # strand splice
            #

            if mapping_type == "strand":

                source_node = (

                    f"{closure_name}"
                    f":B{mapping.get('buffer')}"
                    f":S{mapping.get('strand')}"
                )

                target_node = (

                    f"{mapping.get('outCable')}"
                    f":B{mapping.get('outBuffer')}"
                    f":S{mapping.get('outStrand')}"
                )

                edges.append({

                    "from":
                        closure_node,

                    "to":
                        source_node,

                    "type":"closure-strand"
                })

                edges.append({

                    "from":
                        source_node,

                    "to":
                        target_node,

                    "type":"splice"
                })

            #
            # splitter outputs
            #

            if mapping_type == "splitter-output":

                edges.append({

                    "from":

                        f"Splitter:"
                        f"{mapping.get('splitterId')}"
                        f":P{mapping.get('port')}",

                    "to":

                        f"{mapping.get('outCable')}"
                        f":B{mapping.get('outBuffer')}"
                        f":S{mapping.get('outStrand')}",

                    "type":"splitter-output"
                })

    return edges


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

        "totalPorts":48,

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

    closures = Closure.query.all()

    cable_registry = []

    for closure in closures:

        closure_data = closure.data or {}


        for cable in (
            closure_data.get(
                "cableRegistry"
            ) or []
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

@app.route("/odf/<odf_id>/save", methods=["POST"])
def save_odf_route(odf_id):

    odfs = load_odfs()

    payload = request.json

    for i, odf in enumerate(odfs):

        if odf["id"] == odf_id:

            odfs[i] = payload

            break

    save_odfs(odfs)

    return {"success":True}

@app.route("/api/topology")
def topology_api():

    return jsonify(
        build_topology_edges()
    )

@app.route("/api/trace/<path:start_node>")
def trace_topology(start_node):

    edges = build_topology_edges()

    adjacency = {}

    for edge in edges:

        adjacency.setdefault(
            edge["from"],
            []
        ).append(
            edge["to"]
        )

    visited = set()

    result = []

    def walk(node):

        if node in visited:
            return

        visited.add(node)

        result.append(node)

        for nxt in adjacency.get(
            node,
            []
        ):

            walk(nxt)

    walk(start_node)

    return jsonify(result)

@app.route(
    "/api/reverse-trace/<path:start_node>"
)
def reverse_trace_topology(start_node):

    edges = build_topology_edges()

    reverse_adjacency = {}

    for edge in edges:

        reverse_adjacency.setdefault(
            edge["to"],
            []
        ).append(
            edge["from"]
        )

    visited = set()

    result = []

    def walk(node):

        if node in visited:
            return

        visited.add(node)

        result.append(node)

        for prev in reverse_adjacency.get(
            node,
            []
        ):

            walk(prev)

    walk(start_node)

    return jsonify(result)

@app.route("/api/topology/validate")
def validate_topology():

    closures = Closure.query.all()

    issues = []

    used_targets = set()

    splitter_ports = set()

    closure_names = set()

    #
    # collect closure names
    #

    for closure in closures:

        data = closure.data or {}

        closure_names.add(
            data.get(
                "closureName"
            )
        )

    #
    # validate topology
    #

    for closure in closures:

        data = closure.data or {}

        closure_name = data.get(
            "closureName",
            "UNKNOWN"
        )

        #
        # validate out cables
        #

        for cable in (
            data.get(
                "outCables"
            ) or []
        ):

            destination = cable.get(
                "toClosure"
            )

            if (
                destination and
                destination not in closure_names
            ):

                issues.append({

                    "type":
                        "missing-closure",

                    "message":

                        f"{closure_name} "
                        f"references missing "
                        f"closure "
                        f"{destination}"
                })

        #
        # validate through cables
        #

        for cable in (
            data.get(
                "throughCables"
            ) or []
        ):

            destination = cable.get(
                "toClosure"
            )

            if (
                destination and
                destination not in closure_names
            ):

                issues.append({

                    "type":
                        "missing-closure",

                    "message":

                        f"{closure_name} "
                        f"references missing "
                        f"closure "
                        f"{destination}"
                })

        #
        # validate mappings
        #

        for mapping in (
            data.get(
                "mappings"
            ) or []
        ):

            mapping_type = mapping.get(
                "mappingType"
            )

            #
            # strand splice validation
            #

            if mapping_type == "strand":

                target = (

                    f"{mapping.get('outCable')}"
                    f":B{mapping.get('outBuffer')}"
                    f":S{mapping.get('outStrand')}"
                )

                if target in used_targets:

                    issues.append({

                        "type":
                            "duplicate-strand",

                        "message":

                            f"Duplicate strand "
                            f"usage detected: "
                            f"{target}"
                    })

                else:

                    used_targets.add(
                        target
                    )

            #
            # splitter output validation
            #

            if mapping_type == "splitter-output":

                splitter_key = (

                    f"{mapping.get('splitterId')}"
                    f":P{mapping.get('port')}"
                )

                if splitter_key in splitter_ports:

                    issues.append({

                        "type":
                            "duplicate-splitter-port",

                        "message":

                            f"Splitter port "
                            f"used multiple times: "
                            f"{splitter_key}"
                    })

                else:

                    splitter_ports.add(
                        splitter_key
                    )

    return jsonify(issues)

@app.route("/api/search")
def search_topology():

    query = (
        request.args.get("q","")
        .strip()
        .lower()
    )

    results = []

    if not query:

        return jsonify(results)

    closures = Closure.query.all()

    odfs = load_odfs()

    #
    # search closures
    #

    for closure in closures:

        data = closure.data or {}

        closure_name = (
            data.get(
                "closureName",
                ""
            )
        )

        if query in closure_name.lower():

            results.append({

                "type":"closure",

                "name":closure_name,

                "id":closure.id
            })

        #
        # in cable
        #

        in_cable = (
            data.get(
                "inCable"
            ) or {}
        )

        cable_name = (
            in_cable.get(
                "cableName",
                ""
            )
        )

        if (
            cable_name and
            query in cable_name.lower()
        ):

            results.append({

                "type":"in-cable",

                "name":cable_name,

                "closure":closure_name
            })

        #
        # out cables
        #

        for cable in (
            data.get(
                "outCables"
            ) or []
        ):

            cable_name = (
                cable.get(
                    "cableName",
                    ""
                )
            )

            if (
                cable_name and
                query in cable_name.lower()
            ):

                results.append({

                    "type":"out-cable",

                    "name":cable_name,

                    "closure":closure_name,

                    "destination":
                        cable.get(
                            "toClosure"
                        )
                })

        #
        # through cables
        #

        for cable in (
            data.get(
                "throughCables"
            ) or []
        ):

            cable_name = (
                cable.get(
                    "cableName",
                    ""
                )
            )

            if (
                cable_name and
                query in cable_name.lower()
            ):

                results.append({

                    "type":"through-cable",

                    "name":cable_name,

                    "closure":closure_name,

                    "destination":
                        cable.get(
                            "toClosure"
                        )
                })

        #
        # splitters
        #

        for splitter in (
            data.get(
                "splitters"
            ) or []
        ):

            splitter_id = (
                splitter.get(
                    "id",
                    ""
                )
            )

            if query in splitter_id.lower():

                results.append({

                    "type":"splitter",

                    "id":splitter_id,

                    "closure":closure_name,

                    "buffer":
                        splitter.get(
                            "buffer"
                        ),

                    "strand":
                        splitter.get(
                            "strand"
                        )
                })

    #
    # ODF search
    #

    for odf in odfs:

        odf_name = (
            odf.get(
                "odfName",
                ""
            )
        )

        if query in odf_name.lower():

            results.append({

                "type":"odf",

                "name":odf_name
            })

        for port in (
            odf.get(
                "ports"
            ) or []
        ):

            feeder = (
                port.get(
                    "feederCable",
                    ""
                )
            )

            if (
                feeder and
                query in feeder.lower()
            ):

                results.append({

                    "type":"odf-port",

                    "odf":odf_name,

                    "pon":
                        port.get(
                            "pon"
                        ),

                    "feederCable":
                        feeder
                })

    return jsonify(results)

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
