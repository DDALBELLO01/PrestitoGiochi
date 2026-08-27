# Istruzioni per l'uso - Il Sentiero dei Draghi

## Avvio su Wasmer

Il progetto include `app.yaml` e `Procfile` per il deploy come applicazione Flask tramite Gunicorn. Non usare `wasmer publish`: quel comando serve a pubblicare pacchetti WebAssembly e richiede un file `.wasm`.

1. Esegui `wasmer login`.
2. Esegui `wasmer deploy --path app.yaml` dalla cartella del progetto.
3. Imposta `SECRET_KEY` su un valore segreto personale nelle variabili d'ambiente del servizio.
4. Imposta `AUTH_USERNAME` e `AUTH_PASSWORD` su valori personali nelle variabili d'ambiente del servizio. In alternativa usa `AUTH_PASSWORD_HASH`.
5. Per un database persistente, configura `DATABASE_PATH` su un volume persistente oppure usa `DATABASE_URL` con un database supportato.

Comando di avvio: `gunicorn --bind 0.0.0.0:$PORT app:app`

## 📖 Guida all'uso del software di gestione prestiti giochi

---

## 1. Dashboard

La **Dashboard** è la pagina principale che mostra:
- Numero totale di giochi disponibili
- Numero di prestiti attivi
- Statistiche rapide

---

## 2. Gestione Giochi da Tavolo

### Aggiungere un gioco
1. Clicca su **Giochi da Tavolo** → **Aggiungi Gioco**
2. Compila i campi:
   - **Titolo** (obbligatorio)
   - **Editore** (opzionale)
   - **Anno** (opzionale)
   - **Numero Giocatori** (es. "2-4", "1-6", "4+", "1-4/6")
   - **Durata** (es. "30", "60-90")
   - **Difficoltà** (Facile/Medio/Difficile)
   - **URL Immagine** (opzionale)
   - **Soci Insegnanti** (opzionale): seleziona i soci che sanno spiegare questo gioco
   - **Disponibile** (seleziona se il gioco è disponibile)
3. Clicca su **Salva**

**Nota sui Soci Insegnanti**: Selezionando i soci che conoscono le regole, quando qualcuno prende in prestito il gioco può vedere chi può insegnarlo e selezionare l'insegnante specifico.

### Modificare un gioco
1. Vai su **Giochi da Tavolo** → **Lista Giochi**
2. Clicca sull'icona di modifica (matita) accanto al gioco
3. Modifica i campi necessari (inclusi i soci insegnanti)
4. Clicca su **Salva**

### Eliminare un gioco
1. Vai su **Giochi da Tavolo** → **Lista Giochi**
2. Clicca sull'icona cestino accanto al gioco
3. Conferma l'eliminazione
   - **Nota**: Non puoi eliminare un gioco con prestiti attivi

### Filtri avanzati
Nella lista giochi puoi filtrare per:
- **Ricerca testuale**: cerca per titolo o editore
- **Soci Insegnanti**: mostra solo giochi che un socio specifico può insegnare
- **Numero giocatori**: trova giochi compatibili con un numero specifico
- **Difficoltà**: Facile, Medio, Difficile
- **Durata**: filtra per durata massima in minuti
- **Solo disponibili**: mostra solo giochi disponibili per il prestito

I filtri sono distribuiti su due righe per una migliore usabilità e funzionano in tempo reale.

### Visualizzazione nella lista
Ogni gioco mostra:
- **Immagine**: thumbnail 50x50px
- **Titolo** in grassetto
- **"Spiegano: ..."**: se ci sono soci insegnanti, appaiono in verde sotto il titolo con icona ✓

---

## 3. Gestione Giochi di Ruolo

I **Giochi di Ruolo** (GDR) sono sessioni separate dai giochi da tavolo, con gestione giocatori dedicata e pianificazione temporale.

### Creare una nuova sessione GDR
1. Clicca su **Giochi di Ruolo** → **Nuova Sessione**
2. Compila i campi:
   - **Titolo** (obbligatorio): nome dell'avventura o campagna
   - **Master** (obbligatorio): nome del game master
   - **Descrizione** (opzionale): dettagli sulla sessione, ambientazione, sistema di gioco, ecc.
   - **Numero Minimo Giocatori** (obbligatorio): giocatori necessari per iniziare
   - **Numero Massimo Giocatori** (obbligatorio): limite posti disponibili
   - **Data Sessione** (opzionale): quando si terrà la sessione (formato AAAA-MM-GG)
   - **Orario** (opzionale): ora di inizio (formato HH:MM, usa il picker)
   - **URL Immagine** (opzionale): immagine rappresentativa della campagna/sistema
