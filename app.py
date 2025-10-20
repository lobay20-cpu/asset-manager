import os
import qrcode
import io
from flask import send_file # Ten jest bardzo ważny!
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from flask import Flask, render_template, request, redirect, url_for, flash

# --- KONFIGURACJA APLIKACJI ---

# Pobieramy ścieżkę do bieżącego folderu
basedir = os.path.abspath(os.path.dirname(__file__))

# Tworzymy instancję aplikacji Flask
app = Flask(__name__)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'twoj-bardzo-tajny-i-losowy-klucz' # W produkcji powinien to być prawdziwy losowy ciąg

# Konfigurujemy naszą aplikację, aby wiedziała, gdzie jest plik bazy danych.
# Stworzymy plik 'database.db' w głównym folderze projektu.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
# Wyłączamy niepotrzebne śledzenie modyfikacji, aby oszczędzić zasoby
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.route('/admin')
def panel_admina():
    wszystkie_grupy = Grupa.query.order_by(Grupa.nazwa_grupy).all()
    # --- NOWA LINIA ---
    wszyscy_uzytkownicy = Uzytkownik.query.order_by(Uzytkownik.imie_nazwisko).all()
    
    return render_template(
        'admin.html', 
        wszystkie_grupy=wszystkie_grupy, 
        # --- NOWA LINIA ---
        wszyscy_uzytkownicy=wszyscy_uzytkownicy
    )

# NOWA FUNKCJA DO DODAWANIA GRUPY
@app.route('/admin/dodaj-grupe', methods=['GET', 'POST'])
def dodaj_grupe():
    error = None
    if request.method == 'POST':
        # Pobieramy dane z formularza
        nazwa_grupy = request.form.get('nazwa_grupy')
        skrot = request.form.get('skrot')

        # Prosta walidacja, czy pola nie są puste
        if not nazwa_grupy or not skrot:
            error = "Oba pola (Nazwa grupy i Skrót) są wymagane."
        elif len(skrot) != 3:
            error = "Skrót musi składać się z dokładnie 3 liter."    
        else:
            try:
                
                # Tworzymy nowy obiekt Grupa
                nowa_grupa = Grupa(nazwa_grupy=nazwa_grupy, skrot=skrot.upper())
                
                db.session.add(nowa_grupa)
                db.session.commit()
                
                # Przekierowujemy z powrotem do panelu admina
                return redirect(url_for('panel_admina'))

            except IntegrityError:
                db.session.rollback()
                error = f"Błąd: Grupa o nazwie '{nazwa_grupy}' lub skrócie '{skrot.upper()}' już istnieje."

    # Dla metody GET lub w razie błędu, wyświetlamy formularz
    return render_template('dodaj_grupe.html', error=error)

# NOWA FUNKCJA DO EDYCJI GRUPY
@app.route('/admin/edytuj-grupe/<int:grupa_id>', methods=['GET', 'POST'])
def edytuj_grupe(grupa_id):
    # Znajdź grupę do edycji lub zwróć błąd 404
    grupa_do_edycji = Grupa.query.get_or_404(grupa_id)
    error = None

    if request.method == 'POST':
        # Pobierz nowe dane z formularza
        nowa_nazwa = request.form.get('nazwa_grupy')
        nowy_skrot = request.form.get('skrot')

        # Walidacja (podobna jak przy dodawaniu)
        if not nowa_nazwa or not nowy_skrot:
            error = "Oba pola są wymagane."
        elif len(nowy_skrot) != 3:
            error = "Skrót musi składać się z dokładnie 3 liter."
        else:
            try:
                # Zaktualizuj pola obiektu
                grupa_do_edycji.nazwa_grupy = nowa_nazwa
                grupa_do_edycji.skrot = nowy_skrot.upper()
                
                # Zapisz zmiany w bazie
                db.session.commit()
                
                # Wróć do panelu admina
                return redirect(url_for('panel_admina'))
            except IntegrityError:
                db.session.rollback()
                error = f"Błąd: Grupa o nazwie '{nowa_nazwa}' lub skrócie '{nowy_skrot.upper()}' już istnieje."

    # Dla metody GET, wyświetl formularz z istniejącymi danymi
    return render_template('edytuj_grupe.html', grupa=grupa_do_edycji, error=error)

