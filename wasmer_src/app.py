"""
Main Flask application for board game lending system.
"""
import os
import sys

if os.path.isdir('/site-packages'):
    sys.path.insert(0, '/site-packages')

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from models import db, Gioco, Socio, Prestito, GiocoRuolo
from forms import GiocoForm, PrestitoForm, SocioForm, GiocoRuoloForm
from io import BytesIO
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import requests
from xml.etree import ElementTree

app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))
database_path = os.environ.get('DATABASE_PATH', os.path.join(base_dir, 'instance', 'prestiti.db'))
database_dir = os.path.dirname(database_path)
if database_dir:
    os.makedirs(database_dir, exist_ok=True)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['AUTH_USERNAME'] = os.environ.get('AUTH_USERNAME', 'admin')
app.config['AUTH_PASSWORD_HASH'] = os.environ.get('AUTH_PASSWORD_HASH', '')
if not app.config['AUTH_PASSWORD_HASH'] and os.environ.get('AUTH_PASSWORD'):
    app.config['AUTH_PASSWORD_HASH'] = generate_password_hash(os.environ['AUTH_PASSWORD'])
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', '').lower() == 'true'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', f'sqlite:///{database_path}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BGG_API_TOKEN'] = os.environ.get('BGG_API_TOKEN', '').strip()

db.init_app(app)


# Initialize database
with app.app_context():
    db.create_all()


