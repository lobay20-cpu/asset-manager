# Importujemy potrzebne elementy z naszej głównej aplikacji
from app import app, db, Uzytkownik, Lokalizacja, Urzadzenie
from datetime import date

# "Wchodzimy" w kontekst naszej aplikacji, aby skrypt wiedział,
# z jaką bazą danych ma pracować.
with app.app_context():
    # KROK 1: Usuwamy wszystko, co mogło istnieć wcześniej, aby uniknąć duplikatów
    db.drop_all()
    db.create_all()

    # KROK 2: Tworzymy przykładowych użytkowników
    user1 = Uzytkownik(imie_nazwisko='Jan Kowalski')
    user2 = Uzytkownik(imie_nazwisko='Anna Nowak')
    user3 = Uzytkownik(imie_nazwisko='Piotr Wiśniewski')

    # KROK 3: Tworzymy przykładowe lokalizacje
    lok1 = Lokalizacja(nazwa_lokalizacji='Magazyn Główny', typ_lokalizacji='Magazyn')
    lok2 = Lokalizacja(nazwa_lokalizacji='Samochód SER-01', typ_lokalizacji='Pojazd')
    lok3 = Lokalizacja(nazwa_lokalizacji='Samochód SER-02', typ_lokalizacji='Pojazd')
    lok4 = Lokalizacja(nazwa_lokalizacji='Budowa "Nowe Osiedle"', typ_lokalizacji='Budowa')
    lok5 = Lokalizacja(nazwa_lokalizacji='Serwis Zewnętrzny', typ_lokalizacji='Serwis')

    # KROK 4: Tworzymy przykładowe urządzenia
    dev1 = Urzadzenie(
        identyfikator_sprzetu='RTR-SER-001',
        nazwa='Router Huawei E5577C',
        producent='Huawei',
        nr_seryjny='G4P0218528001234',
        data_zakupu=date(2024, 5, 20),
        aktualny_imei_sim='867591041234567',
        aktualna_lokalizacja='Magazyn Główny',
        aktualny_status='Dostępny'
    )

    dev2 = Urzadzenie(
        identyfikator_sprzetu='RTR-SER-002',
        nazwa='Router TP-Link M7200',
        producent='TP-Link',
        nr_seryjny='SN: 2216129005678',
        data_zakupu=date(2023, 11, 15),
        aktualny_imei_sim='867591041234890',
        aktualna_lokalizacja='Samochód SER-01',
        aktualny_status='W użyciu'
    )

    dev3 = Urzadzenie(
        identyfikator_sprzetu='RTR-PRO-003',
        nazwa='Router ZTE MF971V',
        producent='ZTE',
        nr_seryjny='ZTE4GMF971V1.0',
        data_zakupu=date(2024, 8, 1),
        aktualny_imei_sim='867591041235555',
        aktualna_lokalizacja='Magazyn Główny',
        aktualny_status='Dostępny',
        uwagi_serwisowe='Wymaga aktualizacji firmware'
    )

    # KROK 5: Dodajemy stworzone obiekty do "sesji" - czyli kolejki rzeczy do zapisania
    db.session.add_all([user1, user2, user3])
    db.session.add_all([lok1, lok2, lok3, lok4, lok5])
    db.session.add_all([dev1, dev2, dev3])

    # KROK 6: Zapisujemy wszystkie zmiany w bazie danych
    db.session.commit()

    print("Baza danych została wypełniona przykładowymi danymi!")