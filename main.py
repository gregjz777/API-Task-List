import datetime
import jwt
import uuid
from functools import wraps
from dateutil.relativedelta import relativedelta
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields, validate, validates, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS

SWAGGER_URL = '/api/docs'
API_URL = '/static/openapi.json'


swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Lista zadań"
    },)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kluczprywatny'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://baza:SwF7Qn:WLc+98L]@192.168.75.159:3306/baza_danych_projekt"
app.config['CORS_HEADERS'] = 'Content-Type'
app.register_blueprint(swaggerui_blueprint)
db = SQLAlchemy(app)

CORS(app, origins=["https://localhost:5173", "https://127.0.0.1:5000"])


# modele bazy danych
class Uzytkownik(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    publiczne_id = db.Column(db.String(36), unique=True, nullable=False)
    nazwa_uzytkownika = db.Column(db.String(30), unique=True, nullable=False)
    haslo_uzytkownika = db.Column(db.String(120), nullable=False)
    admin = db.Column(db.Boolean, nullable=False)

    #relacja
    zadania = db.relationship("Lista_zadan", backref="uzytkownik", lazy=True)

    #dodatkowe sprawdzenie wejscia
    __table_args__ = (db.CheckConstraint(admin >= 0, name="sprawdz_admin1"),
                      db.CheckConstraint(admin <= 1, name="sprawdz_admin2"),
                      db.CheckConstraint(
                          "publiczne_id RLIKE '[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'",
                            name="sprawdz_publiczne_id"),
                      db.CheckConstraint(
                          "nazwa_uzytkownika RLIKE '^[a-zA-ZĄąBbCcĆćDdEeĘęFfGgHhIiJjKkLlŁłMmNnŃńOoÓóPpRrSsŚśTtUuWwYyZzŹźŻż0-9:$]*$'",
                          name="sprawdz_nazwe_uzytkownika"),
                      db.CheckConstraint(
                          "haslo_uzytkownika RLIKE '^[a-zA-ZĄąBbCcĆćDdEeĘęFfGgHhIiJjKkLlŁłMmNnŃńOoÓóPpRrSsŚśTtUuWwYyZzŹźŻż0-9:$]*$'",
                          name="sprawdz_haslo_uzytkownika"))


class Lista_zadan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10), nullable=False)
    godzina = db.Column(db.String(5), nullable=False)
    tytul = db.Column(db.String(30), nullable=False)
    opis = db.Column(db.String(50), nullable=False)
    zakonczone = db.Column(db.Boolean, nullable=False)
    id_uzytkownika = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)

    #dodatkowe sprawdzenie wejscia
    __table_args__ = (db.CheckConstraint("data RLIKE '^[0-9]{2}[.]{1}[0-9]{2}[.]{1}[0-9]{4}$'", name="sprawdz_data"),
                      db.CheckConstraint("godzina RLIKE '^[0-9]{2}[:]{1}[0-9]{2}$'", name="sprawdz_godzina"),
                      db.CheckConstraint("tytul RLIKE '^[a-zA-ZĄąBbCcĆćDdEeĘęFfGgHhIiJjKkLlŁłMmNnŃńOoÓóPpRrSsŚśTtUuWwYyZzŹźŻż0-9[:space:]]*$'",
                                         name="sprawdz_tytul"),
                      db.CheckConstraint("opis RLIKE '^[a-zA-ZĄąBbCcĆćDdEeĘęFfGgHhIiJjKkLlŁłMmNnŃńOoÓóPpRrSsŚśTtUuWwYyZzŹźŻż0-9[:space:]]*$'",
                                         name="sprawdz_opis"),
                      db.CheckConstraint(zakonczone >= 0, name="sprawdz_zakonczone1"),
                      db.CheckConstraint(zakonczone <= 1, name="sprawdz_zakonczone2"))

#polecenie utworzenia bazy danych
with app.app_context():
    db.create_all()


# schematy do walidacji body JSON
class Dodawanie_nowego_uzytkownika_schemat(Schema):
    nazwa = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=30)
    )
    haslo = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=100)
    )