# NOWA FUNKCJA DO BEZPIECZNEGO USUWANIA GRUPY
@app.route('/admin/usun-grupe/<int:grupa_id>')
def usun_grupe(grupa_id):
    # Znajdź grupę do usunięcia
    grupa_do_usuniecia = Grupa.query.get_or_404(grupa_id)
    
    # --- KLUCZOWE ZABEZPIECZENIE ---
    # Sprawdź, czy istnieją jakiekolwiek urządzenia w tej grupie
    if grupa_do_usuniecia.urzadzenia:
        # Jeśli tak, nie usuwaj. Wyświetl komunikat błędu.
        flash(f"Błąd: Nie można usunąć grupy '{grupa_do_usuniecia.nazwa_grupy}', ponieważ są do niej przypisane urządzenia.", 'error')
    else:
        # Jeśli nie ma urządzeń, można bezpiecznie usunąć.
        db.session.delete(grupa_do_usuniecia)
        db.session.commit()
        flash(f"Grupa '{grupa_do_usuniecia.nazwa_grupy}' została pomyślnie usunięta.", 'success')
        
    # Niezależnie od wyniku, wróć do panelu admina
    return redirect(url_for('panel_admina'))

# NOWA FUNKCJA DO GENEROWANIA KODU QR
@app.route('/qr-code/<int:urzadzenie_id>')
def generuj_qr(urzadzenie_id):
    # Krok 1: Upewnij się, że urządzenie o danym ID istnieje.
    urzadzenie = Urzadzenie.query.get_or_404(urzadzenie_id)

    # Krok 2: Wygeneruj pełny, docelowy URL do strony szczegółów.
    # Używamy `_external=True`, aby uzyskać pełny adres z domeną, np. http://127.0.0.1:5000/...
    url_do_zakodowania = url_for('zmien_status', urzadzenie_id=urzadzenie.id, _external=True)

    # Krok 3: Wygeneruj obrazek kodu QR w pamięci.
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_do_zakodowania)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Krok 4: Zapisz obrazek do "wirtualnego pliku" w pamięci RAM.
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0) # Przewiń "plik" na początek

    # Krok 5: Wyślij ten wirtualny plik do przeglądarki jako odpowiedź.
    return send_file(img_io, mimetype='image/png')

# NOWA FUNKCJA DO WYŚWIETLANIA STRONY Z KODEM QR
@app.route('/pokaz-qr/<int:urzadzenie_id>')
def pokaz_qr(urzadzenie_id):
    urzadzenie = Urzadzenie.query.get_or_404(urzadzenie_id)
    return render_template('pokaz_qr.html', urzadzenie=urzadzenie)

# NOWA FUNKCJA DO DODAWANIA UŻYTKOWNIKA
@app.route('/admin/dodaj-uzytkownika', methods=['GET', 'POST'])
def dodaj_uzytkownika():
    error = None
    if request.method == 'POST':
        imie_nazwisko = request.form.get('imie_nazwisko')

        if not imie_nazwisko:
            error = "Pole Imię i Nazwisko jest wymagane."
        else:
            try:
                nowy_uzytkownik = Uzytkownik(imie_nazwisko=imie_nazwisko)
                db.session.add(nowy_uzytkownik)
                db.session.commit()
                flash(f"Użytkownik '{imie_nazwisko}' został pomyślnie dodany.", 'success')
                return redirect(url_for('panel_admina'))
            except IntegrityError:
                db.session.rollback()
                error = f"Błąd: Użytkownik o imieniu '{imie_nazwisko}' już istnieje."

    return render_template('dodaj_uzytkownika.html', error=error)

# NOWA FUNKCJA DO EDYCJI UŻYTKOWNIKA
@app.route('/admin/edytuj-uzytkownika/<int:user_id>', methods=['GET', 'POST'])
def edytuj_uzytkownika(user_id):
    user_do_edycji = Uzytkownik.query.get_or_404(user_id)
    error = None

    if request.method == 'POST':
        nowe_imie = request.form.get('imie_nazwisko')
        if not nowe_imie:
            error = "Pole Imię i Nazwisko jest wymagane."
        else:
            try:
                user_do_edycji.imie_nazwisko = nowe_imie
                db.session.commit()
                flash(f"Nazwa użytkownika została zaktualizowana.", 'success')
                return redirect(url_for('panel_admina'))
            except IntegrityError:
                db.session.rollback()
                error = f"Błąd: Użytkownik o imieniu '{nowe_imie}' już istnieje."

    return render_template('edytuj_uzytkownika.html', user=user_do_edycji, error=error)

