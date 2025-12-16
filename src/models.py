from extensions import db
from datetime import datetime
from sqlalchemy.sql import func

# -------------------------
# Tabela Korisnik
# -------------------------
class Korisnik(db.Model):
    __tablename__ = 'korisnici'

    idKorisnici = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    uloga = db.Column(db.String(20), nullable=False)  # 'stomatolog', 'stom_sestra', 'pacijent'

    pacijenti = db.relationship('Pacijent', backref='korisnik', lazy=True)
    stomatolozi = db.relationship('Stomatolog', backref='korisnik', lazy=True)
    stom_sestre = db.relationship('StomatoloskaSestra', backref='korisnik', lazy=True)


# -------------------------
# Tabela Pacijent
# -------------------------
class Pacijent(db.Model):
    __tablename__ = 'pacijent'

    idPacijent = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(50), nullable=False)
    prezime = db.Column(db.String(50), nullable=False)
    broj_telefona = db.Column(db.String(20))
    datum_rodjenja = db.Column(db.Date, nullable=False)
    adresa = db.Column(db.String(100))
    grad = db.Column(db.String(50))
    alergije = db.Column(db.String(100))
    korisnikID = db.Column(db.Integer, db.ForeignKey('korisnici.idKorisnici'))

    termini = db.relationship('Termin', backref='pacijent', lazy=True)
    racuni = db.relationship('Racun', backref='pacijent', lazy=True)
    med_dokumentacije = db.relationship('MedicinskaDokumentacija', backref='pacijent', lazy=True, uselist=False)


# -------------------------
# Tabela Stomatolog
# -------------------------
class Stomatolog(db.Model):
    __tablename__ = 'stomatolog'

    idStomatolog = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(50), nullable=False)
    prezime = db.Column(db.String(50), nullable=False)
    broj_telefona = db.Column(db.String(20))
    korisnikID = db.Column(db.Integer, db.ForeignKey('korisnici.idKorisnici'))

    termini = db.relationship('Termin', backref='stomatolog', lazy=True)
    intervencije = db.relationship('Intervencija', backref='stomatolog', lazy=True)


# -------------------------
# Tabela Stomatoloska Sestra
# -------------------------
class StomatoloskaSestra(db.Model):
    __tablename__ = 'stomatoloska_sestra'

    idStomatoloskaSestra = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(50), nullable=False)
    prezime = db.Column(db.String(50), nullable=False)
    broj_telefona = db.Column(db.String(20))
    korisnikID = db.Column(db.Integer, db.ForeignKey('korisnici.idKorisnici'))

    termini = db.relationship('Termin', backref='stomatoloska_sestra', lazy=True)
    intervencije = db.relationship('Intervencija', backref='stomatoloska_sestra', lazy=True)
    racuni = db.relationship('Racun', backref='stomatoloska_sestra', lazy=True)


# -------------------------
# Tabela Termin
# -------------------------
class Termin(db.Model):
    __tablename__ = 'termin'

    idTermin = db.Column(db.Integer, primary_key=True)
    datum = db.Column(db.DateTime, nullable=False, server_default=func.getdate())
    status = db.Column(db.String(20), nullable=False)  # 'zakazan', 'realizovan', 'otkazan'
    pacijentID = db.Column(db.Integer, db.ForeignKey('pacijent.idPacijent'))
    stomatologID = db.Column(db.Integer, db.ForeignKey('stomatolog.idStomatolog'))
    stomatoloskaSestraID = db.Column(db.Integer, db.ForeignKey('stomatoloska_sestra.idStomatoloskaSestra'))

    intervencije = db.relationship('Intervencija', backref='termin', lazy=True)


# -------------------------
# Tabela Intervencija
# -------------------------
class Intervencija(db.Model):
    __tablename__ = 'intervencija'

    idIntervencija = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(50), nullable=False)
    opis = db.Column(db.String(200))
    cena = db.Column(db.Numeric(10, 2))
    terminID = db.Column(db.Integer, db.ForeignKey('termin.idTermin'))
    stomatologID = db.Column(db.Integer, db.ForeignKey('stomatolog.idStomatolog'))
    stomatoloskaSestraID = db.Column(db.Integer, db.ForeignKey('stomatoloska_sestra.idStomatoloskaSestra'))

    med_dokumentacije = db.relationship('MedicinskaDokumentacija', backref='intervencija', lazy=True)
    racuni = db.relationship('Racun', backref='intervencija', lazy=True)


# -------------------------
# Tabela Medicinska Dokumentacija
# -------------------------
class MedicinskaDokumentacija(db.Model):
    __tablename__ = 'medicinska_dokumentacija'

    idMedicinska_dokumentacija = db.Column(db.Integer, primary_key=True)
    opis = db.Column(db.String(200))
    datum_upisa = db.Column(db.DateTime, nullable=False, server_default=func.getdate())
    pacijentID = db.Column(db.Integer, db.ForeignKey('pacijent.idPacijent'), unique=True)
    intervencijaID = db.Column(db.Integer, db.ForeignKey('intervencija.idIntervencija'))


# -------------------------
# Tabela Nacin Placanja
# -------------------------
class NacinPlacanja(db.Model):
    __tablename__ = 'nacin_placanja'

    idNacinPlacanja = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(20), nullable=False, server_default='kes')  # 'kes', 'kartica'

    racuni = db.relationship('Racun', backref='nacin_placanja', lazy=True)


# -------------------------
# Tabela Racun
# -------------------------
class Racun(db.Model):
    __tablename__ = 'racun'

    idRacun = db.Column(db.Integer, primary_key=True)
    datum_izdavanja = db.Column(db.DateTime, nullable=False, server_default=func.getdate())
    iznos = db.Column(db.Numeric(10, 2))
    pacijentID = db.Column(db.Integer, db.ForeignKey('pacijent.idPacijent'))
    stomatoloskaSestraID = db.Column(db.Integer, db.ForeignKey('stomatoloska_sestra.idStomatoloskaSestra'))
    intervencijaID = db.Column(db.Integer, db.ForeignKey('intervencija.idIntervencija'))
    nacinPlacanjaID = db.Column(db.Integer, db.ForeignKey('nacin_placanja.idNacinPlacanja'))