class Dodanie_nowego_wpisu_do_listy_zadan_schemat(Schema):
    data = fields.Str(
        required=True,
        validate=validate.Length(equal=10)
    )
    godzina = fields.Str(
        required=True,
        validate=validate.Length(equal=5)
    )
    tytul = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=30)
    )
    opis = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50)
    )

    @validates('data')
    def walidacja_tytul(self, wartosc):
        if len(wartosc.split(".")) != 3:
            raise ValidationError("Nieprawidlowy format daty!")

    @validates('godzina')
    def walidacja_godzina(self, wartosc):
        if len(wartosc.split(":")) != 2:
            raise ValidationError("Nieprawidlowy format godziny!")


class Wyswietlenie_harmonogramu_schemat(Schema):
    dzien = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=31)
    )
    miesiac = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=12)
    )
    rok = fields.Integer(
        required=True,
        validate=validate.Range(min=2023, max=9999)
    )
    zakres = fields.Str(
        required=True,
        validate=validate.OneOf(("dzien", "tydzien", "miesiac", "inny"))
    )
    dzien2 = fields.Integer(
        validate=validate.Range(min=1, max=31)
    )
    miesiac2 = fields.Integer(
        validate=validate.Range(min=1, max=12)
    )
    rok2 = fields.Integer(
        validate=validate.Range(min=2023, max=9999)
    )


def sprawdzanie_tokenu(f):
    @wraps(f)
    def dekorator(*args, **kwargs):
        token = None

        if "token-dostepu" in request.headers:
            token = request.headers["token-dostepu"]

        if not token:
            return jsonify({'wiadomosc': "Brak tokenu"}), 401

        try:
            dane = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            #sprawdzenie, czy token nie wygasl
            if datetime.datetime.fromisoformat(dane['wygasa']) < datetime.datetime.utcnow():
                return jsonify({'wiadomosc': "Token wygasl, zaloguj sie ponownie"}), 401
            else:
                aktualny_uzytkownik = Uzytkownik.query.filter_by(publiczne_id=dane['publiczne_id']).first()
        except:
            return jsonify({'wiadomosc': "Nieprawidlowy token, zaloguj sie ponownie"}), 401

        return f(aktualny_uzytkownik, *args, **kwargs)

    return dekorator


# metody
@app.route('/uzytkownik', methods=['POST'])
def utworz_nowego_uzytkownika():
    # pobranie danych z formularza
    dane = request.get_json()

    # walidacja danych z formularza
    bledy = Dodawanie_nowego_uzytkownika_schemat().validate(dane)
    if bledy:
        return bledy, 422

    # sprawdzenie, czy uzytkownik istnieje w bazie
    if Uzytkownik.query.filter_by(nazwa_uzytkownika=dane['nazwa']).first():
        return jsonify({'wiadomosc': "Nazwa uzytkownika zajeta; wybierz inna nazwe"}), 400

    # dodanie nowego uzytkownika do bazy
    zahaszowane_haslo = generate_password_hash(dane['haslo'], method='pbkdf2:sha256')
    nowy_uzytkownik = Uzytkownik(publiczne_id=str(uuid.uuid4()), nazwa_uzytkownika=dane['nazwa'],
                                 haslo_uzytkownika=zahaszowane_haslo, admin=False)
    db.session.add(nowy_uzytkownik)
    db.session.commit()
    return jsonify({'wiadomosc': "Nowy uzytkownik utworzony"}), 201


@app.route('/uzytkownik/logowanie', methods=['GET'])
def logowanie():
    # prosba o podanie danych logowania
    autoryzacja = request.authorization
    if not autoryzacja or not autoryzacja.username or not autoryzacja.password:
        return make_response("Nie mozna zweryfikowac", 401, {"autoryzacja-www": "Wymagane logowanie!"})

    # sprawdzanie, czy uzytkownik znajduje sie w bazie danych
    uzytkownik = Uzytkownik.query.filter_by(nazwa_uzytkownika=autoryzacja.username).first()
    if not uzytkownik:
        return make_response("Nie mozna zweryfikowac", 401, {"autoryzacja-www": "Nieprawidlowa nazwa uzytkownika!"})

    # generowanie tokenu, jeśli autoryzacja hasla pomyślna
    if check_password_hash(uzytkownik.haslo_uzytkownika, autoryzacja.password):
        token = jwt.encode({'publiczne_id': uzytkownik.publiczne_id,
                            'wygasa': (datetime.datetime.utcnow() + datetime.timedelta(minutes=30)).isoformat()},
                           app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token}), 200

    return make_response("Nie mozna zweryfikowac", 401, {"autoryzacja-www": "Nieprawidlowe haslo!"})