# NOWA FUNKCJA DO BEZPIECZNEGO USUWANIA UŻYTKOWNIKA
@app.route('/admin/zmien-status-uzytkownika/<int:user_id>')
def zmien_status_uzytkownika(user_id):
    user = Uzytkownik.query.get_or_404(user_id)
    # Odwracamy status: z aktywnego na nieaktywny i na odwrót
    user.is_active = not user.is_active
    db.session.commit()
    
    status_text = "aktywny" if user.is_active else "nieaktywny"
    flash(f"Status użytkownika '{user.imie_nazwisko}' został zmieniony na: {status_text}.", 'success')
    return redirect(url_for('panel_admina'))
    
    # --- KLUCZOWE ZABEZPIECZENIE ---
    # Sprawdzamy, czy ten użytkownik ma jakiekolwiek wpisy w historii zmian
    if user_do_usuniecia.historia_zmian:
        flash(f"Błąd: Nie można usunąć użytkownika '{user_do_usuniecia.imie_nazwisko}', ponieważ jest powiązany z historią zmian urządzeń.", 'error')
    else:
        db.session.delete(user_do_usuniecia)
        db.session.commit()
        flash(f"Użytkownik '{user_do_usuniecia.imie_nazwisko}' został pomyślnie usunięty.", 'success')
        
    return redirect(url_for('panel_admina'))

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

class Uzytkownik(db.Model):
    __tablename__ = 'uzytkownicy'
    id = db.Column(db.Integer, primary_key=True)
    imie_nazwisko = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    historia_zmian = db.relationship('HistoriaZmian', backref='uzytkownik', lazy=True)

class Lokalizacja(db.Model):
    __tablename__ = 'lokalizacje'
    id = db.Column(db.Integer, primary_key=True)
        # TYP LOKALIZACJI - to jest teraz nasz główny przełącznik
    nazwa_lokalizacji = db.Column(db.String(100), unique=True, nullable=False)
        # Nazwa miejsca (używane tylko, gdy typ to BUDOWA)
    typ_lokalizacji = db.Column(db.String(50), nullable=False)
        # Połączenie z użytkownikiem (używane tylko, gdy typ to OSOBA)

class Grupa(db.Model):
    __tablename__ = 'grupy'
    id = db.Column(db.Integer, primary_key=True)
    nazwa_grupy = db.Column(db.String(100), unique=True, nullable=False)
    skrot = db.Column(db.String(10), unique=True, nullable=False)
    urzadzenia = db.relationship('Urzadzenie', back_populates='grupa', lazy=True)

class Urzadzenie(db.Model):
    __tablename__ = 'urzadzenia'
    id = db.Column(db.Integer, primary_key=True)
    numer_ewidencyjny = db.Column(db.Integer, unique=True, nullable=False)
    nazwa = db.Column(db.String(100), nullable=False)
    producent = db.Column(db.String(100))
    nr_seryjny = db.Column(db.String(100), unique=True)
    data_zakupu = db.Column(db.Date)
    aktualny_imei_sim = db.Column(db.String(50))
        # --- UPEWNIJ SIĘ, ŻE TA LINIA WYGLĄDA DOKŁADNIE TAK ---
    aktualna_lokalizacja = db.Column(db.String(100)) # A NIE lokalizacja_id
    aktualny_status = db.Column(db.String(50))
    uwagi_serwisowe = db.Column(db.Text)
    grupa_id = db.Column(db.Integer, db.ForeignKey('grupy.id'), nullable=False)
    grupa = db.relationship('Grupa', back_populates='urzadzenia')
    
    historia = db.relationship('HistoriaZmian', backref='urzadzenie', lazy=True, cascade="all, delete-orphan")

    @property
    def wyswietlana_lokalizacja(self):
        if not self.lokalizacja:
            return "Brak przypisania"
        if self.lokalizacja.typ_lokalizacji == 'MAGAZYN':
            return "Magazyn Główny"
        if self.lokalizacja.typ_lokalizacji == 'BUDOWA':
            return self.lokalizacja.nazwa_budowy
        if self.lokalizacja.typ_lokalizacji == 'OSOBA':
            return self.lokalizacja.przypisany_uzytkownik.imie_nazwisko
        return "Nieznana lokalizacja"

    @property
    def identyfikator_sprzetu(self):
        return f"FR-{self.grupa.skrot}-{self.numer_ewidencyjny:03d}"
    
