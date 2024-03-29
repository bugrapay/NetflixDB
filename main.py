from flask import Flask, request, jsonify, redirect, url_for, render_template
from flask_jwt_extended import create_access_token, JWTManager, create_refresh_token, jwt_required
from flask_sqlalchemy import SQLAlchemy
from email.message import EmailMessage
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3, ssl, smtplib


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/bugra/Desktop/Coding/NetflixDB/users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/bugra/Desktop/Coding/NetflixDB/filmsDB/films.db'
db = SQLAlchemy(app)
app.config['JWT_SECRET_KEY'] = 'alttab'
jwt = JWTManager(app)


# Kullanıcı Veritabanı işleme
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)


# Film Veritabanı işleme
class Films(db.Model):
    __tablename__ = "films"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    year = db.Column(db.Integer)
    cast = db.Column(db.String)
    director = db.Column(db.String)
    genre = db.Column(db.String)
    score = db.Column(db.String)
    url = db.Column(db.String)

#Film Ekleme:
@app.route('/api/films/<int:id>/thumbnails', methods=['POST'])
def add_thumbnail(id):
    film = Films(
        url =request.form['url'],
        name=request.form["name"],
        year=request.form["year"],
        cast=request.form["cast"],
        director=request.form["director"],
        genre=request.form["genre"],
        score=request.form["score"]

    )
    db.session.add(film)
    db.session.commit()
    return 'Thumbnail added', 201


# Giriş sayfası
@app.route('/login', methods=['POST'])
def login():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()

    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username:
        return jsonify({"msg": "Kullanıcı Adı giriniz"}), 400
    if not password:
        return jsonify({"msg": "Parola giriniz"}), 400

    # kullanıcı kimlik kontrolü

    for row in rows:
        if row[1] == username and row[5] == password:

            access_token = create_access_token(identity=username)
            return jsonify({"msg": "Giriş Başarılı!"}), 200
            break
        refresh_token = create_refresh_token({"username": username})
        return {
            "access_token": access_token.decode(),
            "refresh_token": refresh_token.decode(),
        }

    conn.close()

    # erişim tokeni oluşturma

    # return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Kullanıcı adı veya parola hatalı!"}), 400


# Kullanıcı listesi
@app.route("/users")
def user_list():
    users = db.session.execute(
        db.select(Users).order_by(Users.username)).scalars()
    # return render_template("user/list.html", users=users)
    return jsonify(users=users)


@app.route("/users/create", methods=["GET", "POST"])
def user_create():
    if request.method == "POST":
        user = Users(
            name=request.form["name"],
            surname=request.form["surname"],
            username=request.form["username"],
            email=request.form["email"],
            password=request.form["password"],
            location=request.form["location"]

        )
        db.session.add(user)
        db.session.commit()
        # return redirect(url_for("user_detail", id=user.id))

    # return render_template("user/create.html")
    return redirect(url_for("user_detail", id=user.id))


# Kullanıcı bilgileri
@app.route("/user/<int:id>")
@jwt_required()
def user_detail(id):
    user = db.get_or_404(Users, id)
    # return render_template("user/detail.html", user=user)
    return jsonify(user=user)


# Kullanıcı silme
@app.route("/user/<int:id>/delete", methods=["GET", "POST"])
@jwt_required()
def user_delete(id):
    user = db.get_or_404(Users, id)

    if request.method == "POST":
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for("user_list"))

    return render_template("user/delete.html", user=user)


# Kullanıcı güncelleme
@app.route("/update/<int:id>", methods=["GET", "POST"])
@jwt_required()
def update_user(id):
    user_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        user_to_update.name = request.form["name"]
        user_to_update.surname = request.form["surname"]
        user_to_update.email = request.form["email"]
        user_to_update.location = request.form["location"]
        user_to_update.password = request.form["password"]
        try:
            db.session.commit()
            return jsonify("Kullanıcı bilgileri başarıyla güncellendi")
        except:
            return "Kullanıcı bilgileri güncellenirken sorun oluştu..."

    return


# Forgot Password
@app.route("/forgotpass", methods=["POST"])
def send_email_pass():
    given_email = request.json["email"]
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()

    for row in rows:

        if row[4] == given_email:
            email_sender = "netflix.db.gr4@gmail.com"
            email_sender_password = "canubbaoreztdduh"
            email_receiver = given_email
            subject = "Şifre Sıfırlama"
            body = """
            Helal lan Buğra
            """

            em = EmailMessage()
            em["From"] = email_sender
            em["To"] = email_receiver
            em["subject"] = subject
            em.set_content(body)

            context = ssl.create_default_context

            """
            server = smtplib.SMTP("smtp.gmail.com",465)
            server.login(email_sender, email_sender_password)
            server.sendmail(email_sender, email_receiver, context)
            server.quit()
            """

            with smtplib.SMTP_SSL("smtp.gmail.com", 587, context=context) as smtp:
                smtp.login(email_sender, email_sender_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string)
                return jsonify({"msg": "Lütfen eposta kutunuzu kontrol edin"}), 200
            
        continue

    conn.close()

"""
@app.route("/deneme", methods=["GET", "POST"])
def deneme():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    jsonify(print(rows))

    for row in rows:
        jsonify(print(row[4]))
        continue
"""

if __name__ == '__main__':
    app.run(debug=True)