@app.route('/zadanie', methods=['POST'])
@sprawdzanie_tokenu
def dodaj_nowy_wpis(aktualny_uzytkownik):
    # pobranie danych z formularza
    dane = request.get_json()

    # walidacja danych z formularza
    bledy = Dodanie_nowego_wpisu_do_listy_zadan_schemat().validate(dane)
    if bledy:
        return bledy, 422

    # dodanie nowego wpisu do listy zadan
    nowe_zadanie = Lista_zadan(data=dane['data'], godzina=dane['godzina'], tytul=dane['tytul'], opis=dane['opis'],
                               zakonczone=False,
                               id_uzytkownika=aktualny_uzytkownik.id)
    db.session.add(nowe_zadanie)
    db.session.commit()
    return jsonify({'wiadomosc': "Nowe zadanie zostalo dodane do listy"}), 201


@app.route('/zadanie/<id_wybranego_zadania>', methods=['PUT'])
@sprawdzanie_tokenu
def edytuj_wpis(aktualny_uzytkownik, id_wybranego_zadania):
    # pobranie danych z formularza
    dane = request.get_json()

    # walidacja danych z formularza
    bledy = Dodanie_nowego_wpisu_do_listy_zadan_schemat().validate(dane)
    if bledy:
        return bledy, 422

    # znalezienie wpisu
    wpis = Lista_zadan.query.filter_by(id_uzytkownika=aktualny_uzytkownik.id, id=id_wybranego_zadania).first()

    if not wpis:
        return jsonify({"wiadomosc": "Nie znaleziono zadania!"}), 400

    # zaktualizowanie wpisu z listy zadan
    wpis.data = dane['data']
    wpis.godzina = dane['godzina']
    wpis.tytul = dane['tytul']
    wpis.opis = dane['opis']

    db.session.commit()
    return jsonify({'wiadomosc': "Zadanie zostalo zaktualizowane"}), 200


@app.route('/zadanie/<id_wybranego_zadania>', methods=['DELETE'])
@sprawdzanie_tokenu
def usun_wpis(aktualny_uzytkownik, id_wybranego_zadania):
    wpis = Lista_zadan.query.filter_by(id_uzytkownika=aktualny_uzytkownik.id, id=id_wybranego_zadania).first()
    if not wpis:
        return jsonify({"wiadomosc": "Nie znaleziono zadania!"}), 400

    db.session.delete(wpis)
    db.session.commit()
    return jsonify({"wiadomosc": "Zadanie zostało usuniete"}), 200


@app.route('/zadanie/<id_wybranego_zadania>', methods=['GET'])
@sprawdzanie_tokenu
def pobierz_jeden_wpis(aktualny_uzytkownik, id_wybranego_zadania):
    lista = Lista_zadan.query.filter_by(id_uzytkownika=aktualny_uzytkownik.id, id=id_wybranego_zadania)
    if lista.count() == 0:
        return jsonify({"wiadomosc": "Nie znaleziono zadania!"}), 400

    wyjscie = []
    for zadanie in lista:
        z = {'data': zadanie.data, 'godzina': zadanie.godzina, 'tytul': zadanie.tytul, 'opis': zadanie.opis, 'zakonczone': zadanie.zakonczone}
        wyjscie.append(z)

    return jsonify({"zadanie": wyjscie}), 200


@app.route('/zadanie/wszystkie', methods=['GET'])
@sprawdzanie_tokenu
def wyswietl_cala_liste(aktualny_uzytkownik):
    lista = Lista_zadan.query.filter_by(id_uzytkownika=aktualny_uzytkownik.id)
    if lista.count() == 0:
        return jsonify({"wiadomosc": "Nie znaleziono zadań dla danego użytkownika!"}), 400
    wyjscie = []
    for zadanie in lista:
        z = {'data': zadanie.data, 'godzina': zadanie.godzina, 'tytul': zadanie.tytul, 'opis': zadanie.opis, 'zakonczone': zadanie.zakonczone, 'id': zadanie.id}
        wyjscie.append(z)

    return jsonify({"zadania": wyjscie}), 200