class HistoriaZmian(db.Model):
    __tablename__ = 'historia_zmian'
    id = db.Column(db.Integer, primary_key=True)
    data_zmiany = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lokalizacja = db.Column(db.String(100))
    status = db.Column(db.String(50))
    imei_sim = db.Column(db.String(50))
    uwagi = db.Column(db.Text)
    urzadzenie_id = db.Column(db.Integer, db.ForeignKey('urzadzenia.id'), nullable=False)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownicy.id'), nullable=False)

def generuj_nastepny_numer():
    # Znajdź ostatnie urządzenie, posortowane po numerze, niezależnie od grupy
    ostatnie_urzadzenie = Urzadzenie.query.order_by(Urzadzenie.numer_ewidencyjny.desc()).first()
    if ostatnie_urzadzenie:
        return ostatnie_urzadzenie.numer_ewidencyjny + 1
    else:
        return 1

@app.route('/')
def index():
    # Krok 1: Pobierz parametry filtrowania z adresu URL.
    wybrany_status = request.args.get('status')
    wybrana_grupa_id = request.args.get('grupa_id')

    # Krok 2: Zacznij budować zapytanie do bazy. Zaczynamy od "daj mi wszystko".
    query = Urzadzenie.query

    # Krok 3: Stopniowo dodawaj filtry do zapytania, jeśli zostały wybrane.
    if wybrany_status and wybrany_status != 'Wszystkie':
        query = query.filter(Urzadzenie.aktualny_status == wybrany_status)
    
    if wybrana_grupa_id and wybrana_grupa_id != 'Wszystkie':
        query = query.filter(Urzadzenie.grupa_id == wybrana_grupa_id)

    # Krok 4: Na samym końcu wykonaj zbudowane zapytanie.
    urzadzenia_do_wyswietlenia = query.order_by(Urzadzenie.id).all()
    
    # Krok 5: Przygotuj dane potrzebne do wyświetlenia formularza filtrów.
    wszystkie_grupy = Grupa.query.order_by(Grupa.nazwa_grupy).all()
    
    return render_template('index.html', 
                           urzadzenia=urzadzenia_do_wyswietlenia,
                           wszystkie_grupy=wszystkie_grupy,
                           wszystkie_statusy=['Wszystkie'] + MOZLIWE_STATUSY,
                           wybrany_status=wybrany_status or 'Wszystkie',
                           # POPRAWKA TUTAJ:
                           wybrana_grupa_id=int(wybrana_grupa_id) if wybrana_grupa_id and wybrana_grupa_id.isdigit() else 'Wszystkie')

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
        wszyscy_uzytkownicy = Uzytkownik.query.filter_by(is_active=True).order_by(Uzytkownik.imie_nazwisko).all()
        return render_template('zmien_status.html', 
                               urzadzenie=urzadzenie_do_zmiany,
                               wszystkie_lokalizacje=wszystkie_lokalizacje,
                               wszyscy_uzytkownicy=wszyscy_uzytkownicy,
                               możliwe_statusy=MOZLIWE_STATUSY)
    


@app.route('/szczegoly/<int:urzadzenie_id>')
def szczegoly_urzadzenia(urzadzenie_id):
    urzadzenie = Urzadzenie.query.get_or_404(urzadzenie_id)
    return render_template('szczegoly.html', urzadzenie=urzadzenie)

