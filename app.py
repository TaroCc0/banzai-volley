from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'super_secret_banzai_key_2026'

# Configurazione del Database SQLite (creerà un file chiamato banzai.db)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'banzai.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inizializzazione del database
db = SQLAlchemy(app)

# --------------------------------------------------------
# MODELLI DEL DATABASE (Tabelle)
# --------------------------------------------------------

class Squadra(db.Model):
    __tablename__ = 'squadre'
    id = db.Column(db.Integer, primary_key=True)
    nome_squadra = db.Column(db.String(100), nullable=False, unique=True)
    nome_capitano = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    note = db.Column(db.Text, nullable=True)
    
    # Relazione uno-a-molti: Una squadra ha molti giocatori
    giocatori = db.relationship('Giocatore', backref='squadra', lazy=True, cascade="all, delete-orphan")

class Giocatore(db.Model):
    __tablename__ = 'giocatori'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_nascita = db.Column(db.String(10), nullable=False) # Formato YYYY-MM-DD dal form
    is_capitano = db.Column(db.Boolean, default=False)
    
    # Chiave esterna per collegare il giocatore alla sua squadra
    squadra_id = db.Column(db.Integer, db.ForeignKey('squadre.id'), nullable=False)


# --------------------------------------------------------
# ROTTE DEL SITO
# --------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info')
def info():
    return render_template('info.html')

@app.route('/minigiochi')
def minigiochi():
    return render_template('minigiochi.html')

@app.route('/iscrizione', methods=['GET', 'POST'])
def iscrizione():
    if request.method == 'POST':
        try:
            # 1. Recupero dati generali dal form
            nome_sq = request.form.get('nome_squadra')
            nome_cap = request.form.get('nome_capitano')
            tel = request.form.get('telefono')
            mail = request.form.get('email')
            note_add = request.form.get('note_aggiuntive')
            
            giocatori_nomi = request.form.getlist('giocatore_nome[]')
            giocatori_date = request.form.getlist('giocatore_data[]')
            capitano_index = request.form.get('capitano_selezionato', type=int)
            
            # Controllo se il nome squadra esiste già per evitare duplicati
            squadra_esistente = Squadra.query.filter_by(nome_squadra=nome_sq).first()
            if squadra_esistente:
                flash("Questo nome squadra è già stato registrato!", "danger")
                return redirect(url_for('iscrizione'))

            # 2. Creiamo l'oggetto Squadra
            nuova_squadra = Squadra(
                nome_squadra=nome_sq,
                nome_capitano=nome_cap,
                telefono=tel,
                email=mail,
                note=note_add
            )
            db.session.add(nuova_squadra)
            db.session.flush() # Genera l'ID della squadra prima del commit finale

            # 3. Ciclo per inserire tutti i giocatori collegandoli alla squadra
            for i in range(len(giocatori_nomi)):
                nuovo_giocatore = Giocatore(
                    nome=giocatori_nomi[i],
                    data_nascita=giocatori_date[i],
                    is_capitano=(i == capitano_index),
                    squadra_id=nuova_squadra.id  # Collega la chiave esterna
                )
                db.session.add(nuovo_giocatore)
            
            # 4. Saliamo tutto definitivamente nel database
            db.session.commit()
            
            flash(f"Squadra '{nome_sq}' iscritta con successo nel Database!", "success")
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback() # Annulla le operazioni in caso di errore
            print(f"Errore DB: {e}") # Log per il developer in console
            flash("Si è verificato un errore durante l'iscrizione nel database.", "danger")
            return redirect(url_for('iscrizione'))

    return render_template('iscrizione.html')

# Creazione automatica delle tabelle se non esistono al lancio dell'app
with app.app_context():
    db.create_all()

@app.route('/squadre')
def squadre():
    # Recupera tutte le squadre caricate nel database
    tutte_le_squadre = Squadra.query.all()
    
    # Calcola il numero di squadre iscritte
    totale_iscritte = len(tutte_le_squadre)
    
    # Imposta il limite massimo descritto nelle grafiche
    slot_massimi = 16
    slot_rimanenti = slot_massimi - totale_iscritte
    
    # CORRETTO: rimosso il refuso della 's' finale
    if slot_rimanenti < 0: 
        slot_rimanenti = 0 
    
    return render_template(
        'squadre.html', 
        squadre=tutte_le_squadre, 
        totale=totale_iscritte, 
        massimo=slot_massimi,
        rimanenti=slot_rimanenti
    )

if __name__ == '__main__':
    # host='0.0.0.0' permette l'accesso da altri dispositivi nella stessa rete
    app.run(debug=True, host='0.0.0.0', port=5000)