from app import app, db, Uzytkownik, Lokalizacja, Urzadzenie, Grupa
from datetime import date

with app.app_context():
    # KROK 1: Całkowite wyczyszczenie i stworzenie nowej struktury bazy
    db.drop_all()
    db.create_all()

    # KROK 2: Tworzymy użytkowników i lokalizacje (bez zmian)
    user1 = Uzytkownik(imie_nazwisko='Jan Kowalski')
    user2 = Uzytkownik(imie_nazwisko='Anna Nowak')
    db.session.add_all([user1, user2])

    lok1 = Lokalizacja(nazwa_lokalizacji='Magazyn Główny', typ_lokalizacji='Magazyn')
    lok2 = Lokalizacja(nazwa_lokalizacji='Samochód SER-01', typ_lokalizacji='Pojazd')
    db.session.add_all([lok1, lok2])
    
    # KROK 3: Tworzymy GRUPY URZĄDZEŃ, dodając nowe pole 'skrot'
    grupa_rtr = Grupa(nazwa_grupy='Routery Mobilne', skrot='RTR')
    grupa_pom = Grupa(nazwa_grupy='Przyrządy Pomiarowe', skrot='POM')
    db.session.add_all([grupa_rtr, grupa_pom])
    db.session.commit() # Commit, aby grupy dostały swoje ID

    # KROK 4: Tworzymy przykładowe urządzenia w NOWEJ STRUKTURZE
    
    # Pierwszy router (dostanie numer kolejny 1 w grupie RTR)
    dev1 = Urzadzenie(
        numer_ewidencyjny=1,
        grupa_id=grupa_rtr.id,
        nazwa='Router Huawei E5577C',
        producent='Huawei',
        nr_seryjny='G4P0218528001234',
        data_zakupu=date(2024, 5, 20),
        aktualny_imei_sim='867591041234567',
        aktualna_lokalizacja='Magazyn Główny',
        aktualny_status='Dostępny'
    )

    # Drugi router (dostanie numer kolejny 2 w grupie RTR)
    dev2 = Urzadzenie(
        numer_ewidencyjny=2,
        grupa_id=grupa_rtr.id,
        nazwa='Router TP-Link M7200',
        producent='TP-Link',
        nr_seryjny='SN: 2216129005678',
        data_zakupu=date(2023, 11, 15),
        aktualny_imei_sim='867591041234890',
        aktualna_lokalizacja='Samochód SER-01',
        aktualny_status='W użyciu'
    )
    
    # Pierwszy przyrząd pomiarowy (dostanie numer kolejny 1 w grupie POM)
    dev3 = Urzadzenie(
        numer_ewidencyjny=3,
        grupa_id=grupa_pom.id,
        nazwa='Miernik Sonel MPI-540',
        producent='Sonel',
        nr_seryjny='SN: 987654321',
        data_zakupu=date(2024, 8, 1),
        aktualny_imei_sim=None,
        aktualna_lokalizacja='Magazyn Główny',
        aktualny_status='Dostępny'
    )
    db.session.add_all([dev1, dev2, dev3])

    # KROK 5: Zapisujemy wszystkie zmiany
    db.session.commit()

    print("Baza danych została PRZEBUDOWANA pod automatyczną numerację i wypełniona danymi!")