@app.route('/admin/dodaj-urzadzenie', methods=['GET', 'POST'])
def dodaj_urzadzenie():
    error = None
    if request.method == 'POST':
        # Pobieramy dane z formularza
        grupa_id = request.form.get('grupa')
        nazwa = request.form.get('nazwa')
        producent = request.form.get('producent')
        nr_seryjny = request.form.get('nr_seryjny')
        data_zakupu_str = request.form.get('data_zakupu')
        imei = request.form.get('aktualny_imei_sim')
        
        # Sprawdzamy, czy wybrano grupę
        if not grupa_id:
            error = "Błąd: Musisz wybrać grupę urządzenia."
        else:
            try:
                # --- TUTAJ DZIEJE SIĘ MAGIA ---
                # 1. Generujemy nowy numer KOLEJNY dla wybranej grupy
                nowy_numer_ewidencyjny = generuj_nastepny_numer()

                data_zakupu = None
                if data_zakupu_str:
                    data_zakupu = datetime.strptime(data_zakupu_str, '%Y-%m-%d').date()

                # 2. Tworzymy nowy obiekt z wygenerowanym numerem
                nowe_urzadzenie = Urzadzenie(
                    numer_ewidencyjny=nowy_numer_ewidencyjny, # Używamy nowej, poprawnej nazwy pola
                    grupa_id=grupa_id,
                    nazwa=nazwa,
                    producent=producent,
                    nr_seryjny=nr_seryjny,
                    data_zakupu=data_zakupu,
                    aktualny_imei_sim=imei,
                    aktualna_lokalizacja='Magazyn Główny',
                    aktualny_status='Dostępny'
                )
                
                db.session.add(nowe_urzadzenie)
                db.session.commit()
                
                # Przekierowujemy na stronę główną, aby zobaczyć nowy wpis
                return redirect(url_for('index'))
            
            except IntegrityError:
                db.session.rollback()
                # Ten błąd nie powinien się już zdarzyć, ale zostawiamy go jako zabezpieczenie
                error = "Błąd: Wystąpił problem z unikalnością numeru. Spróbuj ponownie."

    # Dla metody GET lub w razie błędu:
    wszystkie_grupy = Grupa.query.all()
    return render_template('dodaj_urzadzenie.html', error=error, wszystkie_grupy=wszystkie_grupy)

# NOWA FUNKCJA DO USUWANIA URZĄDZENIA
@app.route('/usun/<int:urzadzenie_id>')
def usun_urzadzenie(urzadzenie_id):
    # Krok 1: Znajdź w bazie urządzenie, które chcemy usunąć.
    # Jeśli nie istnieje, automatycznie zwróci błąd 404.
    urzadzenie_do_usuniecia = Urzadzenie.query.get_or_404(urzadzenie_id)
    
    # Krok 2: Dodaj znaleziony obiekt do "kolejki do usunięcia" w sesji bazy danych.
    db.session.delete(urzadzenie_do_usuniecia)
    
    # Krok 3: Zatwierdź zmiany - to jest moment fizycznego usunięcia danych.
    db.session.commit()
    
    # Krok 4: Przekieruj użytkownika z powrotem na stronę główną.
    return redirect(url_for('index'))

# NOWA FUNKCJA DO EDYCJI URZĄDZENIA
@app.route('/edytuj/<int:urzadzenie_id>', methods=['GET', 'POST'])
def edytuj_urzadzenie(urzadzenie_id):
    # Krok 1: Pobierz z bazy urządzenie, które chcemy edytować.
    urzadzenie_do_edycji = Urzadzenie.query.get_or_404(urzadzenie_id)
    error = None

    if request.method == 'POST':
        # Krok 2: Jeśli formularz został wysłany, pobierz nowe dane.
        try:
            urzadzenie_do_edycji.grupa_id = int(request.form.get('grupa'))
            urzadzenie_do_edycji.nazwa = request.form.get('nazwa')
            urzadzenie_do_edycji.producent = request.form.get('producent')
            urzadzenie_do_edycji.aktualny_imei_sim = request.form.get('aktualny_imei_sim')
            
            db.session.commit()

            # Krok 3: Zapisz zmiany w bazie.
            return redirect(url_for('szczegoly_urzadzenia', urzadzenie_id=urzadzenie_id))
            
            # Krok 4: Przekieruj na stronę szczegółów tego urządzenia.
            return redirect(url_for('szczegoly_urzadzenia', urzadzenie_id=urzadzenie_id))
        
        except IntegrityError:
            # Obsługa błędu, jeśli nowy identyfikator lub nr seryjny już istnieje.
            db.session.rollback()
            error = "Błąd: Wystąpił problem z unikalnością danych (np. numer seryjny już istnieje)."

    # Krok 5: Jeśli metoda to GET (lub wystąpił błąd), wyświetl formularz
    # z już wypełnionymi danymi urządzenia.
    wszystkie_grupy = Grupa.query.all()
    return render_template('edytuj_urzadzenie.html', urzadzenie=urzadzenie_do_edycji, error=error, wszystkie_grupy=wszystkie_grupy)

# --- URUCHOMIENIE APLIKACJI ---

if __name__ == '__main__':
    app.run(debug=True)