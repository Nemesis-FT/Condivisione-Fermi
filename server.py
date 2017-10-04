from flask import Flask, session, url_for, redirect, request, render_template, abort
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime, date, timedelta
import os
import smtplib

app = Flask(__name__)
#app.secret_key = os.environ["flask_secret_key"]
app.secret_key = "ciao"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Classi


class User(db.Model):
    __tablename__ = 'user'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    passwd = db.Column(db.LargeBinary)
    nome = db.Column(db.String)
    cognome = db.Column(db.String)
    classe = db.Column(db.String)
    tipo = db.Column(db.Integer)
    # 0 = utente normale, 1 = peer, 2 = amministratore
    telegram_username = db.Column(db.String, nullable=True)
    corsi = db.relationship("Corso")
    materie = db.relationship("Abilitato", backref='utente', lazy='dynamic', cascade='delete')
    impegno = db.relationship("Impegno")

    def __init__(self, username, passwd, nome, cognome, classe, tipo, telegram_username):
        self.username = username
        self.passwd = passwd
        self.nome = nome
        self.cognome = cognome
        self.classe = classe
        self.tipo = tipo
        self.telegram_username = telegram_username

    def __repr__(self):
        return "<User {}>".format(self.username, self.passwd, self.nome, self.cognome, self.classe)


class Corso(db.Model):
    __tablename__ = 'corso'
    cid = db.Column(db.Integer, primary_key=True)
    pid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    argomenti = db.Column(db.String)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.mid'))
    impegno = db.relationship("Impegno")
    materia = db.relationship("Materia")

    def __init__(self, pid, argomenti, materia_id):
        self.pid = pid
        self.argomenti = argomenti
        self.materia_id = materia_id

    def __repr__(self):
        return "<Corso {}>".format(self.cid, self.pid)


class Materia(db.Model):
    __tablename__ = "materia"
    mid = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String)
    professore = db.Column(db.String)
    impegno = db.relationship("Impegno")
    utente = db.relationship("Abilitato", backref="materia", lazy='dynamic', cascade='delete')
    giorno_settimana = db.Column(db.Integer)
    ora = db.Column(db.String)

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
    corso_id = db.Column(db.Integer, db.ForeignKey('corso.cid'))
    stud_id = db.Column(db.Integer, db.ForeignKey('user.uid'))
    mat_id = db.Column(db.Integer, db.ForeignKey('materia.mid'))
    materia = db.Column(db.String)
    peer = db.Column(db.String)
    giorno = db.Column(db.Integer)
    ora = db.Column(db.String)

    def __init__(self, peer_id, stud_id, mat_id, materia, peer, giorno, ora):
        self.peer_id = peer_id
        self.stud_id = stud_id
        self.mat_id = mat_id
        self.materia = materia
        self.peer = peer
        self.giorno = giorno
        self.ora = ora


class Messaggio(db.Model):
    __tablename__ = 'messaggio'
    mid = db.Column(db.Integer, primary_key=True, unique=True)
    testo = db.Column(db.String)
    data = db.Column(db.Date)
    tipo = db.Column(db.Integer)  # 1 = success 2 = primary 3 = warning

    def __init__(self, testo, data, tipo):
        self.testo = testo
        self.data = data
        self.tipo = tipo


class Abilitato(db.Model):
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

# Funzioni


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


def sendemail(emailutente, kind, appuntamento, nome, materia, messaggio):
    username = ""
    password = ""
    sender = ""
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(username, password)
        msg = "Qualcosa non ha funzionato. Collegati al sito per vedere cosa c\'e\' di nuovo"
        if kind == 1:  # Hai una nuova richiesta sul sito
            msg = "L\'utente " + nome + " ha chiesto un appuntamento il " + appuntamento + " per " + materia + ". Per accettare o declinare, accedi al sito Condivisione."
        elif kind == 2:
            msg = "La tua richiesta di ripetizione fatta allo studente " + nome + " non e\' stata accettata. La motivazione e\' stata: " + messaggio + "."
        elif kind == 3:
            msg = "La tua richiesta di ripetizione fatta allo studente " + nome + " e\' stata accettata."
        elif kind == 4:
            msg = "Il peer " + nome + " ha chiesto di spostare la ripetizione per il " + appuntamento + ". Per accettare o declinare, accedi al sito Condivisione."
        elif kind == 5:
            msg = "Lo studente " + nome + "ha accettato la tua proposta per il " + appuntamento
        server.sendmail(sender, emailutente, msg)
        server.quit()
    except:
        stringa = "Errore di invio e-mail"
        nuovorecord = Log(stringa, datetime.today())
        db.session.add(nuovorecord)


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
            valore = 2
        nuovouser = User(request.form['username'], cenere, request.form['nome'], request.form['cognome'],
                         request.form['classe'], valore, request.form['usernameTelegram'])
        stringa = "L'utente " + nuovouser.username + " si è iscritto a Condivisione"
        nuovorecord = Log(stringa, datetime.today())
        db.session.add(nuovorecord)
        db.session.add(nuovouser)
        db.session.commit()
        return redirect(url_for('page_login'))