@app.before_request
def require_login():
    """Protect every page except authentication and static files."""
    if request.endpoint in {'login', 'static'}:
        return None
    if not session.get('authenticated'):
        return redirect(url_for('login', next=request.full_path))
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate an operator with the configured password hash."""
    if session.get('authenticated'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_hash = app.config['AUTH_PASSWORD_HASH']

        if username == app.config['AUTH_USERNAME'] and password_hash and check_password_hash(password_hash, password):
            session.clear()
            session.permanent = True
            session['authenticated'] = True
            next_url = request.form.get('next', '')
            if next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect(url_for('index'))

        flash('Credenziali non valide.', 'error')

    return render_template('login.html', next_url=request.args.get('next', ''))


@app.route('/logout', methods=['POST'])
def logout():
    """End the current authenticated session."""
    session.clear()
    return redirect(url_for('login'))


# ============= ROUTES: HOME & DASHBOARD =============

@app.route('/')
def index():
    """Dashboard with overview statistics."""
    prestiti_attivi = Prestito.query.filter_by(data_restituzione_effettiva=None).count()
    giochi_disponibili = Gioco.query.filter_by(disponibile=True).count()
    totale_giochi = Gioco.query.count()
    totale_soci = Socio.query.count()
    totale_prestiti = Prestito.query.count()
    
    # Recent active loans
    ultimi_prestiti = Prestito.query.filter_by(data_restituzione_effettiva=None)\
        .order_by(desc(Prestito.data_prestito)).limit(5).all()
    
    return render_template('index.html',
                         prestiti_attivi=prestiti_attivi,
                         giochi_disponibili=giochi_disponibili,
                         totale_giochi=totale_giochi,
                         totale_soci=totale_soci,
                         totale_prestiti=totale_prestiti,
                         ultimi_prestiti=ultimi_prestiti)


# ============= ROUTES: GIOCHI (CRUD) =============

@app.route('/giochi')
def giochi_lista():
    """List all games with optional search filter."""
    search = request.args.get('search', '')
    disponibili_only = request.args.get('disponibili', '')
    
    query = Gioco.query
    
    if search:
        query = query.filter(
            (Gioco.titolo.ilike(f'%{search}%')) |
            (Gioco.editore.ilike(f'%{search}%'))
        )
    
    if disponibili_only == 'true':
        query = query.filter_by(disponibile=True)
    
    giochi = query.order_by(Gioco.titolo).all()
    
    # Get all soci for filter dropdown
    soci = Socio.query.order_by(Socio.cognome, Socio.nome).all()
    
    return render_template('giochi_lista.html', giochi=giochi, search=search, soci=soci)


@app.route('/giochi/nuovo', methods=['GET', 'POST'])
def giochi_nuovo():
    """Create a new game."""
    form = GiocoForm()
    
    # Populate soci choices
    form.soci_ids.choices = [(s.id, s.nome_completo) for s in Socio.query.order_by(Socio.cognome, Socio.nome).all()]
    
    if form.validate_on_submit():
        gioco = Gioco(
            titolo=form.titolo.data,
            editore=form.editore.data,
            anno=form.anno.data,
            numero_giocatori=form.numero_giocatori.data,
            durata=form.durata.data,
            difficolta=form.difficolta.data,
            immagine_path=form.immagine_path.data,
            disponibile=form.disponibile.data
        )
        
        # Add selected soci
        for socio_id in form.soci_ids.data:
            socio = Socio.query.get(socio_id)
            if socio:
                gioco.soci.append(socio)
        
        db.session.add(gioco)
        db.session.commit()
        return redirect(url_for('giochi_lista'))
    
    return render_template('giochi_form.html', form=form, title='Nuovo Gioco', ha_prestito_attivo=None)


@app.route('/giochi/<int:id>/modifica', methods=['GET', 'POST'])
def giochi_modifica(id):
    """Edit an existing game."""
    gioco = Gioco.query.get_or_404(id)
    form = GiocoForm(obj=gioco)
    
    # Populate soci choices
    form.soci_ids.choices = [(s.id, s.nome_completo) for s in Socio.query.order_by(Socio.cognome, Socio.nome).all()]
    
    if request.method == 'GET':
        # Pre-select current soci
        form.soci_ids.data = [s.id for s in gioco.soci]
    
    if form.validate_on_submit():
        # Check if trying to mark as available while there's an active loan
        ha_prestito_attivo = Prestito.query.filter_by(gioco_id=gioco.id, data_restituzione_effettiva=None).first()
        
        if ha_prestito_attivo and form.disponibile.data:
            flash(f'Impossibile rendere disponibile il gioco "{gioco.titolo}": è attualmente in prestito!', 'error')
            return render_template('giochi_form.html', form=form, title='Modifica Gioco', gioco=gioco)
        
        gioco.titolo = form.titolo.data
        gioco.editore = form.editore.data
        gioco.anno = form.anno.data
        gioco.numero_giocatori = form.numero_giocatori.data
        gioco.durata = form.durata.data
        gioco.difficolta = form.difficolta.data
        gioco.immagine_path = form.immagine_path.data
        gioco.disponibile = form.disponibile.data
        
        # Update soci relationship
        gioco.soci.clear()
        for socio_id in form.soci_ids.data:
            socio = Socio.query.get(socio_id)
            if socio:
                gioco.soci.append(socio)
        
        db.session.commit()
        return redirect(url_for('giochi_lista'))
    
    # Check if game has active loan
    ha_prestito_attivo = Prestito.query.filter_by(gioco_id=gioco.id, data_restituzione_effettiva=None).first()
    
    return render_template('giochi_form.html', form=form, title='Modifica Gioco', gioco=gioco, ha_prestito_attivo=ha_prestito_attivo)


@app.route('/giochi/<int:id>/elimina', methods=['POST'])
def giochi_elimina(id):
    """Delete a game."""
    gioco = Gioco.query.get_or_404(id)
    
    # Check if game has active loans
    prestiti_attivi = Prestito.query.filter_by(gioco_id=id, data_restituzione_effettiva=None).count()
    if prestiti_attivi > 0:
        flash(f'Impossibile eliminare "{gioco.titolo}": ci sono prestiti attivi!', 'error')
        return redirect(url_for('giochi_lista'))
    
    titolo = gioco.titolo
    db.session.delete(gioco)
    db.session.commit()
    return redirect(url_for('giochi_lista'))


# ============= ROUTES: SOCI (CRUD) =============

@app.route('/soci')
def soci_lista():
    """List all club members with optional search filter."""
    search = request.args.get('search', '')
    
    query = Socio.query
    
    if search:
        query = query.filter(
            (Socio.nome.ilike(f'%{search}%')) |
            (Socio.cognome.ilike(f'%{search}%'))
        )
    
    soci = query.order_by(Socio.cognome, Socio.nome).all()
    return render_template('soci_lista.html', soci=soci, search=search)


@app.route('/soci/nuovo', methods=['GET', 'POST'])
def soci_nuovo():
    """Create a new club member."""
    form = SocioForm()
    
    if form.validate_on_submit():
        socio = Socio(
            nome=form.nome.data,
            cognome=form.cognome.data,
            email=form.email.data,
            telefono=form.telefono.data,
            note=form.note.data
        )
        db.session.add(socio)
        db.session.commit()
        return redirect(url_for('soci_lista'))
    
    return render_template('soci_form.html', form=form, title='Nuovo Socio')


@app.route('/soci/<int:id>/modifica', methods=['GET', 'POST'])
def soci_modifica(id):
    """Edit an existing club member."""
    socio = Socio.query.get_or_404(id)
    form = SocioForm(obj=socio)
    
    if form.validate_on_submit():
        socio.nome = form.nome.data
        socio.cognome = form.cognome.data
        socio.email = form.email.data
        socio.telefono = form.telefono.data
        socio.note = form.note.data
        db.session.commit()
        return redirect(url_for('soci_lista'))
    
    return render_template('soci_form.html', form=form, title='Modifica Socio', socio=socio)


@app.route('/soci/<int:id>/elimina', methods=['POST'])
def soci_elimina(id):
    """Delete a club member."""
    socio = Socio.query.get_or_404(id)
    
    nome_completo = socio.nome_completo
    db.session.delete(socio)
    db.session.commit()
    return redirect(url_for('soci_lista'))


# ============= ROUTES: 
    # Check if game has active loans
    prestiti_attivi = Prestito.query.filter_by(gioco_id=id, data_restituzione_effettiva=None).count()
    if prestiti_attivi > 0:
        flash(f'Impossibile eliminare "{gioco.titolo}": ci sono prestiti attivi!', 'error')
        return redirect(url_for('giochi_lista'))
    
    titolo = gioco.titolo
    db.session.delete(gioco)
    db.session.commit()
    return redirect(url_for('giochi_lista'))


# ============= ROUTES: PRESTITI =============

@app.route('/prestiti/nuovo', methods=['GET', 'POST'])
def prestiti_nuovo():
    """Create a new loan."""
    form = PrestitoForm()
    
    # Populate choices with available games
    form.gioco_id.choices = [(0, 'Seleziona un gioco...')] + [
        (g.id, f'{g.titolo} ({g.editore or "N/A"})') 
        for g in Gioco.query.filter_by(disponibile=True).order_by(Gioco.titolo).all()
    ]
    
    # Populate choices for number of players
    form.numero_giocatori_effettivi.choices = [(0, 'Non specificato')] + [(i, str(i)) for i in range(1, 21)]
    
    # Populate choices for socio insegnante (will be updated dynamically via JavaScript)
    form.socio_insegnante_id.choices = [(0, 'Nessuno')]
    
    if form.validate_on_submit():
        if form.gioco_id.data == 0:
            flash('Seleziona un gioco valido!', 'error')
            return render_template('prestiti_nuovo.html', form=form)
        
        # Verify game is available
        gioco = Gioco.query.get(form.gioco_id.data)
        if not gioco or not gioco.disponibile:
            flash('Il gioco selezionato non è disponibile!', 'error')
            return render_template('prestiti_nuovo.html', form=form)
        
        # Create loan with person data
        numero_giocatori = form.numero_giocatori_effettivi.data
        if numero_giocatori == 0:
            numero_giocatori = None
        
        socio_insegnante = form.socio_insegnante_id.data
        if socio_insegnante == 0:
            socio_insegnante = None
        
        prestito = Prestito(
            gioco_id=form.gioco_id.data,
            nome=form.nome.data,
            cognome=form.cognome.data,
            tipo_documento=form.tipo_documento.data,
            slot_archivio=form.slot_archivio.data,
            numero_giocatori_effettivi=numero_giocatori,
            socio_insegnante_id=socio_insegnante,
            data_prestito=datetime.now(),
            note=form.note.data
        )
        
        # Mark game as unavailable
        gioco.disponibile = False
        
        db.session.add(prestito)
        db.session.commit()
        
        return redirect(url_for('prestiti_attivi'))
    
    return render_template('prestiti_nuovo.html', form=form)


@app.route('/prestiti/attivi')
def prestiti_attivi():
    """List all active loans."""
    prestiti = Prestito.query.filter_by(data_restituzione_effettiva=None)\
        .order_by(Prestito.data_prestito.desc()).all()
    return render_template('prestiti_attivi.html', prestiti=prestiti)


@app.route('/prestiti/<int:id>/restituisci', methods=['POST'])
def prestiti_restituisci(id):
    """Mark a loan as returned."""
    prestito = Prestito.query.get_or_404(id)
    
    if prestito.data_restituzione_effettiva is not None:
        flash('Questo prestito è già stato restituito!', 'warning')
        return redirect(url_for('prestiti_attivi'))
    
    # Mark as returned
    prestito.data_restituzione_effettiva = datetime.now()
    
    # Mark game as available
    prestito.gioco.disponibile = True
    
    # Increment giochi_insegnati counter ONLY for the specific socio who taught the game
    if prestito.socio_insegnante_id:
        socio = Socio.query.get(prestito.socio_insegnante_id)
        if socio:
            socio.giochi_insegnati += 1
    
    db.session.commit()
    return redirect(url_for('prestiti_attivi'))


@app.route('/prestiti/storico')
def prestiti_storico():
    """List all completed loans."""
    prestiti = Prestito.query.filter(Prestito.data_restituzione_effettiva.isnot(None))\
        .order_by(Prestito.data_restituzione_effettiva.desc()).all()
    return render_template('prestiti_storico.html', prestiti=prestiti)


# ============= ROUTES: STATISTICHE =============

@app.route('/statistiche')
def statistiche():
    """Display statistics about loans and games."""
    # Most loaned games - get full Gioco objects with loan count
    giochi_piu_prestati = db.session.query(
        Gioco,
        func.count(Prestito.id).label('num_prestiti')
    ).join(Prestito).group_by(Gioco.id).order_by(desc('num_prestiti')).limit(10).all()
    
    # Convert to list of dicts for easier access in template
    giochi_piu_prestati = [{'gioco': gioco, 'titolo': gioco.titolo, 'num_prestiti': count, 'immagine_path': gioco.immagine_path} 
                           for gioco, count in giochi_piu_prestati]
    
    # People with most loans (group by nome and cognome)
    persone_piu_prestiti = db.session.query(
        Prestito.nome,
        Prestito.cognome,
        func.count(Prestito.id).label('num_prestiti')
    ).group_by(Prestito.nome, Prestito.cognome).order_by(desc('num_prestiti')).limit(10).all()
    
    # Overall statistics
    totale_prestiti = Prestito.query.count()
    prestiti_attivi = Prestito.query.filter_by(data_restituzione_effettiva=None).count()
    prestiti_completati = Prestito.query.filter(Prestito.data_restituzione_effettiva.isnot(None)).count()
    
    # Total players who came to play (sum of numero_giocatori_effettivi)
    prestiti_con_giocatori = Prestito.query.filter(Prestito.numero_giocatori_effettivi.isnot(None)).all()
    totale_giocatori = sum([p.numero_giocatori_effettivi for p in prestiti_con_giocatori])
    
    # Average players per game (rounded up)
    import math
    if prestiti_con_giocatori:
        media_giocatori = math.ceil(totale_giocatori / len(prestiti_con_giocatori))
    else:
        media_giocatori = 0
    
    # Average loan duration for completed loans (in hours)
    prestiti_comp = Prestito.query.filter(Prestito.data_restituzione_effettiva.isnot(None)).all()
    if prestiti_comp:
        durata_media = sum([p.ore_prestito for p in prestiti_comp]) / len(prestiti_comp)
    else:
        durata_media = 0
    
    # Game with longest active loan (partita più lunga)
    prestito_piu_lungo = None
    tutti_prestiti = Prestito.query.all()
    if tutti_prestiti:
        prestito_piu_lungo = max(tutti_prestiti, key=lambda p: p.ore_prestito)
    
    # GDR sessions scheduled for today
    oggi = datetime.now().date()
    sessioni_gdr_oggi = GiocoRuolo.query.filter(
        GiocoRuolo.data_sessione == oggi
    ).order_by(GiocoRuolo.orario).all()
    
    return render_template('statistiche.html',
                         giochi_piu_prestati=giochi_piu_prestati,
                         persone_piu_prestiti=persone_piu_prestiti,
                         totale_prestiti=totale_prestiti,
                         prestiti_attivi=prestiti_attivi,
                         prestiti_completati=prestiti_completati,
                         durata_media=durata_media,
                         totale_giocatori=totale_giocatori,
                         media_giocatori=media_giocatori,
                         prestito_piu_lungo=prestito_piu_lungo,
                         sessioni_gdr_oggi=sessioni_gdr_oggi)


@app.route('/statistiche/completo')
def statistiche_completo():
    """Display all statistics in a single view for data analysis."""
    # Most loaned games
    giochi_piu_prestati = db.session.query(
        Gioco,
        func.count(Prestito.id).label('num_prestiti')
    ).join(Prestito).group_by(Gioco.id).order_by(desc('num_prestiti')).limit(10).all()
    
    giochi_piu_prestati = [{'gioco': gioco, 'titolo': gioco.titolo, 'num_prestiti': count, 'immagine_path': gioco.immagine_path} 
                           for gioco, count in giochi_piu_prestati]
    
    # People with most loans
    persone_piu_prestiti = db.session.query(
        Prestito.nome,
        Prestito.cognome,
        func.count(Prestito.id).label('num_prestiti')
    ).group_by(Prestito.nome, Prestito.cognome).order_by(desc('num_prestiti')).limit(10).all()
    
    # Overall statistics
    totale_prestiti = Prestito.query.count()
    prestiti_attivi = Prestito.query.filter_by(data_restituzione_effettiva=None).count()
    prestiti_completati = Prestito.query.filter(Prestito.data_restituzione_effettiva.isnot(None)).count()
    
    # Players statistics
    prestiti_con_giocatori = Prestito.query.filter(Prestito.numero_giocatori_effettivi.isnot(None)).all()
    totale_giocatori = sum([p.numero_giocatori_effettivi for p in prestiti_con_giocatori])
    
    import math
    if prestiti_con_giocatori:
        media_giocatori = math.ceil(totale_giocatori / len(prestiti_con_giocatori))
    else:
        media_giocatori = 0
    
    # Average loan duration
    prestiti_comp = Prestito.query.filter(Prestito.data_restituzione_effettiva.isnot(None)).all()
    if prestiti_comp:
        durata_media = sum([p.ore_prestito for p in prestiti_comp]) / len(prestiti_comp)
    else:
        durata_media = 0
    
    # Longest loan
    prestito_piu_lungo = None
    tutti_prestiti = Prestito.query.all()
    if tutti_prestiti:
        prestito_piu_lungo = max(tutti_prestiti, key=lambda p: p.ore_prestito)
    
    # Additional stats for complete view
    totale_giochi = Gioco.query.count()
    giochi_disponibili = Gioco.query.filter_by(disponibile=True).count()
    
    # GDR sessions scheduled for today
    oggi = datetime.now().date()
    sessioni_gdr_oggi = GiocoRuolo.query.filter(
        GiocoRuolo.data_sessione == oggi
    ).order_by(GiocoRuolo.orario).all()
    
    return render_template('statistiche_completo.html',
                         giochi_piu_prestati=giochi_piu_prestati,
                         persone_piu_prestiti=persone_piu_prestiti,
                         totale_prestiti=totale_prestiti,
                         prestiti_attivi=prestiti_attivi,
                         prestiti_completati=prestiti_completati,
                         durata_media=durata_media,
                         totale_giocatori=totale_giocatori,
                         media_giocatori=media_giocatori,
                         prestito_piu_lungo=prestito_piu_lungo,
                         totale_giochi=totale_giochi,
                         giochi_disponibili=giochi_disponibili,
                         sessioni_gdr_oggi=sessioni_gdr_oggi)

# ============= ROUTES: GIOCHI DI RUOLO (GDR) =============

@app.route('/gdr')
def gdr_lista():
    """List all role-playing game sessions."""
    gdr_list = GiocoRuolo.query.order_by(GiocoRuolo.data_creazione.desc()).all()
    return render_template('gdr_lista.html', gdr_list=gdr_list)


@app.route('/gdr/nuovo', methods=['GET', 'POST'])
def gdr_nuovo():
    """Create a new role-playing game session."""
    form = GiocoRuoloForm()
    
    if form.validate_on_submit():
        # Validate min <= max
        if form.numero_min_giocatori.data > form.numero_max_giocatori.data:
            flash('Il numero minimo di giocatori non può essere maggiore del massimo!', 'error')
            return render_template('gdr_form.html', form=form, title='Nuovo Gioco di Ruolo')
        
        # Parse orario if provided
        orario_obj = None
        if form.orario.data:
            try:
                from datetime import time
                ore, minuti = map(int, form.orario.data.split(':'))
                orario_obj = time(ore, minuti)
            except:
                pass
        
        # Parse data_sessione if provided
        data_obj = None
        if form.data_sessione.data:
            try:
                from datetime import datetime as dt
                data_obj = dt.strptime(form.data_sessione.data, '%Y-%m-%d').date()
            except:
                pass
        
        # Create GDR session
        gdr = GiocoRuolo(
            titolo=form.titolo.data,
            master=form.master.data,
            descrizione=form.descrizione.data,
            numero_min_giocatori=form.numero_min_giocatori.data,
            numero_max_giocatori=form.numero_max_giocatori.data,
            data_sessione=data_obj,
            orario=orario_obj,
            immagine_path=form.immagine_path.data
        )
        
        # Get player names from request (exactly max_giocatori fields)
        giocatori_nomi = []
        for i in range(form.numero_max_giocatori.data):
            nome = request.form.get(f'giocatore_{i}', '').strip()
            if nome:
                giocatori_nomi.append(nome)
        
        gdr.set_giocatori_list(giocatori_nomi)
        
        db.session.add(gdr)
        db.session.commit()
        return redirect(url_for('gdr_lista'))
    
    return render_template('gdr_form.html', form=form, title='Nuovo Gioco di Ruolo')


@app.route('/gdr/<int:id>/modifica', methods=['GET', 'POST'])
def gdr_modifica(id):
    """Edit an existing role-playing game session."""
    gdr = GiocoRuolo.query.get_or_404(id)
    form = GiocoRuoloForm(obj=gdr)
    
    if form.validate_on_submit():
        # Validate min <= max
        if form.numero_min_giocatori.data > form.numero_max_giocatori.data:
            flash('Il numero minimo di giocatori non può essere maggiore del massimo!', 'error')
            return render_template('gdr_form.html', form=form, title='Modifica Gioco di Ruolo', gdr=gdr)
        
        # Parse orario if provided
        orario_obj = None
        if form.orario.data:
            try:
                from datetime import time
                ore, minuti = map(int, form.orario.data.split(':'))
                orario_obj = time(ore, minuti)
            except:
                pass
        
        # Parse data_sessione if provided
        data_obj = None
        if form.data_sessione.data:
            try:
                from datetime import datetime as dt
                data_obj = dt.strptime(form.data_sessione.data, '%Y-%m-%d').date()
            except:
                pass
        
        gdr.titolo = form.titolo.data
        gdr.master = form.master.data
        gdr.descrizione = form.descrizione.data
        gdr.numero_min_giocatori = form.numero_min_giocatori.data
        gdr.numero_max_giocatori = form.numero_max_giocatori.data
        gdr.data_sessione = data_obj
        gdr.orario = orario_obj
        gdr.immagine_path = form.immagine_path.data
        
        # Get player names from request (exactly max_giocatori fields)
        giocatori_nomi = []
        for i in range(form.numero_max_giocatori.data):
            nome = request.form.get(f'giocatore_{i}', '').strip()
            if nome:
                giocatori_nomi.append(nome)
        
        gdr.set_giocatori_list(giocatori_nomi)
        
        db.session.commit()
        return redirect(url_for('gdr_lista'))
    
    # Pre-fill data and orario fields if exist
    if not form.is_submitted():
        if gdr.data_sessione:
            form.data_sessione.data = gdr.data_sessione.strftime('%Y-%m-%d')
        if gdr.orario:
            form.orario.data = gdr.orario.strftime('%H:%M')
    
    return render_template('gdr_form.html', form=form, title='Modifica Gioco di Ruolo', gdr=gdr)


@app.route('/gdr/<int:id>/elimina', methods=['POST'])
def gdr_elimina(id):
    """Delete a role-playing game session."""
    gdr = GiocoRuolo.query.get_or_404(id)
    
    db.session.delete(gdr)
    db.session.commit()
    return redirect(url_for('gdr_lista'))


# ============= ROUTES: EXPORT/IMPORT =============

@app.route('/export')
def export_database():
    """Export entire database to Excel file."""
    try:
        import pandas as pd

        # Create Excel writer
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Export Giochi
            giochi_data = []
            for gioco in Gioco.query.all():
                giochi_data.append({
                    'ID': gioco.id,
                    'Titolo': gioco.titolo,
                    'Editore': gioco.editore,
                    'Anno': gioco.anno,
                    'Numero Giocatori': gioco.numero_giocatori,
                    'Durata': gioco.durata,
                    'Difficoltà': gioco.difficolta,
                    'Immagine URL': gioco.immagine_path,
                    'Disponibile': 'Sì' if gioco.disponibile else 'No'
                })
            df_giochi = pd.DataFrame(giochi_data)
            df_giochi.to_excel(writer, sheet_name='Giochi', index=False)
            
            # Export Soci
            soci_data = []
            for socio in Socio.query.all():
                soci_data.append({
                    'ID': socio.id,
                    'Nome': socio.nome,
                    'Cognome': socio.cognome,
                    'Email': socio.email,
                    'Telefono': socio.telefono,
                    'Note': socio.note
                })
            df_soci = pd.DataFrame(soci_data)
            df_soci.to_excel(writer, sheet_name='Soci', index=False)
            
            # Export Prestiti
            prestiti_data = []
            for prestito in Prestito.query.all():
                prestiti_data.append({
                    'ID': prestito.id,
                    'Gioco': prestito.gioco.titolo,
                    'Nome': prestito.nome,
                    'Cognome': prestito.cognome,
                    'Tipo Documento': prestito.tipo_documento,
                    'Slot Archivio': prestito.slot_archivio,
                    'Numero Giocatori': prestito.numero_giocatori_effettivi if prestito.numero_giocatori_effettivi else '',
                    'Data Prestito': prestito.data_prestito.strftime('%d/%m/%Y %H:%M') if prestito.data_prestito else '',
                    'Data Restituzione': prestito.data_restituzione_effettiva.strftime('%d/%m/%Y %H:%M') if prestito.data_restituzione_effettiva else 'In corso',
                    'Durata': prestito.durata_formattata if prestito.data_restituzione_effettiva else f"{prestito.durata_formattata} (in corso)",
                    'Note': prestito.note
                })
            df_prestiti = pd.DataFrame(prestiti_data)
            df_prestiti.to_excel(writer, sheet_name='Prestiti', index=False)
        
        buffer.seek(0)
        
        filename = f"sentiero_draghi_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        flash(f'Errore durante l\'esportazione: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/import', methods=['GET', 'POST'])
def import_database():
    """Import database from Excel file."""
    if request.method == 'POST':
        try:
            import pandas as pd

            # Check if file was uploaded
            if 'file' not in request.files:
                flash('Nessun file selezionato!', 'error')
                return redirect(url_for('import_database'))
            
            file = request.files['file']
            
            if file.filename == '':
                flash('Nessun file selezionato!', 'error')
                return redirect(url_for('import_database'))
            
            # Check file format
            if not file.filename.endswith(('.xlsx', '.xls')):
                flash('Il file deve essere in formato Excel (.xlsx, .xls)!', 'error')
                return redirect(url_for('import_database'))
            
            clear_existing = request.form.get('clear_existing') == 'yes'
            
            # ========== EXCEL IMPORT ==========
            # Read Excel file
            excel_data = pd.read_excel(file, sheet_name=None)  # Read all sheets
            
            # Validate sheets
            required_sheets = ['Giochi', 'Soci', 'Prestiti']
            missing_sheets = [s for s in required_sheets if s not in excel_data]
            if missing_sheets:
                flash(f'Fogli mancanti nel file Excel: {", ".join(missing_sheets)}', 'error')
                return redirect(url_for('import_database'))
            
            if clear_existing:
                Prestito.query.delete()
                Gioco.query.delete()
                Socio.query.delete()
                db.session.commit()
            
            # Import Soci
            soci_imported = 0
            df_soci = excel_data['Soci']
            for _, row in df_soci.iterrows():
                if pd.notna(row.get('ID')):
                    socio_id = int(row['ID'])
                    existing = Socio.query.get(socio_id) if not clear_existing else None
                    if not existing:
                        socio = Socio(
                            id=socio_id,
                            nome=row['Nome'],
                            cognome=row['Cognome'],
                            email=row.get('Email') if pd.notna(row.get('Email')) else None,
                            telefono=row.get('Telefono') if pd.notna(row.get('Telefono')) else None,
                            note=row.get('Note') if pd.notna(row.get('Note')) else None
                        )
                        db.session.add(socio)
                        soci_imported += 1
            
            db.session.commit()
            
            # Import Giochi
            giochi_imported = 0
            df_giochi = excel_data['Giochi']
            for _, row in df_giochi.iterrows():
                if pd.notna(row.get('ID')):
                    gioco_id = int(row['ID'])
                    existing = Gioco.query.get(gioco_id) if not clear_existing else None
                    if not existing:
                        gioco = Gioco(
                            id=gioco_id,
                            titolo=row['Titolo'],
                            editore=row.get('Editore') if pd.notna(row.get('Editore')) else None,
                            anno=int(row['Anno']) if pd.notna(row.get('Anno')) else None,
                            numero_giocatori=row.get('Numero Giocatori') if pd.notna(row.get('Numero Giocatori')) else None,
                            durata=row.get('Durata') if pd.notna(row.get('Durata')) else None,
                            difficolta=row.get('Difficoltà') if pd.notna(row.get('Difficoltà')) else 'Medio',
                            immagine_path=row.get('Immagine URL') if pd.notna(row.get('Immagine URL')) else None,
                            disponibile=row.get('Disponibile') == 'Sì' if pd.notna(row.get('Disponibile')) else True
                        )
                        db.session.add(gioco)
                        giochi_imported += 1
            
            db.session.commit()
            
            # Import Prestiti
            prestiti_imported = 0
            df_prestiti = excel_data['Prestiti']
            for _, row in df_prestiti.iterrows():
                if pd.notna(row.get('ID')) and pd.notna(row.get('Gioco')):
                    prestito_id = int(row['ID'])
                    existing = Prestito.query.get(prestito_id) if not clear_existing else None
                    if not existing:
                        # Find game by title
                        gioco = Gioco.query.filter_by(titolo=row['Gioco']).first()
                        if gioco:
                            # Parse dates
                            data_prestito = None
                            if pd.notna(row.get('Data Prestito')):
                                try:
                                    data_prestito = pd.to_datetime(row['Data Prestito'], format='%d/%m/%Y %H:%M')
                                except:
                                    data_prestito = datetime.now()
                            
                            data_restituzione = None
                            if pd.notna(row.get('Data Restituzione')) and row['Data Restituzione'] != 'In corso':
                                try:
                                    data_restituzione = pd.to_datetime(row['Data Restituzione'], format='%d/%m/%Y %H:%M')
                                except:
                                    pass
                            
                            prestito = Prestito(
                                id=prestito_id,
                                gioco_id=gioco.id,
                                nome=row['Nome'],
                                cognome=row['Cognome'],
                                tipo_documento=row.get('Tipo Documento', 'Altro'),
                                slot_archivio=int(row['Slot Archivio']) if pd.notna(row.get('Slot Archivio')) else 1,
                                numero_giocatori_effettivi=int(row['Numero Giocatori']) if pd.notna(row.get('Numero Giocatori')) and row['Numero Giocatori'] != '' else None,
                                data_prestito=data_prestito,
                                data_restituzione_effettiva=data_restituzione,
                                note=row.get('Note') if pd.notna(row.get('Note')) else None
                            )
                            db.session.add(prestito)
                            prestiti_imported += 1
            
            db.session.commit()
            
            return redirect(url_for('index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Errore durante l\'importazione: {str(e)}', 'error')
            return redirect(url_for('import_database'))
    
    # GET request - show import form
    return render_template('import.html')


@app.route('/scraping-giochi', methods=['GET', 'POST'])
def scraping_giochi():
    """Complete missing board game metadata using BoardGameGeek."""
    metadati = ('editore', 'anno', 'numero_giocatori', 'durata', 'difficolta', 'immagine_path')
    giochi = Gioco.query.order_by(Gioco.titolo).all()
    giochi_da_completare = [
        gioco for gioco in giochi
        if any(not getattr(gioco, campo) for campo in metadati)
    ]

    if request.method == 'POST':
        aggiornati = 0
        non_trovati = []
        try:
            headers = _bgg_headers()
            for gioco in giochi_da_completare:
                search_response = requests.get(
                    'https://boardgamegeek.com/xmlapi2/search',
                    params={'query': gioco.titolo, 'type': 'boardgame'},
                    headers=headers,
                    timeout=15
                )
                search_response.raise_for_status()
                risultati = ElementTree.fromstring(search_response.content).findall('item')
                if not risultati:
                    non_trovati.append(gioco.titolo)
                    continue

                bgg_id = risultati[0].get('id')
                detail_response = requests.get(
                    'https://boardgamegeek.com/xmlapi2/thing',
                    params={'id': bgg_id},
                    headers=headers,
                    timeout=15
                )
                detail_response.raise_for_status()
                item = ElementTree.fromstring(detail_response.content).find('item')
                if item is None:
                    non_trovati.append(gioco.titolo)
                    continue

                changed = False
                primary_name = item.find("name[@type='primary']")
                values = {
                    'editore': next((node.get('value') for node in item.findall('link[@type="boardgamepublisher"]')), None),
                    'anno': item.findtext('yearpublished'),
                    'numero_giocatori': _format_range(item.findtext('minplayers'), item.findtext('maxplayers')),
                    'durata': _format_range(item.findtext('minplaytime'), item.findtext('maxplaytime'), ' min'),
                    'difficolta': _format_difficulty(item.findtext('statistics/ratings/averageweight')),
                    'immagine_path': item.findtext('image')
                }
                for campo, valore in values.items():
                    if not getattr(gioco, campo) and valore:
                        setattr(gioco, campo, valore)
                        changed = True
                if changed:
                    aggiornati += 1

            db.session.commit()
            flash(f'Metadati aggiornati per {aggiornati} gioco/i.', 'success')
            if non_trovati:
                flash('Nessun risultato trovato per: ' + ', '.join(non_trovati), 'warning')
        except RuntimeError as exc:
            flash(str(exc), 'error')
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 401:
                flash('Token BoardGameGeek non valido o non autorizzato.', 'error')
            else:
                flash(f'Errore durante lo scraping: {exc}', 'error')
            db.session.rollback()
        except (requests.RequestException, ElementTree.ParseError) as exc:
            db.session.rollback()
            flash(f'Errore durante lo scraping: {exc}', 'error')

        giochi = Gioco.query.order_by(Gioco.titolo).all()
        giochi_da_completare = [gioco for gioco in giochi if any(not getattr(gioco, campo) for campo in metadati)]

    return render_template('scraping_giochi.html', giochi=giochi_da_completare)


def _bgg_headers():
    """Build the authenticated headers required by BoardGameGeek."""
    token = app.config['BGG_API_TOKEN']
    if not token:
        raise RuntimeError(
            'Configurazione incompleta: imposta la variabile d\'ambiente BGG_API_TOKEN '
            'con l\'Application Token BoardGameGeek.'
        )
    return {
        'Authorization': f'Bearer {token}',
        'User-Agent': 'IlSentieroDeiDraghi/1.0'
    }


def _format_range(minimum, maximum, suffix=''):
    """Format a numeric range returned by BoardGameGeek."""
    if not minimum or not maximum:
        return None
    return f'{minimum}{suffix}' if minimum == maximum else f'{minimum}-{maximum}{suffix}'


def _format_difficulty(weight):
    """Map BoardGameGeek's complexity score to the local difficulty labels."""
    if not weight:
        return None
    value = float(weight)
    if value < 2:
        return 'Facile'
    if value < 3.5:
        return 'Medio'
    return 'Difficile'


