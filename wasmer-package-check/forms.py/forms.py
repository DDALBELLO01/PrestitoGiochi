"""
Flask-WTF forms for validation and rendering.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, BooleanField, TextAreaField, SelectField, DateField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Email


class SocioForm(FlaskForm):
    """Form for creating and editing club members/partners."""
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    cognome = StringField('Cognome', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=200)])
    telefono = StringField('Telefono', validators=[Optional(), Length(max=50)])
    note = TextAreaField('Note', validators=[Optional(), Length(max=500)])


class GiocoForm(FlaskForm):
    """Form for creating and editing board games."""
    titolo = StringField('Titolo', validators=[DataRequired(), Length(max=200)])
    editore = StringField('Editore', validators=[Optional(), Length(max=100)])
    anno = IntegerField('Anno', validators=[Optional(), NumberRange(min=1900, max=2100)])
    numero_giocatori = StringField('Numero Giocatori', validators=[Optional(), Length(max=50)])
    durata = StringField('Durata', validators=[Optional(), Length(max=50)])
    soci_ids = SelectMultipleField('Soci', coerce=int, validators=[Optional()])
    difficolta = SelectField('Difficoltà', 
                            choices=[('', 'Seleziona...'), 
                                   ('Facile', 'Facile'), 
                                   ('Medio', 'Medio'), 
                                   ('Difficile', 'Difficile')],
                            validators=[Optional()])
    immagine_path = StringField('URL Immagine', validators=[Optional(), Length(max=500)])
    disponibile = BooleanField('Disponibile', default=True)


class PrestitoForm(FlaskForm):
    """Form for creating new loans."""
    gioco_id = SelectField('Gioco', coerce=int, validators=[DataRequired()])
    nome = StringField('Nome', validators=[DataRequired(), Length(max=100)])
    cognome = StringField('Cognome', validators=[DataRequired(), Length(max=100)])
    tipo_documento = SelectField('Tipo Documento', 
                                choices=[
                                    ('Carta d\'identità', 'Carta d\'identità'),
                                    ('Patente', 'Patente'),
                                    ('Passaporto', 'Passaporto'),
                                    ('Altro', 'Altro')
                                ],
                                validators=[DataRequired()])
    slot_archivio = IntegerField('Slot Archivio', validators=[DataRequired(), NumberRange(min=1)])
    numero_giocatori_effettivi = SelectField('Numero Giocatori', coerce=int, validators=[Optional()])
    socio_insegnante_id = SelectField('Insegnato da', coerce=int, validators=[Optional()])
    note = TextAreaField('Note', validators=[Optional(), Length(max=500)])


class GiocoRuoloForm(FlaskForm):
    """Form for creating and editing role-playing game sessions."""
    titolo = StringField('Titolo', validators=[DataRequired(), Length(max=200)])
    master = StringField('Master', validators=[DataRequired(), Length(max=100)])
    descrizione = TextAreaField('Descrizione', validators=[Optional(), Length(max=1000)])
    numero_min_giocatori = IntegerField('Numero Minimo Giocatori', validators=[DataRequired(), NumberRange(min=1, max=50)])
    numero_max_giocatori = IntegerField('Numero Massimo Giocatori', validators=[DataRequired(), NumberRange(min=1, max=50)])
    data_sessione = StringField('Data Sessione', validators=[Optional(), Length(max=10)])  # Format YYYY-MM-DD
    orario = StringField('Orario', validators=[Optional(), Length(max=5)])  # Format HH:MM
    immagine_path = StringField('URL Immagine', validators=[Optional(), Length(max=500)])
    # Player names will be handled dynamically in the template
