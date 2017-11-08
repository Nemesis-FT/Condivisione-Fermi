from flask import Flask, session, url_for, redirect, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
import bcrypt
import smtplib
from datetime import datetime, date, timedelta
import os
import telepot
from telepot.loop import MessageLoop

app = Flask(__name__)
# app.secret_key = os.environ["flask_secret_key"]
chiavi = open("configurazione.txt", 'r')
dati = chiavi.readline()
appkey, telegramkey, from_addr, accesso, password = dati.split("|",
                                                               4)  # Struttura del file configurazione.txt: appkey|telegramkey|emailcompleta|nomeaccountgmail|passwordemail
print(appkey)
print(telegramkey)
print(from_addr)
print(accesso)
print(password)
app.secret_key = appkey
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Classi
# TODO: aggiungere bot

class User(db.Model):
    __tablename__ = 'user'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    emailgenitore = db.Column(db.String, nullable=False)
    passwd = db.Column(db.LargeBinary, nullable=False)
    nome = db.Column(db.String, nullable=False)
    cognome = db.Column(db.String, nullable=False)
    classe = db.Column(db.String)
    tipo = db.Column(db.Integer, nullable=False)
    # 0 = utente normale, 1 = peer, 2 = professore, 3 = amministratore
    telegram_username = db.Column(db.String)
    telegram_chat_id = db.Column(db.String, unique=True)
    corsi = db.relationship("Corso", backref="peer")
    materie = db.relationship("Abilitato", backref='utente', lazy='dynamic', cascade='delete')
    impegno = db.relationship("Impegno")

    def __init__(self, username, passwd, nome, cognome, classe, tipo, telegram_username, emailgenitore):
        self.username = username
        self.passwd = passwd
        self.nome = nome
        self.cognome = cognome
        self.classe = classe
        self.tipo = tipo
        self.telegram_username = telegram_username
        self.emailgenitore = emailgenitore

    def __repr__(self):
        return "<User {}>".format(self.username, self.passwd, self.nome, self.cognome, self.classe)

    def __str__(self):
        return self.nome + " " + self.cognome