3. **Giocatori Iscritti**:
   - Il sistema genera automaticamente tanti campi quanti il numero massimo
   - Scrivi i nomi dei giocatori a mano (non sono presi dal database soci)
   - Lascia vuoti i campi per i posti non ancora occupati
4. Clicca su **Salva**

**Nota sulla Data**: Se inserisci una data sessione, la sessione apparirà nelle statistiche del giorno quando arriva quella data.

### Modificare una sessione GDR
1. Vai su **Giochi di Ruolo** → **Lista Sessioni**
2. Clicca sull'icona di modifica (matita)
3. Modifica i campi, inclusi data, orario e giocatori
4. Clicca su **Salva**

### Visualizzare le informazioni
Nella lista sessioni vengono mostrati:
- **Titolo** e **Master**
- **Data** (formato GG/MM/AAAA con icona calendario)
- **Orario** (formato HH:MM con icona orologio)
- **Immagine** (thumbnail 40x40px)
- **Numero giocatori**: iscritti/massimo (es. 4/6)
- Clicca su **Mostra** per vedere l'elenco completo dei giocatori iscritti

### Stati sessione
Le sessioni hanno 3 possibili stati:
- **🟡 In attesa**: non ha ancora raggiunto il minimo di giocatori
- **🟢 Pronto**: ha il minimo di giocatori necessari per iniziare
- **🔴 Completo**: tutti i posti sono occupati

### Filtri sessioni GDR
Nella lista puoi filtrare per:
- **Titolo o Master**: ricerca testuale
- **Stato**: Completi, Con posti disponibili, Pronti per iniziare

### Statistiche GDR
Le sessioni con data_sessione impostata su oggi appariranno automaticamente nelle statistiche carousel (Slide 7) e nella vista completa, mostrando:
- Titolo, Master, Descrizione
- Data e Orario
- Numero giocatori iscritti

### Visualizzazione nella lista soci
Ogni socio mostra:
- Nome, Cognome, Email, Telefono
- **Giochi Insegnati**: badge blu con icona 🏆 che mostra il numero di volte che ha insegnato giochi
- **Sa spiegare X giochi**: numero di giochi di cui conosce le regole (associati nel database giochi)

### Come funziona il contatore "Giochi Insegnati"
Il contatore viene incrementato automaticamente quando:
1. Un gioco viene preso in prestito
2. Nel form prestito viene selezionato questo socio come "Insegnato da"
3. Il prestito viene restituito

**Importante**: Solo il socio selezionato specificamente nel prestito incrementa il contatore, permettendo di tracciare con precisione chi ha effettivamente insegnato ogni gioco.
- Immagine (se presente)

---

## 4. Gestione Soci

### Aggiungere un socio
1. Clicca su **Soci** → **Aggiungi Socio**
2. Compila:
   - **Nome** e **Cognome** (obbligatori)
   - **Email** e **Telefono** (opzionali)
   - **Note** (opzionali)
3. Clicca su **Salva**, durata, e soci che possono insegnarlo
3. **Numero giocatori**:
   - Se il gioco ha un range (es. "2-4"), scegli dalla lista
   - Se il gioco ha "4+", inserisci manualmente il numero (minimo indicato)
4. **Insegnato da** (opzionale):
   - Dopo aver selezionato numero giocatori, appare questo campo
   - Se il gioco ha soci associati che lo sanno spiegare, verranno mostrati nel dropdown
   - Seleziona il socio specifico che insegnerà il gioco, oppure "Nessuno"
   - Questo permette di tracciare precisamente chi ha insegnato ogni gioco
