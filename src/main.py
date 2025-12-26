
from flask import Flask,render_template,redirect,url_for,request,session
from extensions import db
from flask_migrate import Migrate
from sqlalchemy import text, inspect

app = Flask(__name__)
app.config['SECRET_KEY'] = "RAF2021-2022"
app.config['SQLALCHEMY_DATABASE_URI'] = ('mssql+pyodbc://@localhost/stom_ordinacija?''driver=ODBC+Driver+17+for+SQL+Server')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

migrate = Migrate(app, db)

from models import *

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/test_db')
def test_db():
    try:
        result = db.session.execute(text("SELECT 1")).scalar()
        if result == 1:
            return "Konekcija sa bazom je uspešna!"
        else:
            return "Konekcija nije uspela."
    except Exception as e:
        return f"Došlo je do greške: {e}"


@app.route('/fetch_all_korisnici')
def fetch_all_korisnici():
    korisnici = Korisnik.query.all()
    return render_template("korisnici.html", korisnici=korisnici)

@app.route('/login', methods=['GET', 'POST'])
def login():
	korisnici = Korisnik.query.all()
    
	if request.method == "GET":
		return render_template("login.html")
	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']
	
		if username == "" or password == "":
			return render_template("login.html", greska = "Sva polja moraju biti popunjena!")
        
		for k in korisnici:
			if k.username == username and k.password == password:
				session['user_id'] = k.idKorisnici
				session['username'] = k.username
				session['role'] = k.uloga

				return redirect(url_for('pocetna_stranica'))
		
		return render_template("login.html", greska = "Neadekvatni kredencijali za login!")
			
@app.route('/pocetna_stranica')
def pocetna_stranica():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    termini = []

    if session['role'] == 'pacijent':
        pacijent = Pacijent.query.filter_by(
            korisnikID=session['user_id']
        ).first()

        termini = Termin.query.filter_by(
            pacijentID=pacijent.idPacijent
        ).order_by(Termin.datum.asc()).all()

    elif session['role'] == 'stomatolog':
        stomatolog = Stomatolog.query.filter_by(
            korisnikID=session['user_id']
        ).first()

        termini = Termin.query.filter(
            Termin.stomatologID == stomatolog.idStomatolog,
            Termin.status == 'zakazan'   # 👈 KLJUČNA LINIJA
        ).order_by(Termin.datum.asc()).all()

    return render_template(
        "pocetna_stranica.html",
        user=session['username'],
        role=session['role'],
        id=session['user_id'],
        termini=termini
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == "GET":
		return render_template('register.html')
	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']
		password_again = request.form['password_again']
		ime = request.form['ime']
		prezime = request.form['prezime']
		broj_telefona = request.form['broj_telefona']
		datum_rodjenja = request.form['datum_rodjenja']
		adresa = request.form['adresa']
		grad = request.form['grad']
		alergije = request.form['alergije']

		if username == "" or password == "" or password_again == "" or ime == "" or prezime == "" or broj_telefona == "" or datum_rodjenja == "" or adresa == "" or grad == "":
			return render_template('register.html', greska = "Sva polja (osim polja alergije) moraju biti popunjena!")

		if password != password_again:
			return render_template('register.html', greska = "Sifre se ne poklapaju!")
		
		if any(char.isdigit() for char in ime):
			return render_template('register.html', greska = "Polje ime ne sme sadrzati brojeve!")

		if any(char.isdigit() for char in prezime):
			return render_template('register.html', greska = "Polje prezime ne sme sadrzati brojeve!")
		
		novi_korisnik = Korisnik(
			username = username,
			password = password,
			uloga = 'pacijent'
		)
		db.session.add(novi_korisnik)
		db.session.commit()

		novi_pacijent = Pacijent(
			ime = ime,
			prezime = prezime,
			broj_telefona = broj_telefona,
			datum_rodjenja = datum_rodjenja,
			adresa = adresa,
			grad = grad,
			alergije = alergije,
			korisnikID = novi_korisnik.idKorisnici
		)
		db.session.add(novi_pacijent)
		db.session.commit()

		

		return redirect(url_for('success'))

@app.route('/success')
def success():
	return render_template("success.html")

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for("login"))

@app.route('/zakazi_termin', methods=['GET', 'POST'])
def zakazi_termin():
	if 'user_id' not in session or session['role'] != 'pacijent':
		return redirect(url_for('login'))
	
	pacijent = Pacijent.query.filter_by(korisnikID=session['user_id']).first()
	stomatolozi = Stomatolog.query.all()
	
	if request.method == 'GET':
		return render_template(
            'zakazi_termin.html',
            stomatolozi=stomatolozi,
			zauzeti_sati = []
        )
	
	if request.method == 'POST':
		datum_str = request.form['datum']
		vreme = int(request.form['vreme'])
		stomatolog_id = request.form['stomatolog']

		datum_obj = datetime.strptime(datum_str, "%Y-%m-%d")
		pocetak_dana = datum_obj.replace(hour=0, minute=0, second=0)
		kraj_dana = datum_obj.replace(hour=23, minute=59, second=59)

		termini_na_datum = Termin.query.filter(
        	Termin.stomatologID==stomatolog_id,
        	Termin.status == 'zakazan',
    		Termin.datum >= pocetak_dana,
    		Termin.datum <= kraj_dana
    	).all()

		zauzeti_sati = [t.datum.hour for t in termini_na_datum]

		if vreme in zauzeti_sati:
			return render_template(
            	'zakazi_termin.html',
            	stomatolozi=stomatolozi,
            	greska="Izabrani termin je već zauzet. Molimo izaberite drugi termin.",
            	zauzeti_sati=zauzeti_sati
        	)

		datum = datum_obj.replace(hour=vreme, minute=0, second=0)
		
		
		novi_termin = Termin(
        	datum=datum,
        	status='zakazan',
        	pacijentID=pacijent.idPacijent,
        	stomatologID=stomatolog_id
    	)

		db.session.add(novi_termin)
		db.session.commit()

		return redirect(url_for('pocetna_stranica'))