class Corso(db.Model):
    __tablename__ = 'corso'
    cid = db.Column(db.Integer, primary_key=True)
    pid = db.Column(db.Integer, db.ForeignKey('user.uid'), nullable=False)
    argomenti = db.Column(db.String, nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.mid'), nullable=False)
    impegno = db.relationship("Impegno")
    materia = db.relationship("Materia")
    tipo = db.Column(db.Integer, nullable=False)  # 0 = ripetizione studente, 1 = recupero professore
    appuntamento = db.Column(db.DateTime)
    limite = db.Column(db.Integer)
    occupati = db.Column(db.Integer)

    def __init__(self, pid, argomenti, materia_id, tipo):
        self.pid = pid
        self.argomenti = argomenti
        self.materia_id = materia_id
        self.tipo = tipo
        if tipo == 0:
            self.limite = 3
        self.occupati = 0

    def __repr__(self):
        return "<Corso {}>".format(self.cid, self.pid)


class Materia(db.Model):
    __tablename__ = "materia"
    mid = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    professore = db.Column(db.String, nullable=False)
    utente = db.relationship("Abilitato", backref="materia", lazy='dynamic', cascade='delete')
    giorno_settimana = db.Column(db.Integer)  # Datetime no eh
    ora = db.Column(db.String)  # Time no eh

    def __init__(self, nome, professore, giorno, ora):
        self.nome = nome
        self.professore = professore
        self.giorno_settimana = giorno
        self.ora = ora

    def __repr__(self):
        return "<Materia {}>".format(self.nome)


class Impegno(db.Model):
    __tablename__ = 'impegno'
    iid = db.Column(db.Integer, primary_key=True, unique=True)
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.cid'), nullable=False)
    stud_id = db.Column(db.Integer, db.ForeignKey('user.uid'), nullable=False)
    studente = db.relationship("User")
    appuntamento = db.Column(db.DateTime)  # ridondante? decisamente
    presente = db.Column(db.Boolean, nullable=False)


class Messaggio(db.Model):
    __tablename__ = 'messaggio'
    mid = db.Column(db.Integer, primary_key=True)
    testo = db.Column(db.String)
    data = db.Column(db.Date)  # FIXME: fammi diventare un datetime e al limite visualizza solo la data
    tipo = db.Column(db.Integer)  # 1 = success 2 = primary 3 = warning

    def __init__(self, testo, data, tipo):
        self.testo = testo
        self.data = data
        self.tipo = tipo


class Abilitato(db.Model):
    # Tabella di associazione
    __tablename__ = "abilitazioni"

    mid = db.Column(db.Integer, db.ForeignKey('materia.mid'), primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'), primary_key=True)

    def __init__(self, mid, uid):
        self.mid = mid
        self.uid = uid

    def __repr__(self):
        return "<Abilitato {} per {}>".format(self.uid, self.mid)


class Log(db.Model):
    __tablename__ = "log"
    lid = db.Column(db.Integer, primary_key=True)
    contenuto = db.Column(db.String)
    ora = db.Column(db.DateTime)

    def __init__(self, contenuto, ora):
        self.contenuto = contenuto
        self.ora = ora


class SessioneBot:
    def __init__(self, utente, nomemenu, autenticato=0):
        self.utente = utente
        self.nomemenu = nomemenu


# Funzioni


def login(username, password):
    user = User.query.filter_by(username=username).first()
    try:
        return bcrypt.checkpw(bytes(password, encoding="utf-8"), user.passwd)
    except AttributeError:
        # Se non esiste l'Utente
        return False


def find_user(username):
    return User.query.filter_by(username=username).first()


def sendemail(to_addr_list, subject, message, smtpserver='smtp.gmail.com:587'):
    e = "Errore di invio mail. Il server potrebbe non essere raggiungibile o l'email immessa errata."
    try:
        header = 'From: %s' % from_addr
        header += 'To: %s' % ','.join(to_addr_list)
        header += 'Subject: %s' % subject
        message = header + message
        server = smtplib.SMTP(smtpserver)
        server.starttls()
        server.login(accesso, password)
        problems = server.sendmail(from_addr, to_addr_list, message)
        server.quit()
    except:
        return redirect(url_for(page_500, e))


def rendi_data_leggibile(poccio):
    data, ora = str(poccio).split(" ", 1)
    anno, mese, giorno = data.split("-", 2)
    ora, minuto, spazzatura = ora.split(":", 2)
    risultato = mese + "/" + giorno + " " + ora + ":" + minuto
    return risultato


def broadcast(msg, utenti=[]):
    for utente in utenti:
        if utente.telegram_chat_id:
            bot.sendMessage(utente.telegram_chat_id, msg)


# Gestori Errori


@app.errorhandler(400)
def page_400(_):
    return render_template('400.htm')


@app.errorhandler(403)
def page_403(_):
    return render_template('403.htm')


@app.errorhandler(404)
def page_404(_):
    return render_template('404.htm')


@app.errorhandler(500)
def page_500(e):
    return render_template('500.htm', e=e)


# Pagine


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
        utenti = User.query.all()
        valore = 0
        if len(utenti) == 0:
            valore = 3
        nuovouser = User(request.form['username'], cenere, request.form['nome'], request.form['cognome'],
                         request.form['classe'], valore, request.form['usernameTelegram'], request.form['mailGenitori'])
        stringa = "L'utente " + nuovouser.username + " si è iscritto a Condivisione"
        nuovorecord = Log(stringa, datetime.today())
        db.session.add(nuovorecord)
        db.session.add(nuovouser)
        db.session.commit()
        return redirect(url_for('page_login'))


@app.route('/dashboard')
def page_dashboard():
    if 'username' not in session or 'username' is None:
        abort(403)
    else:
        utente = find_user(session['username'])
        messaggi = Messaggio.query.order_by(Messaggio.data.desc()).all()
        corsi = Corso.query.join(Materia).join(User).all()
        query1 = text(
            "SELECT impegno.*, materia.nome, materia.giorno_settimana, materia.ora, impegno.appuntamento, corso.limite, corso.occupati , corso.pid FROM impegno JOIN corso ON impegno.corso_id=corso.cid JOIN materia ON corso.materia_id = materia.mid JOIN user ON impegno.stud_id = user.uid WHERE corso.pid=:x;")
        impegni = db.session.execute(query1, {"x": utente.uid}).fetchall()
        query2 = text(
            "SELECT impegno.*, materia.nome, materia.giorno_settimana, materia.ora, impegno.appuntamento, corso.limite, corso.occupati, corso.pid FROM  impegno JOIN corso ON impegno.corso_id=corso.cid JOIN materia ON corso.materia_id = materia.mid JOIN user ON impegno.stud_id = user.uid WHERE impegno.stud_id=:x;")
        lezioni = db.session.execute(query2, {"x": utente.uid}).fetchall()
        db.session.commit()
        return render_template("dashboard.htm", utente=utente, messaggi=messaggi, corsi=corsi, impegni=impegni,
                               lezioni=lezioni)


@app.route('/informazioni')
def page_informaizoni():
    return render_template("informazioni.htm")


@app.route('/message_add', methods=['GET', 'POST'])
def page_message_add():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 3:
            abort(403)
        if request.method == "GET":
            return render_template("Message/add.htm", utente=utente)
        else:
            oggi = date.today()
            nuovomessaggio = Messaggio(request.form['testo'], oggi, request.form['scelta'])
            db.session.add(nuovomessaggio)
            db.session.commit()
            return redirect(url_for('page_dashboard'))


@app.route('/message_del/<int:mid>')
def page_message_del(mid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 3:
            abort(403)
        messaggio = Messaggio.query.get_or_404(mid)
        db.session.delete(messaggio)
        db.session.commit()
        return redirect(url_for('page_dashboard'))


@app.route('/user_list')
def page_user_list():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 3:
            abort(403)
        utenti = User.query.all()
        return render_template("User/list.htm", utente=utente, utenti=utenti)


@app.route('/user_changepw/<int:uid>', methods=['GET', 'POST'])
def page_user_changepw(uid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 3:
            abort(403)
        if request.method == "GET":
            entita = User.query.get_or_404(uid)
            return render_template("User/changepw.htm", utente=utente, entita=entita)
        else:
            stringa = "L'utente " + utente.username + " ha cambiato la password a " + str(uid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            entita = User.query.get_or_404(uid)
            p = bytes(request.form["password"], encoding="utf-8")
            cenere = bcrypt.hashpw(p, bcrypt.gensalt())
            entita.passwd = cenere
            db.session.commit()
            return redirect(url_for('page_user_list'))


@app.route('/user_ascend/<int:uid>', methods=['GET', 'POST'])
def page_user_ascend(uid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 3:
            abort(403)
        else:
            stringa = "L'utente " + utente.username + " ha reso PEER (o rimosso da tale incarico) l'utente " + str(uid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            entita = User.query.get_or_404(uid)
            if request.method == 'GET' and entita.tipo == 0:
                materie = Materia.query.all()
                return render_template("User/ascend.htm", utente=utente, entita=entita, materie=materie)
            elif entita.tipo == 1:
                entita.tipo = 0
                for materia in entita.materie:
                    db.session.delete(materia)
                db.session.commit()
                return redirect(url_for('page_user_list'))
            else:
                materie = list()
                while True:
                    materiestring = 'materia{}'.format(len(materie))
                    if materiestring in request.form:
                        materie.append(request.form[materiestring])
                    else:
                        break
                for materia in materie:
                    nuovocompito = Abilitato(materia, entita.uid)
                    db.session.add(nuovocompito)
                entita.tipo = 1
                db.session.commit()
                return redirect(url_for('page_user_list'))


@app.route('/user_godify/<int:uid>')
def page_user_godify(uid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 3:
            abort(403)
        else:
            stringa = "L'utente " + utente.username + " ha reso ADMIN l'utente " + str(uid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            entita = User.query.get_or_404(uid)
            if entita.tipo == 3:
                entita.tipo = 1
            else:
                entita.tipo = 3
            db.session.commit()
            return redirect(url_for('page_user_list'))


@app.route('/user_teacher/<int:uid>')
def page_user_teacher(uid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 3:
            abort(403)
        else:
            entita = User.query.get_or_404(uid)
            if entita.tipo == 2:
                corsi = Corso.query.filter_by(pid=uid).all()
                for corso in corsi:
                    db.session.remove(corso)
                entita.tipo = 0
            else:
                entita.tipo = 2
            db.session.commit()
            return redirect(url_for('page_user_list'))


@app.route('/user_del/<int:uid>')
def page_user_del(uid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 3:
            abort(403)
        else:
            stringa = "L'utente " + utente.username + " ha ELIMINATO l'utente " + str(uid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            entita = User.query.get_or_404(uid)
            corsi = Corso.query.filter_by(pid=entita.uid).all()
            for corso in corsi:
                stringa = "L'utente " + utente.username + " ha ELIMINATO il corso " + str(corso.cid)
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
                for oggetti in corso.impegno:
                    db.session.delete(oggetti)
                db.session.delete(corso)
            for materia in entita.materie:
                stringa = "L'utente " + utente.username + " ha ELIMINATO la materia " + str(materia.mid)
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
                db.session.delete(materia)
            for compito in entita.impegno:
                db.session.delete(compito)
            db.session.delete(entita)
            db.session.commit()
            return redirect(url_for('page_user_list'))


@app.route('/user_inspect/<int:pid>')
def page_user_inspect(pid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        entita = User.query.get_or_404(pid)
        return render_template("User/inspect.htm", utente=utente, entita=entita)


@app.route('/user_edit/<int:uid>', methods=['GET', 'POST'])
def page_user_edit(uid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.uid != uid:
            abort(403)
        else:
            if request.method == 'GET':
                entita = User.query.get_or_404(uid)
                return render_template("User/edit.htm", utente=utente, entita=entita)
            else:
                stringa = "L'utente " + utente.username + " ha modificato il proprio profilo"
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
                entita = User.query.get_or_404(uid)
                p = bytes(request.form["password"], encoding="utf-8")
                cenere = bcrypt.hashpw(p, bcrypt.gensalt())
                entita.passwd = cenere
                entita.classe = request.form["classe"]
                entita.telegram_username = request.form["usernameTelegram"]
                entita.emailgenitore = request.form['mailGenitori']
                db.session.commit()
                return redirect(url_for('page_dashboard'))


@app.route('/materia_add', methods=['GET', 'POST'])
def page_materia_add():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 2:
            abort(403)
        else:
            if request.method == 'GET':
                return render_template("Materia/add.htm", utente=utente)
            else:
                stringa = "L'utente " + utente.username + " ha creato una materia "
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
                nuovamateria = Materia(request.form["nome"], request.form["professore"], request.form["giorno"],
                                       request.form['ora'])
                db.session.add(nuovamateria)
                db.session.commit()
                return redirect(url_for('page_materia_list'))


@app.route('/materia_list')
def page_materia_list():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 2:
            abort(403)
        else:
            materie = Materia.query.all()
            return render_template("Materia/list.htm", utente=utente, materie=materie)


@app.route('/materia_edit/<int:mid>', methods=['GET', 'POST'])
def page_materia_edit(mid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 2:
            abort(403)
        else:
            if request.method == 'GET':
                materia = Materia.query.get_or_404(mid)
                return render_template("Materia/edit.htm", utente=utente, materia=materia)
            else:
                stringa = "L'utente " + utente.username + " ha modificato la materia " + str(mid)
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
                materia = Materia.query.get_or_404(mid)
                materia.nome = request.form['nome']
                materia.professore = request.form['professore']
                materia.giorno_settimana = request.form['giorno']
                materia.ora = request.form['ora']
                db.session.commit()
                return redirect(url_for('page_materia_list'))


@app.route('/materia_del/<int:mid>')
def page_materia_del(mid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 2:
            abort(403)
        else:
            materia = Materia.query.get_or_404(mid)
            corsi = Corso.query.filter_by(materia_id=mid).all()
            stringa = "L'utente " + utente.username + " ha ELIMINATO la materia " + str(mid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            for corso in corsi:
                for impegni in corso.impegno:
                    db.session.delete(impegni)
                db.session.delete(corso)
                stringa = "L'utente " + utente.username + " ha ELIMINATO il corso " + str(corso.cid)
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
            db.session.delete(materia)
            db.session.commit()
            return redirect(url_for('page_dashboard'))


@app.route('/corso_add', methods=['GET', 'POST'])
def page_corso_add():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 1:
            abort(403)
        else:
            if utente.tipo == 1:
                if request.method == 'GET':
                    autorizzate = Materia.query.join(Abilitato).join(User).all()
                    return render_template("Corso/add.htm", utente=utente, materie=autorizzate)
                else:
                    stringa = "L'utente " + utente.username + "ha creato un nuovo corso "
                    nuovorecord = Log(stringa, datetime.today())
                    db.session.add(nuovorecord)
                    nuovocorso = Corso(utente.uid, request.form['argomenti'], request.form['materia'], 0)
                    db.session.add(nuovocorso)
                    db.session.commit()
                    return redirect(url_for('page_dashboard'))
            elif utente.tipo == 2:
                if request.method == 'GET':
                    materie = Materia.query.all()
                    return render_template("Recuperi/add.htm", utente=utente, materie=materie)
                else:
                    stringa = "L'utente " + utente.username + "ha creato un nuovo corso "
                    nuovorecord = Log(stringa, datetime.today())
                    db.session.add(nuovorecord)
                    nuovocorso = Corso(utente.uid, request.form['argomenti'], request.form['materia'], 1)
                    yyyy, mm, dd = request.form["data"].split("-", 2)
                    hh, mi = request.form["ora"].split(":", 1)
                    try:
                        data = datetime(int(yyyy), int(mm), int(dd), int(hh), int(mi))
                    except ValueError:
                        # TODO: metti un errore più carino
                        abort(400)
                    nuovocorso.appuntamento = data
                    nuovocorso.limite = request.form["massimo"]
                    db.session.add(nuovocorso)
                    db.session.commit()
                    utenze = User.query.all()
                    oggetto = Materia.query.filter_by(mid=request.form['materia'])
                    msg = "E' stato creato un nuovo corso di " + oggetto[
                        0].nome + "!.\nPer maggiori informazioni, collegati a Condivisione!"
                    broadcast(msg, utenze)
                    return redirect(url_for('page_dashboard'))


@app.route('/corso_del/<int:cid>')
def page_corso_del(cid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 2:
            abort(403)
        else:
            stringa = "L'utente " + utente.username + " ha ELIMINATO il corso " + str(cid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            corso = Corso.query.get_or_404(cid)
            impegni = Impegno.query.all()
            for impegno in impegni:
                if impegno.corso_id == cid:
                    db.session.delete(impegno)
                    stringa = "L'utente " + utente.username + " ha ELIMINATO l'impegno " + str(impegno.iid)
                    nuovorecord = Log(stringa, datetime.today())
                    db.session.add(nuovorecord)
            db.session.delete(corso)
            db.session.commit()
            return redirect(url_for('page_dashboard'))


@app.route('/corso_join/<int:cid>', methods=['GET', 'POST'])
def page_corso_join(cid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        impegni = Impegno.query.filter_by(stud_id=utente.uid).all()
        for impegno in impegni:
            if impegno.stud_id == utente.uid and impegno.corso_id == cid:
                return redirect(url_for('page_dashboard'))
        corso = Corso.query.get_or_404(cid)
        if corso.occupati >= corso.limite:
            return redirect(url_for('page_dashboard'))
        corso.occupati = corso.occupati + 1
        stringa = "L'utente " + utente.username + " ha chiesto di unirsi al corso " + str(cid)
        nuovorecord = Log(stringa, datetime.today())
        db.session.add(nuovorecord)
        nuovoimpegno = Impegno(studente=utente,
                               corso_id=cid, presente=False)
        if corso.tipo != 0:
            print(corso.materia.nome)
            nuovoimpegno.appuntamento = corso.appuntamento
        oggetto = "Condivisione - Iscrizione alla lezione"
        mail = "\n\nSuo figlio si e' iscritto ad una lezione sulla piattaforma Condivisione. Per maggiori informazioni, collegarsi al sito.\nQuesto messaggio e' stato creato automaticamente da Condivisione. Messaggi inviati a questo indirizzo non verranno letti. Per qualsiasi problema, contattare la segreteria."
        sendemail(utente.emailgenitore, oggetto, mail)
        db.session.add(nuovoimpegno)
        db.session.commit()
        return redirect(url_for('page_dashboard'))


@app.route('/server_log')
def page_log_view():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 3:
            abort(403)
        else:
            logs = Log.query.order_by(Log.ora.desc()).all()
            return render_template("logs.htm", logs=logs, utente=utente)


@app.route('/corso_membri/<int:cid>')
def corso_membri(cid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 1:
            abort(403)
        query = text(
            "SELECT corso.*, impegno.stud_id, impegno.presente, user.cognome, user.nome FROM corso JOIN impegno ON corso.cid = impegno.corso_id JOIN user on impegno.stud_id = user.uid WHERE corso.cid=:x;")
        utenti = db.session.execute(query, {"x": cid}).fetchall()
        return render_template("Corso/membri.htm", utente=utente, entita=utenti, idcorso=cid)


@app.route('/presenza/<int:uid>/<int:cid>')
def page_presenza(uid, cid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        lezione = Corso.query.get(cid)
        if utente.tipo <= 1 or utente.uid != lezione.pid:
            abort(403)
        else:
            impegno = Impegno.query.filter_by(stud_id=uid, corso_id=cid).first()
            if impegno.presente:
                impegno.presente = False
            else:
                impegno.presente = True
            db.session.commit()
            return redirect(url_for('corso_membri', cid=cid))


@app.route('/inizialezione/<int:cid>')
def page_inizia(cid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        lezione = Corso.query.get_or_404(cid)
        if utente.tipo < 1 or utente.uid != lezione.pid:
            abort(403)
        query = text(
            "SELECT corso.*, impegno.stud_id, impegno.presente, user.cognome, user.nome, user.emailgenitore FROM corso JOIN impegno ON corso.cid = impegno.corso_id JOIN user on impegno.stud_id = user.uid WHERE corso.cid=:x;")
        utenti = db.session.execute(query, {"x": cid}).fetchall()
        for utente2 in utenti:
            if str(utente2[9]) == 1:
                oggetto = "Condivisione - Partecipazione alla lezione"
                mail = "\n\nSuo figlio e' presente alla lezione di oggi pomeriggio.\nQuesto messaggio e' stato creato automaticamente da Condivisione. Messaggi inviati a questo indirizzo non verranno letti. Per qualsiasi problema, contattare la segreteria."
                sendemail(utente2[12], oggetto, mail)
            else:
                oggetto = "Condivisione - Assenza alla lezione"
                mail = "\n\nSuo figlio non e' presente alla lezione di oggi pomeriggio.\nQuesto messaggio e' stato creato automaticamente da Condivisione. Messaggi inviati a questo indirizzo non verranno letti. Per qualsiasi problema, contattare la segreteria."
                sendemail(utente2[12], oggetto, mail)
        stringa = "L'utente " + utente.username + " ha ELIMINATO il corso " + str(cid)
        nuovorecord = Log(stringa, datetime.today())
        db.session.add(nuovorecord)
        corso = Corso.query.get_or_404(cid)
        impegni = Impegno.query.all()
        for impegno in impegni:
            if impegno.corso_id == cid:
                db.session.delete(impegno)
                stringa = "L'utente " + utente.username + " ha ELIMINATO l'impegno " + str(impegno.iid)
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
        db.session.delete(corso)
        db.session.commit()
        return redirect(url_for('page_dashboard'))


@app.route('/ricerca', methods=["GET", "POST"])  # Funzione scritta da Stefano Pigozzi nel progetto Estus
def page_ricerca():
    if 'username' not in session:
        return abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 2:
            abort(403)
        else:
            if request.method == 'GET':
                return render_template("query.htm", pagetype="query")
            else:
                try:
                    result = db.engine.execute("SELECT " + request.form["query"] + ";")
                except Exception as e:
                    return render_template("query.htm", query=request.form["query"], error=repr(e), pagetype="query")
                return render_template("query.htm", query=request.form["query"], result=result,
                                       pagetype="query")


@app.route('/botStart')
def page_bot():
    if 'username' not in session:
        return abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 2:
            abort(403)
        else:
            global bot
            bot = telepot.Bot(telegramkey)
            bot.getMe()
            MessageLoop(bot, handle).run_as_thread()


# Bot


def handle(msg):
    with app.app_context():
        content_type, chat_type, chat_id = telepot.glance(msg)
        username = "@"
        username += msg['from']['username']
        if content_type == 'text':
            utenza = User.query.filter_by(telegram_chat_id=chat_id).all()
            if not utenza:
                accedi(chat_id, username)
            else:
                utente = utenza[0]
                testo = msg['text']
                if testo == "/aiuto":
                    bot.sendMessage(chat_id,
                                    "I comandi disponibili sono:\n/aiuto - Lista comandi\n/impegni - Lista degli impegni\n")
                elif testo == "/impegni":

                    query1 = text(
                        "SELECT impegno.*, materia.nome, materia.giorno_settimana, materia.ora, impegno.appuntamento, corso.limite, corso.occupati , corso.pid FROM impegno JOIN corso ON impegno.corso_id=corso.cid JOIN materia ON corso.materia_id = materia.mid JOIN user ON impegno.stud_id = user.uid WHERE corso.pid=:x;")
                    impegni = db.session.execute(query1, {"x": utente.uid}).fetchall()
                    query2 = text(
                        "SELECT impegno.*, materia.nome, materia.giorno_settimana, materia.ora, impegno.appuntamento, corso.limite, corso.occupati, corso.pid FROM  impegno JOIN corso ON impegno.corso_id=corso.cid JOIN materia ON corso.materia_id = materia.mid JOIN user ON impegno.stud_id = user.uid WHERE impegno.stud_id=:x;")
                    lezioni = db.session.execute(query2, {"x": utente.uid}).fetchall()
                    messaggio = ""
                    if len(impegni) > 0:
                        messaggio += "Ecco i tuoi impegni:\n"
                        for impegno in impegni:
                            messaggio += "Materia: " + impegno[5] + " "
                            if impegno[8]:
                                messaggio += rendi_data_leggibile(impegno[8])
                            else:
                                if str(impegno[6]) == "1":
                                    giorno = "Lunedì"
                                elif str(impegno[6]) == "2":
                                    giorno = "Martedì"
                                elif str(impegno[6]) == "3":
                                    giorno = "Mercoledì"
                                elif str(impegno[6]) == "4":
                                    giorno = "Giovedì"
                                elif str(impegno[6]) == "5":
                                    giorno = "Venerdì"
                                ora = str(impegno[7])
                                messaggio += giorno + " " + ora + "\n"
                    if len(lezioni) > 0:
                        messaggio += "Ecco le ripetizioni che devi ricevere:\n"
                        for impegno in lezioni:
                            messaggio += "Materia: " + impegno[5] + " "
                            if impegno[8]:
                                messaggio += rendi_data_leggibile(impegno[8])
                            else:
                                if str(impegno[6]) == "1":
                                    giorno = "Lunedì"
                                elif str(impegno[6]) == "2":
                                    giorno = "Martedì"
                                elif str(impegno[6]) == "3":
                                    giorno = "Mercoledì"
                                elif str(impegno[6]) == "4":
                                    giorno = "Giovedì"
                                elif str(impegno[6]) == "5":
                                    giorno = "Venerdì"
                                ora = str(impegno[7])
                                messaggio += giorno + " " + ora + "\n"
                    if len(lezioni) == 0 and len(impegni) == 0:
                        messaggio += "Sembra che tu non abbia impegni. Beato te!"
                    bot.sendMessage(chat_id, messaggio)


def accedi(chat_id, username):
    with app.app_context():
        utenti = User.query.filter_by(telegram_username=username).all()
        print(username)
        if not utenti:
            bot.sendMessage(chat_id,
                            "Si è verificato un problema con l'autenticazione. Assicurati di aver impostato correttamete il tuo username su Condivisione")
        else:
            bot.sendMessage(chat_id,
                            "Collegamento riuscito. D'ora in avanti, il bot ti avviserà ogni volta che un corso verrà creato e riepilogherà i tuoi impegni.\nPer dissociare questo account, visita Condivisione.\n\nPer visualizzare i comandi, digita /aiuto.")
            utenti[0].telegram_chat_id = chat_id
            db.session.commit()


if __name__ == "__main__":
    # Se non esiste il database viene creato
    if not os.path.isfile("db.sqlite"):
        db.create_all()
        db.session.commit()
    nuovrecord = Log("Condivisione avviato. Condivisione è un programma di FermiTech Softworks.",
                     datetime.today())
    print("Bot di Telegram avviato!")
    db.session.add(nuovrecord)
    db.session.commit()
    app.run()
