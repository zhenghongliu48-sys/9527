from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Marker
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    db_path = os.path.join(BASE_DIR, "markers.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ---------- Templates Routes ----------
    @app.route("/")
    def index():
        # 列表頁（可選擇顯示地圖）
        return render_template("list.html")

    @app.route("/create")
    def create_page():
        return render_template("create.html")

    @app.route("/marker/<int:marker_id>")
    def view_marker(marker_id):
        return render_template("view.html", marker_id=marker_id)

    @app.route("/marker/<int:marker_id>/edit")
    def edit_marker(marker_id):
        return render_template("edit.html", marker_id=marker_id)

    # ---------- RESTful API ----------
    @app.route("/api/markers", methods=["GET"])
    def api_list_markers():
        markers = Marker.query.order_by(Marker.id.desc()).all()
        return jsonify([m.to_dict() for m in markers]), 200

    @app.route("/api/markers/<int:marker_id>", methods=["GET"])
    def api_get_marker(marker_id):
        m = Marker.query.get_or_404(marker_id)
        return jsonify(m.to_dict()), 200

    @app.route("/api/markers", methods=["POST"])
    def api_create_marker():
        data = request.get_json() or request.form
        name = data.get("name")
        description = data.get("description")
        lat = data.get("lat")
        lng = data.get("lng")

        if not name or lat is None or lng is None:
            return jsonify({"error": "缺少必要欄位 (name, lat, lng)"}), 400
        try:
            lat = float(lat); lng = float(lng)
        except ValueError:
            return jsonify({"error": "lat 和 lng 必須為數字"}), 400

        m = Marker(name=name, description=description, lat=lat, lng=lng)
        db.session.add(m)
        db.session.commit()
        return jsonify(m.to_dict()), 201

    @app.route("/api/markers/<int:marker_id>", methods=["PUT"])
    def api_update_marker(marker_id):
        m = Marker.query.get_or_404(marker_id)
        data = request.get_json()
        if not data:
            return jsonify({"error": "需要 JSON body"}), 400

        name = data.get("name")
        description = data.get("description")
        lat = data.get("lat")
        lng = data.get("lng")

        if name is not None:
            m.name = name
        if description is not None:
            m.description = description
        if lat is not None:
            try:
                m.lat = float(lat)
            except ValueError:
                return jsonify({"error":"lat 必須為數字"}), 400
        if lng is not None:
            try:
                m.lng = float(lng)
            except ValueError:
                return jsonify({"error":"lng 必須為數字"}), 400

        db.session.commit()
        return jsonify(m.to_dict()), 200

    @app.route("/api/markers/<int:marker_id>", methods=["DELETE"])
    def api_delete_marker(marker_id):
        m = Marker.query.get_or_404(marker_id)
        db.session.delete(m)
        db.session.commit()
        return jsonify({"message":"刪除成功"}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