@app.route('/dashboard')
def page_dashboard():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        messaggi = Messaggio.query.order_by(Messaggio.data.desc()).all()
        corsi = Corso.query.join(Materia).join(User).all()
        impegni = Impegno.query.filter_by(peer=utente.username).join(Materia).all()
        lezioni = Impegno.query.filter_by(stud_id=utente.uid).join(Materia).all()
        oggi = datetime.today().weekday()
        oggi = oggi + 1
        for impegno in impegni:
            if impegno.giorno == oggi:
                db.session.delete(impegno)
        for lezione in lezioni:
            if lezione.giorno == oggi:
                db.session.delete(lezione)
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
        if utente.tipo != 2:
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
        if utente.tipo != 2:
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
        if utente.tipo != 2:
            abort(403)
        utenti = User.query.all()
        return render_template("User/list.htm", utente=utente, utenti=utenti)


@app.route('/user_changepw/<int:uid>', methods=['GET', 'POST'])
def page_user_changepw(uid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 2:
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
        if utente.tipo != 2:
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
        if utente.tipo != 2:
            abort(403)
        else:
            stringa = "L'utente " + utente.username + " ha reso ADMIN l'utente " + str(uid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            entita = User.query.get_or_404(uid)
            if entita.tipo == 2:
                entita.tipo = 1
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
        if utente.tipo != 2:
            abort(403)
        else:
            stringa = "L'utente " + utente.username + " ha ELIMINATO l'utente "+ str(uid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            entita = User.query.get_or_404(uid)
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
                db.session.commit()
                return redirect(url_for('page_dashboard'))


@app.route('/materia_add', methods=['GET', 'POST'])
def page_materia_add():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 2:
            abort(403)
        else:
            if request.method == 'GET':
                return render_template("Materia/add.htm", utente=utente)
            else:
                stringa = "L'utente " + utente.username + " ha creato una materia "
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
                nuovamateria = Materia(request.form["nome"], request.form["professore"], request.form["giorno"], request.form['ora'])
                db.session.add(nuovamateria)
                db.session.commit()
                return redirect(url_for('page_materia_list'))


@app.route('/materia_list')
def page_materia_list():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 2:
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
        if utente.tipo != 2:
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
        if utente.tipo != 2:
            abort(403)
        else:
            stringa = "L'utente " + utente.username + " ha ELIMINATO la materia " + str(mid)
            nuovorecord = Log(stringa, datetime.today())
            db.session.add(nuovorecord)
            materia = Materia.query.get_or_404(mid)
            corsi = Corso.query.all()
            impegni = Impegno.query.all()
            for corso in corsi:
                if corso.materia_id == mid:
                    db.session.delete(corso)
                    stringa = "L'utente " + utente.username + " ha ELIMINATO il corso " + str(corso.cid)
                    nuovorecord = Log(stringa, datetime.today())
                    db.session.add(nuovorecord)
            for impegno in impegni:
                if impegno.mat_id == mid:
                    db.session.delete(impegno)
                    stringa = "L'utente " + utente.username + " ha ELIMINATO l'impegno " + str(impegno.iid)
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
            if request.method == 'GET':
                autorizzate = Materia.query.join(Abilitato).join(User).all()
                return render_template("Corso/add.htm", utente=utente, materie=autorizzate)
            else:
                stringa = "L'utente " + utente.username + "ha creato un nuovo corso "
                nuovorecord = Log(stringa, datetime.today())
                db.session.add(nuovorecord)
                nuovocorso = Corso(utente.uid, request.form['argomenti'], request.form['materia'])
                db.session.add(nuovocorso)
                db.session.commit()
                return redirect(url_for('page_dashboard'))


@app.route('/corso_del/<int:cid>')
def page_corso_del(cid):
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo != 2:
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
        if len(impegni) > 0:
            return redirect(url_for('page_dashboard'))
        stringa = "L'utente " + utente.username + " ha chiesto di unirsi al corso " + str(cid)
        nuovorecord = Log(stringa, datetime.today())
        db.session.add(nuovorecord)
        corso = Corso.query.get_or_404(cid)
        peer = User.query.get_or_404(corso.pid)
        materia = Materia.query.get_or_404(corso.materia_id)
        nuovoimpegno = Impegno(corso.cid, utente.uid, corso.materia_id, materia.nome, peer.username,
                               materia.giorno_settimana, materia.ora)
        db.session.add(nuovoimpegno)
        db.session.commit()
        return redirect(url_for('page_dashboard'))


@app.route('/server_log')
def page_log_view():
    if 'username' not in session:
        abort(403)
    else:
        utente = find_user(session['username'])
        if utente.tipo < 2:
            abort(403)
        else:
            logs = Log.query.order_by(Log.ora.desc()).all()
            return render_template("logs.htm", logs=logs, utente=utente)


if __name__ == "__main__":
    # Se non esiste il database, crealo e inizializzalo!
    if not os.path.isfile("db.sqlite"):
        db.create_all()
        db.session.commit()
    nuovrecord = Log("Condivisione avviato. Condivisione è un programma di FermiTech Softworks.", datetime.today())
    db.session.add(nuovrecord)
    db.session.commit()
    app.run()
