from flask import Flask, session, url_for, redirect, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime, date, time
import os

app = Flask(__name__)
#app.secret_key = os.environ["flask_secret_key"]
app.secret_key = "ciao"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


"""Tabelle associative"""


materiecorsi_table = db.Table('materiecorsi', db.Model.metadata, db.Column('materia_id', db.Integer, db.ForeignKey('materia.mid')), db.Column('corso_id', db.Integer, db.ForeignKey('corso.cid')))
materieutenti_table = db.Table('materieutenti', db.Model.metadata, db.Column('materia_id', db.Integer, db.ForeignKey('materia.mid')), db.Column('user_id', db.Integer, db.ForeignKey('user.uid')))


"""Seguono le classi del database"""


class User(db.Model):
    __tablename__ = 'user'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    passwd = db.Column(db.LargeBinary)
    nome = db.Column(db.String)
    cognome = db.Column(db.String)
    classe = db.Column(db.String)
    notifiche = db.Column(db.Integer)
    tipo = db.Column(db.Integer)
    """0 = utente normale, 1 = peer, 2 = amministratore"""
    telegram_username = db.Column(db.String)
    corsi = db.relationship("Corso")
    materie = db.relationship("Materia", secondary=materieutenti_table)

    def __init__(self, username, passwd, nome, cognome, classe, tipo, telegram_username):
        self.username = username
        self.passwd = passwd
        self.nome = nome
        self.cognome = cognome
        self.classe = classe
        self.notifiche = 0
        self.tipo = tipo
        self.telegram_username = telegram_username

    def __repr__(self):
        return "<User {}>".format(self.username, self.passwd, self.nome, self.cognome, self.classe)


class Corso(db.Model):
    __tablename__ = 'corso'
    cid = db.Column(db.Integer, primary_key=True)
    pid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    argomenti = db.Column(db.String)
    materia = db.relationship("Materia", secondary=materiecorsi_table)

    def __init__(self, pid, argomenti, materia):
        self.pid = pid
        self.argomenti = argomenti
        self.materia = materia

    def __repr__(self):
        return "<Corso {}>".format(self.cid, self.pid)


class Materia(db.Model):
    __tablename__ = "materia"
    mid = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String)
    professore = db.Column(db.String)

    def __init__(self, nome, professore):
        self.nome = nome
        self.professore = professore

    def __repr__(self):
        return "<Materia {}>".format(self.nome)


class Impegno(db.Model):
    __tablename__ = 'impegno'
    iid = db.Column(db.Integer, primary_key=True, unique=True)
    appuntamento = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    """0 = non visualizzato, 1 = approvato, 2 = non approvato"""
    peer_id = db.Column(db.Integer)
    stud_id = db.Column(db.Integer)
    mat_id = db.Column(db.Integer)

    def __init__(self, appuntamento, peer_id, stud_id, mat_id):
        self.appuntamento = appuntamento
        self.status = 0
        self.peer_id = peer_id
        self.stud_id = stud_id
        self.mat_id = mat_id


"""Funzioni del sito"""


def login(username, password):
    user = User.query.filter_by(username=username).first()
    try:
        return bcrypt.checkpw(bytes(password, encoding="utf-8"), user.passwd)
    except AttributeError:
        # Se non esiste l'Utente
        return False


def find_user(username):
    user = User.query.all()
    for utenze in user:
        if username == utenze.username:
            return utenze


"""Sito"""


@app.route('/')
def page_home():
    if 'username' not in session:
        return redirect(url_for('page_login'))
    else:
        session.pop('username')
        return redirect(url_for('page_login'))


@app.route('/login', methods=['GET', 'POST'])
def page_login():
    if request.method == 'GET':
        css = url_for("static", filename="style.css")
        return render_template("login.htm", css=css)
    else:
        if login(request.form['username'], request.form['password']):
            session['username'] = request.form['username']
            return redirect(url_for('page_dashboard'))
        else:
            abort(403)


@app.route('/register', methods=['GET', 'POST'])
def page_register():
    if request.method == 'GET':
        return render_template("User/add.htm")
    else:
        p = bytes(request.form["password"], encoding="utf-8")
        cenere = bcrypt.hashpw(p, bcrypt.gensalt())
        nuovouser = User(request.form['username'], cenere, request.form['nome'], request.form['cognome'],
                         request.form['classe'], 0, request.form['usernameTelegram'])
        db.session.add(nuovouser)
        db.session.commit()
        return redirect(url_for('page_login'))


@app.route('/dashboard')
def page_dashboard():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        return render_template("dashboard.htm", utente=utente)


if __name__ == "__main__":
    # Se non esiste il database, crealo e inizializzalo!
    if not os.path.isfile("data.db"):
        db.create_all()
    app.run()