@app.route('/otkazi_termin/<int:termin_id>', methods=['POST'])
def otkazi_termin(termin_id):
	if 'user_id' not in session or session['role'] != 'pacijent':
		return redirect(url_for('login'))
	
	pacijent = Pacijent.query.filter_by(korisnikID=session['user_id']).first()

	termin = Termin.query.filter_by(
        idTermin=termin_id,
        pacijentID=pacijent.idPacijent
    ).first()

	if not termin:
		return redirect(url_for('pocetna_stranica'))
	
	termin.status = 'otkazan'
	db.session.commit()

	return redirect(url_for('pocetna_stranica'))

@app.route('/stomatolog/otkazi_termin/<int:termin_id>', methods=['POST'])
def stomatolog_otkazi_termin(termin_id):
    if 'user_id' not in session or session['role'] != 'stomatolog':
        return redirect(url_for('login'))

    termin = Termin.query.get(termin_id)

    if not termin:
        return redirect(url_for('pocetna_stranica'))

    termin.status = 'otkazan'
    db.session.commit()

    return redirect(url_for('pocetna_stranica'))

@app.route('/profil')
def profil():
	if 'user_id' not in session:
		return redirect(url_for('login'))
	
	korisnik = Korisnik.query.get(session['user_id'])

	pacijent = None
	stomatolog = None
	sestra = None

	if not korisnik:
		return redirect(url_for('login'))
	
	if korisnik.uloga == 'pacijent':
		pacijent = Pacijent.query.filter_by(korisnikID=korisnik.idKorisnici).first()
	
	elif korisnik.uloga == 'stomatolog':
		stomatolog = Stomatolog.query.filter_by(korisnikID=korisnik.idKorisnici).first()

	elif korisnik.uloga == 'sestra':
		sestra = StomatoloskaSestra.query.filter_by(korisnikID=korisnik.idKorisnici).first()
	
	return render_template(
        'profil.html',
        korisnik=korisnik,
        pacijent=pacijent,
        stomatolog=stomatolog,
        sestra=sestra
    )

@app.route('/izmeni_profil', methods=['GET', 'POST'])
def izmeni_profil():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    korisnik = Korisnik.query.get(session['user_id'])
    if not korisnik:
        return redirect(url_for('login'))

    if korisnik.uloga == 'pacijent':
        spec = Pacijent.query.filter_by(korisnikID=korisnik.idKorisnici).first()
    elif korisnik.uloga == 'stomatolog':
        spec = Stomatolog.query.filter_by(korisnikID=korisnik.idKorisnici).first()
    elif korisnik.uloga == 'sestra':
        spec = StomatoloskaSestra.query.filter_by(korisnikID=korisnik.idKorisnici).first()
    else:
        spec = None

    if request.method == 'POST':
        # Osnovni podaci
        korisnik.username = request.form['username']
        if 'password' in request.form and request.form['password']:
            korisnik.password = request.form['password']

        # Podaci specifični za ulogu
        if spec:
            spec.ime = request.form.get('ime', spec.ime)
            spec.prezime = request.form.get('prezime', spec.prezime)
            if korisnik.uloga == 'pacijent':
                spec.broj_telefona = request.form.get('broj_telefona', spec.broj_telefona)
                datum_rodjenja = request.form.get('datum_rodjenja')
                if datum_rodjenja:
                    spec.datum_rodjenja = datetime.strptime(datum_rodjenja, "%Y-%m-%d")
                spec.adresa = request.form.get('adresa', spec.adresa)
                spec.grad = request.form.get('grad', spec.grad)
                spec.alergije = request.form.get('alergije', spec.alergije)

        db.session.commit()
        return redirect(url_for('profil'))

    return render_template('izmeni_profil.html', korisnik=korisnik, spec=spec)

	
@app.route('/cenovnik')
def cenovnik():
	return render_template('cenovnik.html',user=session['username'], role=session['role'])

@app.route('/zavrsi_termin/<int:termin_id>', methods=['GET', 'POST'])
def zavrsi_termin(termin_id):
    if 'user_id' not in session or session['role'] != 'stomatolog':
        return redirect(url_for('login'))

    termin = Termin.query.get(termin_id)
    if not termin or termin.status != 'zakazan':
        return redirect(url_for('pocetna_stranica'))

    # Dohvati sve sestre da ih prikažemo u dropdown-u
    sestre = StomatoloskaSestra.query.all()

    if request.method == 'GET':
        return render_template('zavrsi_termin.html', termin=termin, sestre=sestre)

    if request.method == 'POST':
        naziv = request.form['naziv']
        opis = request.form['opis']
        cena = request.form['cena']
        sestra_id = request.form['sestra']  # ID iz dropdown-a

        if sestra_id == '' or sestra_id is None:
            sestra_id = None
        else:
            sestra_id = int(sestra_id)

        nova_intervencija = Intervencija(
            naziv=naziv,
            opis=opis,
            cena=cena,
            terminID=termin.idTermin,
            stomatologID=termin.stomatologID,
            stomatoloskaSestraID=sestra_id
        )

        db.session.add(nova_intervencija)
        termin.status = 'realizovan'
        db.session.commit()

        return redirect(url_for('pocetna_stranica'))



if __name__ == '__main__':
    app.run(debug=True)
    