5. **Dati persona**:
   - **Nome** e **Cognome** della persona che prende in prestito
   - **Tipo documento** lasciato (Carta d'identità, Patente, etc.)
   - **Slot archivio**: numero dello slot dove archiviare il documento
6. **Note** (opzionali)
7. Clicca su **Crea Prestito**

**Nota sull'insegnamento**: 
- Se selezioni un socio insegnante, alla restituzione del gioco quel socio vedrà incrementato il contatore "Giochi Insegnati"
- Se selezioni "Nessuno", non ci sarà alcun incremento (prestito senza insegnamento)
- Questo sistema permette di premiare e tracciare l'attività di insegnamento dei soci

### Restituire un gioco
1. Vai su **Prestiti** → **Prestiti Attivi**
2. Trova il prestito nella lista
3. Clicca sul pulsante **Restituisci** (verde con check)
4. Conferma la restituzione
   - Il gioco tornerà automaticamente disponibile
   - Se era stato selezionato un insegnante, il suo contatore verrà incrementato

### Visualizzare le informazioni
Nella lista prestiti attivi e nello storico puoi vedere:
- Gioco prestato (titolo ed editore)
- Persona che ha preso in prestito
- Numero giocatori effettivi
- **Insegnamento**: badge verde "Sì" con il nome del socio che ha insegnato, oppure "-" se nessuno
- Slot archivio documento
- Data prestito
- Durata del prestito

### Visualizzare lo storico
Vai su **Prestiti** → **Storico** per vedere tutti i prestiti completati con le stesse informazioni, incluso chi ha insegnato ogni gioco.
   - **Tipo documento** lasciato (Carta d'identità,  (ogni 4 secondi)
- Premi **F11** per schermo intero (ideale per monitor secondario o eventi)
- Include 7 slides:
  1. Prestiti totali e attivi
  2. Giocatori totali e media per partita
  3. Durata media prestiti
  4. Gioco più prestato
  5. Partita più lunga
  6. Persone con più prestiti (Top 10)
  7. **Giochi di Ruolo Oggi**: sessioni GDR programmate per oggi con data/orario

### Vista Completa
- Clicca su **Statistiche** → **Vista Completa**
- Mostra tutte le statistiche in una singola pagina scrollabile
- Include grafici, tabelle dettagliate e la sezione "Giochi di Ruolo - Oggi"
- Utile per analisi approfondite e stampa

### Statistiche GDR del giorno
Entrambe le viste mostrano le sessioni GDR programmate per oggi (basate sul campo "Data Sessione"), con:
- Immagine della campagna
- Titolo e Master
- Data e Orario
- Numero giocatori iscritti
- Descrizione brev
Vai su **Prestiti** → **Storico** per vedere tutti i prestiti completati

---

## 6. Statistiche

### Vista Carousel (per presentazioni)
- Clicca su **Statistiche** → **Vista Carousel**
- Mostra statistiche animate in rotazione automatica
- Premi **F11** per schermo intero (ideale per monitor secondario)
- Include:
  - Prestiti totali e attivi
  - Giocatori totali e media per partita
  - Durata media prestiti
  - Gioco più prestato
  - Partita più lunga

### Vista Completa
- Clicca su **Statistiche** → **Vista Completa**
- Mostra tutte le statistiche in una singola pagina
- Include grafici e tabelle dettagliate

---

## 7. Database

### Esportare in Excel
1. Clicca su **Database** → **Esporta in Excel**
2. Il file verrà scaricato automaticamente con timestamp
3. Il file Excel contiene 3 fogli:
   - **Giochi**: tutti i giochi
   - **Soci**: tutti i soci
   - **Prestiti**: tutti i prestiti (attivi e storici)

### Importare da Excel
1. Clicca su **Database** → **Importa da Excel**
2. Seleziona un file Excel con la struttura corretta
3. Il sistema importerà automaticamente i dati
4. **Attenzione**: i dati verranno aggiunti a quelli esistenti

### Reset Prestiti
1. Clicca su **Database** → **Reset Prestiti**
2. **ATTENZIONE**: Questa operazione:
   - Cancella TUTTI i prestiti (attivi e storici)
   - Imposta tutti i giochi come disponibili
   - È IRREVERSIBILE
3. Conferma l'operazione

---

## 8. Ricerca e Filtri

- **Cerca giochi**: usa la barra di ricerca per filtrare per titolo, editore
- **Cerca soci**: filtra per nome, cognome, email
- **Cerca prestiti**: filtra per gioco, persona, slot archivio
- Tutte le ricerche sono in tempo reale
- **Associa i soci insegnanti**: quando aggiungi un gioco, seleziona i soci che lo sanno spiegare
  - Questo facilita l'organizzazione dei prestiti con insegnamento
  - I soci vedranno riconosciuto il loro contributo tramite il contatore

### Per i prestiti
- Verifica sempre il **numero slot archivio** disponibile
- Inserisci il **numero effettivo di giocatori** per statistiche migliori
- **Seleziona l'insegnante** se qualcuno spiega il gioco:
  - Permette di tracciare chi ha insegnato cosa
  - Incrementa il contatore del socio alla restituzione
  - Seleziona "Nessuno" se il prestito è senza insegnamento
- Usa le **note** per informazioni particolari

### Per i soci
- Mantieni aggiornata la lista di giochi che ogni socio sa spiegare
- Il contatore "Giochi Insegnati" riflette l'attività reale di insegnamento
- Usa questa informazione per riconoscere i soci più attivi

### Per le statistiche
- Esporta regolarmente i dati in Excel come backup
- Usa la vista Carousel in F11 per eventi e presentazioni
- Le statistiche GDR del giorno sono utili per organizzare le sessioni

### Per i giochi di ruolo
- Crea la sessione prima di raccogliere le iscrizioni
- Imposta sempre un numero minimo e massimo realistico
- **Usa Data Sessione** per pianificare sessioni future e vederle nelle statistiche
- **Usa Orario** per coordinare gli arrivi
- Usa la **descrizione** per indicare sistema di gioco, livello esperienza richiesto, tono della campagna
- Aggiorna regolarmente i giocatori iscritti
- **Usa URL Immagine** per rendere più accattivante la visualizzazione nelle statisticheri** per statistiche migliori
- Usa le **note** per informazioni particolari

### Per le statistiche
- Esporta regolarmente i dati in Excel come backup

### Il dropdown "Insegnato da" non appare
- Verifica di aver selezionato prima un gioco
- Il dropdown appare solo se il gioco ha soci associati che lo sanno spiegare
- Se nessun socio è associato al gioco, il campo non viene mostrato

### Le sessioni GDR non appaiono nelle statistiche
- Verifica che la **Data Sessione** sia impostata su oggi
- Se la data è nel futuro o nel passato, non appariranno nelle statistiche del giorno
- La data viene confrontata con la data corrente del sistema

### I filtri nella lista giochi non funzionano
- Verifica che JavaScript sia abilitato
- I filtri lavorano in tempo reale, assicurati di aver inserito valori corretti
- Usa il pulsante "Reset" per pulire tutti i filtri
- Usa la vista Carousel in F11 per eventi e presentazioni

### Per i giochi di ruolo
- Crea la sessione prima di raccogliere le iscrizioni
- Imposta sempre un numero minimo e massimo realistico
- Usa la descrizione per indicare sistema di gioco, livello esperienza, ecc.
- Aggiorna regolarmente i giocatori iscritti

---

## 10. Risoluzione Problemi
2.0  
**Ultimo aggiornamento**: Luglio 2026

### Changelog versione 2.0
- ✅ Aggiunto sistema soci insegnanti per i giochi
- ✅ Contatore "Giochi Insegnati" per tracciare l'attività dei soci
- ✅ Dropdown "Insegnato da" nel form prestiti per selezionare l'insegnante specifico
- ✅ Filtro per soci insegnanti nella lista giochi
- ✅ Filtri su due righe per migliore usabilità
- ✅ Data e Orario per sessioni GDR
- ✅ Immagine per sessioni GDR
- ✅ Sessioni GDR nelle statistiche del giorno (carousel e completa)
- ✅ Visualizzazione "Spiegano: ..." nei giochi con soci associatirestiti
- Verifica che il gioco sia segnato come **Disponibile**
- Se c'è un prestito attivo, devi prima restituirlo

### Non riesco a eliminare un gioco
- Verifica che non ci siano prestiti attivi
- Controlla nello storico se ci sono prestiti

### Le statistiche non si aggiornano
- Ricarica la pagina (F5)
- Verifica che i dati siano stati salvati correttamente

### I campi giocatori GDR non si generano
- Assicurati di aver inserito un numero massimo valido (1-50)
- Controlla che JavaScript sia abilitato nel browser

---

## 11. Scorciatoie Tastiera

- **F11**: Modalità schermo intero (specialmente utile per statistiche)
- **Esc**: Esci dalla modalità schermo intero
- **Ctrl+F** (o Cmd+F): Cerca nella pagina corrente

---

## Supporto

Per problemi o suggerimenti, contatta l'amministratore del sistema.

**Versione Software**: 1.0  
**Ultimo aggiornamento**: Luglio 2026
