# EuroFuel - Comparator Prețuri Carburanți Europa

EuroFuel este o aplicație web modernă, rapidă și responsivă, concepută pentru a compara prețurile la benzină (regular 95) și motorină (diesel) din principalele țări continentale din Europa. 

Aplicația afișează prețurile pentru 4 dintre cele mai folosite lanțuri de benzinării din țările selectate, exprimate simultan în trei monede: **moneda locală**, **Euro (EUR)** și **Lei românești (RON)**.

---

## 🚀 Caracteristici Principale

- **Selecție Dinamică:** Compară până la 4 țări simultan folosind filtre dropdown intuitive.
- **Tip Carburant:** Comutator rapid între Benzină (Petrol) și Motorină (Diesel).
- **Conversii în 3 Monede:** Prețurile sunt convertite automat la cursul curent în moneda locală, EUR și RON.
- **Cursuri Valutare Live:** Integrare cu Frankfurter API (bazat pe Banca Centrală Europeană) pentru a prelua ratele de schimb valutare în timp real direct în browser, completând datele de bază.
- **Cache Local robust (LocalStorage):** Aplicația stochează datele local în browser și verifică automat actualizările la startup, dar nu mai des de **2 ore** pentru a economisi resurse.
- **Aesthetic Premium (Dark / Light Mode):** Interfață modernă cu efecte de glassmorphism, culori HSL optimizate pentru ambele teme și micro-animații fine pentru feedback vizual premium.
- **Documentație Integrată:** Footer personalizat care, la click pe textul de autor, afișează acest fișier README frumos formatat chiar în interiorul aplicației.

---

## 🗺️ Țări Continentale Acoperite (21 țări)

Aplicația acoperă principalele țări din Europa continentală:
- **România (RO)**, **Germania (DE)**, **Franța (FR)**, **Italia (IT)**, **Spania (ES)**, **Polonia (PL)**, **Olanda (NL)**, **Belgia (BE)**, **Austria (AT)**, **Ungaria (HU)**, **Cehia (CZ)**, **Bulgaria (BG)**, **Grecia (GR)**, **Portugalia (PT)**, **Slovacia (SK)**, **Croația (HR)**, **Serbia (RS)**, **Slovenia (SI)**, **Moldova (MD)**, **Muntenegru (ME)** și **Macedonia (MK)**.

*Notă: Sunt excluse țările foarte mici (monarhiile/principatele, Malta, Luxemburg), Belarus, Ucraina, Rusia, Marea Britanie (insulară) și țările scandinave (din cauza erorilor SSL de pe serverele Fuelo pentru domeniile respective).*

---

## 📊 Surse de Date și Actualizare

Datele aplicației provin din două surse majore:
1. **Banca Națională a României (BNR):** Cursurile valutare oficiale folosite ca referință stabilă.
2. **Fuelo (fuelo.net) și Peco Online:** Prețurile medii pe rețelele de benzinării din Europa (ex. Petrom, OMV, Rompetrol, Shell, Aral, BP, Repsol, Eni, Total, MOL, etc.).

### Cum se actualizează datele?
- **În Browser (Frontend):** 
  - Datele de prețuri sunt încărcate din fișierul local `data/fuel_data.json` și salvate în LocalStorage. 
  - La pornire, dacă au trecut mai mult de 2 ore de la ultima salvare locală, aplicația re-descarcă `data/fuel_data.json`.
  - Ratele de schimb valutar sunt actualizate live direct din browser apelând API-ul Frankfurter. Cursul EUR/RON este actualizat live, recalculând automat prețurile convertite!
- **În Spatele Scenei (Python Scraper):** 
  - Dezvoltatorul sau administratorul poate rula scriptul de crawling `python scripts/scrape_prices.py` pentru a interoga direct XML-ul BNR și paginile Fuelo.
  - Scriptul actualizează baza de date locală `data/fuel_data.json` cu cele mai proaspete prețuri reale.
  - Dacă un site este temporar indisponibil sau solicitările expiră (timeout), scriptul folosește un sistem inteligent de prețuri de referință (baseline) realiste pentru a nu lăsa aplicația fără date.

---

## 🛠️ Detalii Tehnice de Rulare

Aplicația este construită pe o arhitectură statică, fără dependințe complexe de server:
- **HTML5 & Vanilla Javascript (ES6+)**
- **Modern CSS (Custom Properties, Flexbox, CSS Grid)**
- **Frankfurter API** pentru cursul valutar în timp real.
- **Python 3** pentru scriptul de crawling.

### Lansare Rapidă în Windows 11:
Pentru a porni aplicația și a deschide automat browserul, dați dublu-click pe fișierul:
- `start.bat` (aflat în directorul rădăcină al proiectului).

Acesta va lansa un server web local la `http://localhost:8000` și va deschide pagina principală. Pentru a opri serverul, închideți fereastra de terminal deschisă.

### Actualizarea manuală a bazei de date:
Pentru a actualiza fișierul local de date, deschideți un terminal în directorul proiectului și rulați:
```bash
python scripts/scrape_prices.py
```
Datele noi se vor scrie automat în `data/fuel_data.json` și vor fi încărcate în browser la următoarea reîmprospătare a paginii (dacă intervalul de cache de 2 ore a expirat sau dacă ștergeți LocalStorage-ul).

### Găzduire și Actualizare Automată în Home Assistant:
Dacă găzduiți aplicația local pe un server **Home Assistant** (de exemplu, pe un Intel NUC servit prin NGINX), puteți programa actualizarea automată a prețurilor în fiecare dimineață direct prin sistemul de automatizări din Home Assistant.

Deoarece scriptul `scrape_prices.py` folosește exclusiv librării standard Python (nu are dependențe externe), acesta poate rula nativ în containerul Home Assistant.

#### 1. Definirea comenzii în `configuration.yaml`
Adăugați comanda shell în fișierul de configurare al Home Assistant (ajustați calea în funcție de locația dosarului pe serverul dumneavoastră, ex. în `/config/www/`, `/share/` sau `/media/`):
```yaml
shell_command:
  update_euro_fuel_prices: "python3 /share/webserver/euro_fuel/scripts/scrape_prices.py"
```

#### 2. Crearea automatizării în Home Assistant
Creați o automatizare în Home Assistant (YAML) care rulează scriptul zilnic la ora 07:00 sau când pornește sistemul:
```yaml
alias: "Actualizare prețuri carburanți (EuroFuel)"
description: "Actualizează baza de date EuroFuel la ora 07:00 și la pornirea Home Assistant"
trigger:
  - platform: time
    at: "07:00:00"
action:
  - action: shell_command.update_euro_fuel_prices
mode: single
```

---

**@ concept și realizare vlad39**