@app.route('/zadanie/filtr', methods=['POST'])
@sprawdzanie_tokenu
def wyswietl_wyfiltrowana_liste(aktualny_uzytkownik):
    # pobranie danych z formularza
    dane = request.get_json()

    # walidacja danych z formularza
    bledy = Wyswietlenie_harmonogramu_schemat().validate(dane)
    if bledy:
        return bledy, 422

    # ustalenie dat krancowych
    data_formularz = datetime.date(dane["rok"], dane["miesiac"], dane["dzien"])
    pierwszy_dzien_tygodnia = data_formularz - datetime.timedelta(days=data_formularz.weekday())
    ostatni_dzien_tygodnia = pierwszy_dzien_tygodnia + datetime.timedelta(days=6)
    pierwszy_dzien_miesiaca = data_formularz.replace(day=1)
    ostatni_dzien_miesiaca = data_formularz.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
    data_formularz2 = datetime.date(dane["rok2"], dane["miesiac2"], dane["dzien2"])

    # pobranie zadan z bazy danych
    zakres_szukany = dane['zakres']
    if zakres_szukany == 'dzien':
        filtry = (
            Lista_zadan.data == data_formularz.strftime("%d.%m.%Y"),
            Lista_zadan.id_uzytkownika == aktualny_uzytkownik.id
        )
    elif zakres_szukany == 'tydzien':
        filtry = (
            Lista_zadan.data >= pierwszy_dzien_tygodnia.strftime("%d.%m.%Y"),
            Lista_zadan.data <= ostatni_dzien_tygodnia.strftime("%d.%m.%Y"),
            Lista_zadan.id_uzytkownika == aktualny_uzytkownik.id
        )
    elif zakres_szukany == 'miesiac':
        filtry = (
            Lista_zadan.data >= pierwszy_dzien_miesiaca.strftime("%d.%m.%Y"),
            Lista_zadan.data <= ostatni_dzien_miesiaca.strftime("%d.%m.%Y"),
            Lista_zadan.id_uzytkownika == aktualny_uzytkownik.id
        )
    elif zakres_szukany == 'inny':
        filtry = (
            Lista_zadan.data >= datetime.date(dane["rok"], dane["miesiac"], dane["dzien"]).strftime("%d.%m.%Y"),
            Lista_zadan.data <= datetime.date(dane["rok2"], dane["miesiac2"], dane["dzien2"]).strftime("%d.%m.%Y"),
            Lista_zadan.id_uzytkownika == aktualny_uzytkownik.id
        )
    else:
        return jsonify({"wiadomosc": "Wprowadz poprawny zakres dat!"})

    lista = Lista_zadan.query.filter_by(id_uzytkownika=aktualny_uzytkownik.id)
    if lista.count() == 0:
        return jsonify({"wiadomosc": "Nie znaleziono zadań w szukanym okresie czasu!"}), 400
    wyjscie = []
    for zadanie in lista:
        dzien = int(zadanie.data[0:2])
        miesiac = int(zadanie.data[3:5])
        rok = int(zadanie.data[6:10])
        data_z_listy = datetime.date(rok, miesiac, dzien)
        if zakres_szukany == "dzien":
            if data_formularz == data_z_listy:
                z = {'data': zadanie.data, 'godzina': zadanie.godzina, 'tytul': zadanie.tytul, 'opis': zadanie.opis,
                     'zakonczone': zadanie.zakonczone, 'id': zadanie.id}
                wyjscie.append(z)
        if zakres_szukany == "tydzien":
            if data_z_listy >= pierwszy_dzien_tygodnia and data_z_listy <= ostatni_dzien_tygodnia:
                z = {'data': zadanie.data, 'godzina': zadanie.godzina, 'tytul': zadanie.tytul, 'opis': zadanie.opis,
                     'zakonczone': zadanie.zakonczone, 'id': zadanie.id}
                wyjscie.append(z)
        if zakres_szukany == "miesiac":
            if data_z_listy >= pierwszy_dzien_miesiaca and data_z_listy <= ostatni_dzien_miesiaca:
                z = {'data': zadanie.data, 'godzina': zadanie.godzina, 'tytul': zadanie.tytul, 'opis': zadanie.opis,
                     'zakonczone': zadanie.zakonczone, 'id': zadanie.id}
                wyjscie.append(z)
        if zakres_szukany == "inny":
            data_p1 = datetime.date(dane["rok"], dane["miesiac"], dane["dzien"])
            data_p2 = datetime.date(dane["rok2"], dane["miesiac2"], dane["dzien2"])
            print(data_p1)
            print(data_p2)
            print(dzien, miesiac, rok)
            if data_z_listy >= data_p1 and data_z_listy <= data_p2:
                z = {'data': zadanie.data, 'godzina': zadanie.godzina, 'tytul': zadanie.tytul, 'opis': zadanie.opis,
                     'zakonczone': zadanie.zakonczone, 'id': zadanie.id}
                wyjscie.append(z)
                print(data_z_listy, pierwszy_dzien_tygodnia, ostatni_dzien_tygodnia)
    return jsonify({"zadania": wyjscie}), 200


