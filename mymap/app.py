from flask import Flask, render_template, request, jsonify, redirect, url_for
from .models import db, Marker
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

        # --- 資料驗證 ---
        if not name or lat is None or lng is None:
            return jsonify({"error": "缺少必要欄位 (name, lat, lng)"}), 400
        try:
            lat = float(lat)
            lng = float(lng)
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
                return jsonify({"error": "lat 必須為數字"}), 400
        if lng is not None:
            try:
                m.lng = float(lng)
            except ValueError:
                return jsonify({"error": "lng 必須為數字"}), 400

        db.session.commit()
        return jsonify(m.to_dict()), 200

    @app.route("/api/markers/<int:marker_id>", methods=["DELETE"])
    def api_delete_marker(marker_id):
        m = Marker.query.get_or_404(marker_id)
        db.session.delete(m)
        db.session.commit()
        return jsonify({"message": "刪除成功"}), 200

    return app


# ✅ 程式執行入口
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
    
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from .models import db, Marker, User
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    db_path = os.path.join(BASE_DIR, "markers.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = "secret-key-change-me"

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    # ---------- 登入註冊頁 ----------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            if User.query.filter_by(username=username).first():
                flash("此帳號已存在")
                return redirect(url_for("register"))
            u = User(username=username)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("註冊成功，請登入")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            u = User.query.filter_by(username=username).first()
            if u and u.check_password(password):
                login_user(u)
                flash("登入成功")
                return redirect(url_for("index"))
            flash("帳號或密碼錯誤")
            return redirect(url_for("login"))
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("已登出")
        return redirect(url_for("login"))

    # ---------- 頁面 ----------
    @app.route("/")
    def index():
        return render_template("list.html")

    @app.route("/create")
    @login_required
    def create_page():
        return render_template("create.html")

    @app.route("/marker/<int:marker_id>")
    def view_marker(marker_id):
        return render_template("view.html", marker_id=marker_id)

    @app.route("/marker/<int:marker_id>/edit")
    @login_required
    def edit_marker(marker_id):
        m = Marker.query.get_or_404(marker_id)
        if m.user_id != current_user.id:
            flash("你沒有權限編輯此標記")
            return redirect(url_for("index"))
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
    @login_required
    def api_create_marker():
        data = request.get_json() or request.form
        name = data.get("name")
        lat = data.get("lat")
        lng = data.get("lng")
        description = data.get("description")

        if not name or lat is None or lng is None:
            return jsonify({"error": "缺少必要欄位"}), 400

        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return jsonify({"error": "座標格式錯誤"}), 400

        m = Marker(name=name, description=description, lat=lat, lng=lng, user_id=current_user.id)
        db.session.add(m)
        db.session.commit()
        return jsonify(m.to_dict()), 201

    @app.route("/api/markers/<int:marker_id>", methods=["PUT"])
    @login_required
    def api_update_marker(marker_id):
        m = Marker.query.get_or_404(marker_id)
        if m.user_id != current_user.id:
            return jsonify({"error": "你沒有權限修改此標記"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"error": "需要 JSON body"}), 400

        if "name" in data: m.name = data["name"]
        if "description" in data: m.description = data["description"]
        if "lat" in data: m.lat = float(data["lat"])
        if "lng" in data: m.lng = float(data["lng"])

        db.session.commit()
        return jsonify(m.to_dict()), 200

    @app.route("/api/markers/<int:marker_id>", methods=["DELETE"])
    @login_required
    def api_delete_marker(marker_id):
        m = Marker.query.get_or_404(marker_id)
        if m.user_id != current_user.id:
            return jsonify({"error": "你沒有權限刪除此標記"}), 403
        db.session.delete(m)
        db.session.commit()
        return jsonify({"message": "刪除成功"}), 200

    return app
app = create_app()



