import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError

# --- KONFIGURACJA APLIKACJI ---

# Pobieramy ścieżkę do bieżącego folderu
basedir = os.path.abspath(os.path.dirname(__file__))

# Tworzymy instancję aplikacji Flask
app = Flask(__name__)

# Konfigurujemy naszą aplikację, aby wiedziała, gdzie jest plik bazy danych.
# Stworzymy plik 'database.db' w głównym folderze projektu.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
# Wyłączamy niepotrzebne śledzenie modyfikacji, aby oszczędzić zasoby
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Tworzymy obiekt bazy danych, łącząc SQLAlchemy z naszą aplikacją Flask
db = SQLAlchemy(app)

# --- LISTA PREDEFINIOWANYCH STATUSÓW ---
MOZLIWE_STATUSY = [
    'Dostępny', 
    'W użyciu',
    'Rezerwacja',
    'Wysłany', 
    'Zablokowany', 
    'Uszkodzony', 
]

# --- MODELE DANYCH (ODWZOROWANIE TABEL BAZY DANYCH) ---

class Urzadzenie(db.Model):
    __tablename__ = 'urzadzenia' # Opcjonalnie: явna nazwa tabeli
    id = db.Column(db.Integer, primary_key=True)
    identyfikator_sprzetu = db.Column(db.String(50), unique=True, nullable=False)
    nazwa = db.Column(db.String(100), nullable=False)
    producent = db.Column(db.String(100))
    nr_seryjny = db.Column(db.String(100), unique=True)
    data_zakupu = db.Column(db.Date)
    aktualny_imei_sim = db.Column(db.String(50))
    aktualna_lokalizacja = db.Column(db.String(100))
    aktualny_status = db.Column(db.String(50))
    uwagi_serwisowe = db.Column(db.Text)
    # Relacja do historii zmian - pozwala łatwo uzyskać wszystkie wpisy historii dla danego urządzenia
    historia = db.relationship('HistoriaZmian', backref='urzadzenie', lazy=True)

class Uzytkownik(db.Model):
    __tablename__ = 'uzytkownicy'
    id = db.Column(db.Integer, primary_key=True)
    imie_nazwisko = db.Column(db.String(100), nullable=False)
    historia_zmian = db.relationship('HistoriaZmian', backref='uzytkownik', lazy=True)

class Lokalizacja(db.Model):
    __tablename__ = 'lokalizacje'
    id = db.Column(db.Integer, primary_key=True)
    nazwa_lokalizacji = db.Column(db.String(100), unique=True, nullable=False)
    typ_lokalizacji = db.Column(db.String(50), nullable=False) # np. Magazyn, Pojazd, Budowa

class HistoriaZmian(db.Model):
    __tablename__ = 'historia_zmian'
    id = db.Column(db.Integer, primary_key=True)
    data_zmiany = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lokalizacja = db.Column(db.String(100))
    status = db.Column(db.String(50))
    imei_sim = db.Column(db.String(50))
    uwagi = db.Column(db.Text)
    # Klucze obce - czyli połączenia z innymi tabelami
    urzadzenie_id = db.Column(db.Integer, db.ForeignKey('urzadzenia.id'), nullable=False)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownicy.id'), nullable=False)


@app.route('/')
def index():
    wszystkie_urzadzenia = Urzadzenie.query.all()
    return render_template('index.html', urzadzenia=wszystkie_urzadzenia)


@app.route('/zmien/<int:urzadzenie_id>', methods=['GET', 'POST'])
def zmien_status(urzadzenie_id):
    urzadzenie_do_zmiany = Urzadzenie.query.get_or_404(urzadzenie_id)

    if request.method == 'POST':
        nowa_lokalizacja_id = request.form.get('lokalizacja')
        uzytkownik_id = request.form.get('uzytkownik')
        uwagi = request.form.get('uwagi')
        nowy_status = request.form.get('status')

        nowa_lokalizacja_obj = Lokalizacja.query.get(nowa_lokalizacja_id)
                     
        urzadzenie_do_zmiany.aktualna_lokalizacja = nowa_lokalizacja_obj.nazwa_lokalizacji
        urzadzenie_do_zmiany.aktualny_status = nowy_status

        wpis_historii = HistoriaZmian(
            urzadzenie_id=urzadzenie_do_zmiany.id,
            uzytkownik_id=uzytkownik_id,
            lokalizacja=nowa_lokalizacja_obj.nazwa_lokalizacji,
            status=nowy_status,
            uwagi=uwagi,
            imei_sim=urzadzenie_do_zmiany.aktualny_imei_sim
        )
        db.session.add(wpis_historii)
        
        db.session.commit()
        
        return redirect(url_for('index'))
    else:
        wszystkie_lokalizacje = Lokalizacja.query.all()
        wszyscy_uzytkownicy = Uzytkownik.query.all()
        return render_template('zmien_status.html', 
                               urzadzenie=urzadzenie_do_zmiany,
                               wszystkie_lokalizacje=wszystkie_lokalizacje,
                               wszyscy_uzytkownicy=wszyscy_uzytkownicy,
                               możliwe_statusy=MOZLIWE_STATUSY)
    


@app.route('/szczegoly/<int:urzadzenie_id>')
def szczegoly_urzadzenia(urzadzenie_id):
    urzadzenie = Urzadzenie.query.get_or_404(urzadzenie_id)
    return render_template('szczegoly.html', urzadzenie=urzadzenie)

@app.route('/dodaj', methods=['GET', 'POST'])
def dodaj_urzadzenie():
    # Definiujemy zmienną błędu na początku
    error = None
    if request.method == 'POST':
        # ... (pobieranie danych z formularza bez zmian) ...
        identyfikator = request.form.get('identyfikator_sprzetu')
        nazwa = request.form.get('nazwa')
        producent = request.form.get('producent')
        nr_seryjny = request.form.get('nr_seryjny')
        data_zakupu_str = request.form.get('data_zakupu')
        imei = request.form.get('aktualny_imei_sim')
        
        data_zakupu = None
        if data_zakupu_str:
            data_zakupu = datetime.strptime(data_zakupu_str, '%Y-%m-%d').date()

        nowe_urzadzenie = Urzadzenie(
            identyfikator_sprzetu=identyfikator,
            nazwa=nazwa,
            producent=producent,
            nr_seryjny=nr_seryjny,
            data_zakupu=data_zakupu,
            aktualny_imei_sim=imei,
            aktualna_lokalizacja='Magazyn Główny',
            aktualny_status='Dostępny'
        )
        
        try:
            db.session.add(nowe_urzadzenie)
            db.session.commit()
            return redirect(url_for('index'))
        except IntegrityError:
            # Jeśli wystąpi błąd unikalności, baza danych jest w złym stanie.
            # Musimy "odwołać" nieudaną transakcję.
            db.session.rollback()
            # Ustawiamy komunikat błędu, który wyświetlimy na stronie.
            error = "Błąd: Identyfikator sprzętu lub numer seryjny już istnieje w bazie danych."

    # Jeśli metoda to GET lub wystąpił błąd, wyświetlamy formularz.
    # Przekazujemy zmienną 'error' do szablonu.
    return render_template('dodaj_urzadzenie.html', error=error)

# --- URUCHOMIENIE APLIKACJI ---

if __name__ == '__main__':
    app.run(debug=True)