@app.route('/zadanie/wykonaj/<id_wybranego_zadania>', methods=['PUT'])
@sprawdzanie_tokenu
def oznacz_wpis(aktualny_uzytkownik, id_wybranego_zadania):
    wpis = Lista_zadan.query.filter_by(id_uzytkownika=aktualny_uzytkownik.id, id=id_wybranego_zadania).first()
    if not wpis:
        return jsonify({"wiadomosc": "Nie znaleziono zadania!"}), 400

    if not wpis.zakonczone:
        wpis.zakonczone = True
        db.session.commit()
        return jsonify({"wiadomosc": "Zadanie zostało oznaczone jako wykonane"}), 200
    elif wpis.zakonczone:
        wpis.zakonczone = False
        db.session.commit()
        return jsonify({"wiadomosc": "Zadanie zostało oznaczone jako niewykonane"}), 200


# metody dla administratora
@app.route('/uzytkownik', methods=['GET'])
@sprawdzanie_tokenu
def wyswietl_wszystkich_uzytkownikow(aktualny_uzytkownik):
    if not aktualny_uzytkownik.admin:
        return jsonify({"wiadomosc": "Wymagane konto z uprawnieniami administratora"}), 401
    else:
        lista = Uzytkownik.query
        wyjscie = []
        for uzytkownik in lista:
            u = {'publiczne_id': uzytkownik.publiczne_id, 'nazwa': uzytkownik.nazwa_uzytkownika,  'admin': uzytkownik.admin}
            wyjscie.append(u)

        return jsonify({"uzytkownicy": wyjscie}), 200


@app.route('/uzytkownik/admin', methods=['POST'])
@sprawdzanie_tokenu
def dodaj_admina(aktualny_uzytkownik):
    if not aktualny_uzytkownik.admin:
        return jsonify({"wiadomosc": "Wymagane konto z uprawnieniami administratora"}), 401
    else:
        # pobranie danych z formularza
        dane = request.get_json()

        # walidacja danych z formularza
        bledy = Dodawanie_nowego_uzytkownika_schemat().validate(dane)
        if bledy:
            return bledy, 422

        # sprawdzenie, czy uzytkownik istnieje w bazie
        if Uzytkownik.query.filter_by(nazwa_uzytkownika=dane['nazwa']).first():
            return jsonify({'wiadomosc': "Nazwa uzytkownika zajeta; wybierz inna nazwe"}), 400

        # dodanie nowego uzytkownika do bazy
        zahaszowane_haslo = generate_password_hash(dane['haslo'], method='pbkdf2:sha256')
        nowy_uzytkownik = Uzytkownik(publiczne_id=str(uuid.uuid4()), nazwa_uzytkownika=dane['nazwa'],
                                     haslo_uzytkownika=zahaszowane_haslo, admin=True)
        db.session.add(nowy_uzytkownik)
        db.session.commit()
        return jsonify({'wiadomosc': "Nowy uzytkownik utworzony"}), 201


@app.route('/uzytkownik/<id_uzytkownik>', methods=['DELETE'])
@sprawdzanie_tokenu
def usun_uzytkownika(aktualny_uzytkownik, id_uzytkownik):
    if not aktualny_uzytkownik.admin:
        return jsonify({"wiadomosc": "Wymagane konto z uprawnieniami administratora"}), 401
    else:
        uzytkownik = Uzytkownik.query.filter_by(publiczne_id=id_uzytkownik).first()
        if not uzytkownik:
            return jsonify({"wiadomosc": "Nie znaleziono uzytkownika!"}), 400

        id_uzytkownik_normalne = uzytkownik.id
        lista = Lista_zadan.query.filter_by(id_uzytkownika=id_uzytkownik_normalne)
        for zadanie in lista:
            db.session.delete(zadanie)
        db.session.delete(uzytkownik)
        db.session.commit()
        return jsonify({"wiadomosc": "Uzytkownik został usuniety (wraz z jego zadaniami)"}), 200

context = ('cert.pem', 'key.pem')
if __name__ == "__main__":
    app.run(debug=False, ssl_context=context)