@app.route('/reset-prestiti', methods=['POST'])
def reset_prestiti():
    """Reset all loans and mark all games as available."""
    try:
        # Delete all loans
        num_deleted = Prestito.query.delete()
        
        # Mark all games as available
        num_updated = 0
        for gioco in Gioco.query.all():
            if not gioco.disponibile:
                gioco.disponibile = True
                num_updated += 1
        
        db.session.commit()
        
        return redirect(url_for('index'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante il reset: {str(e)}', 'error')
        return redirect(url_for('index'))


# ============= API ROUTES =============

@app.route('/api/gioco/<int:gioco_id>')
def api_gioco(gioco_id):
    """API endpoint to get game details."""
    gioco = Gioco.query.get_or_404(gioco_id)
    return jsonify({
        'id': gioco.id,
        'titolo': gioco.titolo,
        'editore': gioco.editore,
        'anno': gioco.anno,
        'numero_giocatori': gioco.numero_giocatori,
        'range_giocatori': gioco.get_range_giocatori(),  # [min, max] or None
        'durata': gioco.durata,
        'difficolta': gioco.difficolta,
        'immagine_path': gioco.immagine_path,
        'disponibile': gioco.disponibile,
        'soci': [{'id': s.id, 'nome_completo': s.nome_completo} for s in gioco.soci]
    })


# ============= ROUTES: ISTRUZIONI =============

@app.route('/istruzioni')
def istruzioni():
    """Display user instructions page."""
    try:
        # Try to read instructions file from root directory
        istruzioni_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ISTRUZIONI.md')
        
        # If running as exe, try the build directory
        if not os.path.exists(istruzioni_path):
            istruzioni_path = os.path.join(os.path.dirname(sys.executable), 'ISTRUZIONI.md')
        
        if os.path.exists(istruzioni_path):
            with open(istruzioni_path, 'r', encoding='utf-8') as f:
                contenuto = f.read()
        else:
            contenuto = "# Istruzioni non trovate\n\nIl file ISTRUZIONI.md non è stato trovato."
    except Exception as e:
        contenuto = f"# Errore\n\nImpossibile leggere il file istruzioni: {str(e)}"
    
    return render_template('istruzioni.html', contenuto=contenuto)


# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404


# ============= RUN APPLICATION =============

if __name__ == '__main__':
    app.run(
        debug=os.environ.get('FLASK_DEBUG', '').lower() == 'true',
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '5000'))
    )
