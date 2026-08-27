"""
Database models for the board game lending system.
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Many-to-many relationship table between Gioco and Socio
gioco_socio = db.Table('gioco_socio',
    db.Column('gioco_id', db.Integer, db.ForeignKey('giochi.id'), primary_key=True),
    db.Column('socio_id', db.Integer, db.ForeignKey('soci.id'), primary_key=True)
)


class Socio(db.Model):
    """Member/Partner model for board game club members."""
    __tablename__ = 'soci'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200))
    telefono = db.Column(db.String(50))
    note = db.Column(db.Text)
    giochi_insegnati = db.Column(db.Integer, default=0, nullable=False)  # Counter for games taught/explained
    
    # Relationship
    giochi = db.relationship('Gioco', secondary=gioco_socio, back_populates='soci')
    
    @property
    def nome_completo(self):
        return f'{self.nome} {self.cognome}'
    
    def __repr__(self):
        return f'<Socio {self.nome_completo}>'


class Gioco(db.Model):
    """Board game model with all game details."""
    __tablename__ = 'giochi'
    
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(200), nullable=False)
    editore = db.Column(db.String(100))
    anno = db.Column(db.Integer)
    numero_giocatori = db.Column(db.String(50))  # e.g., "2-4", "1-6"
    durata = db.Column(db.String(50))  # e.g., "30-60 min"
    difficolta = db.Column(db.String(50))  # e.g., "Facile", "Medio", "Difficile"
    immagine_path = db.Column(db.String(500))  # Path locale dell'immagine del gioco
    disponibile = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    soci = db.relationship('Socio', secondary=gioco_socio, back_populates='giochi')
    prestiti = db.relationship('Prestito', backref='gioco', lazy=True)
    
    def get_range_giocatori(self):
        """Parse player range string (e.g., '4-7') and return [min, max] or None."""
        if not self.numero_giocatori:
            return None
        
        try:
            # Try to parse "X-Y" format
            if '-' in self.numero_giocatori:
                parts = self.numero_giocatori.split('-')
                min_players = int(parts[0].strip())
                max_players = int(parts[1].strip())
                return [min_players, max_players]
            # Try single number
            else:
                num = int(self.numero_giocatori.strip())
                return [num, num]
        except (ValueError, IndexError):
            return None
    
    def __repr__(self):
        return f'<Gioco {self.titolo}>'


class Prestito(db.Model):
    """Loan model tracking game loans to people."""
    __tablename__ = 'prestiti'
    
    id = db.Column(db.Integer, primary_key=True)
    gioco_id = db.Column(db.Integer, db.ForeignKey('giochi.id'), nullable=False)
    
    # Dati persona (direttamente nel prestito)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    tipo_documento = db.Column(db.String(50), nullable=False, default='Altro')  # Tipo documento
    slot_archivio = db.Column(db.Integer, nullable=False)  # Slot archivio fisico
    numero_giocatori_effettivi = db.Column(db.Integer, nullable=True)  # Numero giocatori effettivi della sessione
    socio_insegnante_id = db.Column(db.Integer, db.ForeignKey('soci.id'), nullable=True)  # Socio che ha insegnato il gioco
    
    data_prestito = db.Column(db.DateTime, nullable=False, default=datetime.now)
    data_restituzione_effettiva = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.Text)
    
    # Relationship to the socio who taught the game
    socio_insegnante = db.relationship('Socio', foreign_keys=[socio_insegnante_id])
    
    @property
    def nome_completo(self):
        return f'{self.nome} {self.cognome}'
    
    def __repr__(self):
        return f'<Prestito {self.id}: {self.gioco.titolo} -> {self.nome_completo}>'
    
    @property
    def is_attivo(self):
        """Check if the loan is still active (not returned)."""
        return self.data_restituzione_effettiva is None
    
    @property
    def giorni_prestito(self):
        """Calculate the number of days the game has been loaned (deprecated - use ore_prestito)."""
        if self.is_attivo:
            return (datetime.now() - self.data_prestito).days
        else:
            return (self.data_restituzione_effettiva - self.data_prestito).days
    
    @property
    def ore_prestito(self):
        """Calculate total hours the game has been loaned."""
        if self.is_attivo:
            delta = datetime.now() - self.data_prestito
        else:
            delta = self.data_restituzione_effettiva - self.data_prestito
        return delta.total_seconds() / 3600  # Converti in ore
    
    @property
    def durata_formattata(self):
        """Format loan duration as 'Xh Ym' or 'Xg Yh' if more than 24 hours."""
        ore_totali = self.ore_prestito
        
        if ore_totali < 24:
            ore = int(ore_totali)
            minuti = int((ore_totali - ore) * 60)
            return f"{ore}h {minuti}m"
        else:
            giorni = int(ore_totali / 24)
            ore = int(ore_totali % 24)
            return f"{giorni}g {ore}h"


class GiocoRuolo(db.Model):
    """Role-playing game session model."""
    __tablename__ = 'giochi_ruolo'
    
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(200), nullable=False)
    master = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.Text)
    numero_min_giocatori = db.Column(db.Integer, nullable=False)
    numero_max_giocatori = db.Column(db.Integer, nullable=False)
    giocatori_nomi = db.Column(db.Text)  # JSON array of player names
    data_creazione = db.Column(db.DateTime, nullable=False, default=datetime.now)
    data_sessione = db.Column(db.Date)  # Session date
    orario = db.Column(db.Time)  # Session time
    immagine_path = db.Column(db.String(500))  # Image URL or path
    
    def get_giocatori_list(self):
        """Get list of player names from JSON field."""
        if not self.giocatori_nomi:
            return []
        import json
        try:
            return json.loads(self.giocatori_nomi)
        except:
            return []
    
    def set_giocatori_list(self, nomi_list):
        """Set player names as JSON."""
        import json
        # Filter out empty strings
        nomi_filtrati = [nome.strip() for nome in nomi_list if nome and nome.strip()]
        self.giocatori_nomi = json.dumps(nomi_filtrati)
    
    @property
    def num_giocatori_iscritti(self):
        """Count non-empty player slots."""
        return len(self.get_giocatori_list())
    
    @property
    def posti_disponibili(self):
        """Calculate available spots."""
        return self.numero_max_giocatori - self.num_giocatori_iscritti
    
    @property
    def is_completo(self):
        """Check if the session is full."""
        return self.num_giocatori_iscritti >= self.numero_max_giocatori
    
    @property
    def can_start(self):
        """Check if the session has enough players to start."""
        return self.num_giocatori_iscritti >= self.numero_min_giocatori
    
    @property
    def is_oggi(self):
        """Check if the session is scheduled for today."""
        if self.data_sessione:
            oggi = datetime.now().date()
            return self.data_sessione == oggi
        elif self.data_creazione:
            oggi = datetime.now().date()
            return self.data_creazione.date() == oggi
        return False
    
    def __repr__(self):
        return f'<GiocoRuolo {self.titolo} - Master: {self.master}>'
