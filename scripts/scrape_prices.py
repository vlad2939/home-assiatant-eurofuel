#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Concept și realizare: vlad39
Script de colectare a datelor despre prețurile carburanților în Europa continentală.
Acest script descarcă cursurile valutare oficiale de la BNR și parcurge site-urile 
Fuelo subdomeniu cu subdomeniu pentru a extrage cele mai recente prețuri de la 
top 4 benzinării din fiecare țară. În caz de eroare de rețea sau timeout, se folosesc
valori de referință (baseline) realiste pentru a asigura un JSON valid și complet.
"""

import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
import re
import json
import time
import os
import sys
from datetime import datetime

# Safe print for Windows terminal to avoid UnicodeEncodeErrors with diacritics
def safe_print(*args, **kwargs):
    msg = " ".join(str(arg) for arg in args)
    try:
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()
    except UnicodeEncodeError:
        clean_msg = msg.encode('ascii', 'ignore').decode('ascii')
        sys.stdout.write(clean_msg + "\n")
        sys.stdout.flush()

print = safe_print

# Structura țărilor continentale de interes cu subdomenii și date de referință (baseline)
COUNTRIES_CONFIG = {
    "ro": {
        "name": "România",
        "subdomain": "ro.fuelo.net",
        "currency": "RON",
        "symbol": "lei",
        "baseline": [
            {"name": "Petrom", "petrol": 7.15, "diesel": 7.35},
            {"name": "Lukoil", "petrol": 7.20, "diesel": 7.40},
            {"name": "OMV", "petrol": 7.32, "diesel": 7.52},
            {"name": "MOL", "petrol": 7.25, "diesel": 7.45}
        ]
    },
    "de": {
        "name": "Germania",
        "subdomain": "de.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Aral", "petrol": 1.89, "diesel": 1.79},
            {"name": "Shell", "petrol": 1.92, "diesel": 1.82},
            {"name": "Esso", "petrol": 1.87, "diesel": 1.77},
            {"name": "Total", "petrol": 1.86, "diesel": 1.76}
        ]
    },
    "fr": {
        "name": "Franța",
        "subdomain": "fr.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "TotalEnergies", "petrol": 1.88, "diesel": 1.78},
            {"name": "E.Leclerc", "petrol": 1.75, "diesel": 1.65},
            {"name": "Carrefour", "petrol": 1.78, "diesel": 1.68},
            {"name": "Esso", "petrol": 1.82, "diesel": 1.72}
        ]
    },
    "it": {
        "name": "Italia",
        "subdomain": "it.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Eni", "petrol": 1.89, "diesel": 1.79},
            {"name": "IP", "petrol": 1.86, "diesel": 1.76},
            {"name": "Q8", "petrol": 1.87, "diesel": 1.77},
            {"name": "Tamoil", "petrol": 1.82, "diesel": 1.72}
        ]
    },
    "es": {
        "name": "Spania",
        "subdomain": "es.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Repsol", "petrol": 1.68, "diesel": 1.58},
            {"name": "Cepsa", "petrol": 1.65, "diesel": 1.55},
            {"name": "BP", "petrol": 1.69, "diesel": 1.59},
            {"name": "Galp", "petrol": 1.62, "diesel": 1.52}
        ]
    },
    "bg": {
        "name": "Bulgaria",
        "subdomain": "bg.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Lukoil", "petrol": 1.54, "diesel": 1.58},
            {"name": "OMV", "petrol": 1.56, "diesel": 1.59},
            {"name": "Shell", "petrol": 1.55, "diesel": 1.58},
            {"name": "EKO", "petrol": 1.56, "diesel": 1.60}
        ]
    },
    "hu": {
        "name": "Ungaria",
        "subdomain": "hu.fuelo.net",
        "currency": "HUF",
        "symbol": "Ft",
        "baseline": [
            {"name": "MOL", "petrol": 620.0, "diesel": 630.0},
            {"name": "OMV", "petrol": 630.0, "diesel": 640.0},
            {"name": "Shell", "petrol": 625.0, "diesel": 635.0},
            {"name": "Lukoil", "petrol": 615.0, "diesel": 625.0}
        ]
    },
    "pl": {
        "name": "Polonia",
        "subdomain": "pl.fuelo.net",
        "currency": "PLN",
        "symbol": "zł",
        "baseline": [
            {"name": "Orlen", "petrol": 6.55, "diesel": 6.65},
            {"name": "BP", "petrol": 6.62, "diesel": 6.72},
            {"name": "Shell", "petrol": 6.68, "diesel": 6.78},
            {"name": "Circle K", "petrol": 6.58, "diesel": 6.68}
        ]
    },
    "cz": {
        "name": "Cehia",
        "subdomain": "cz.fuelo.net",
        "currency": "CZK",
        "symbol": "Kč",
        "baseline": [
            {"name": "Orlen Benzina", "petrol": 38.5, "diesel": 37.8},
            {"name": "MOL", "petrol": 39.2, "diesel": 38.5},
            {"name": "OMV", "petrol": 39.5, "diesel": 38.8},
            {"name": "Shell", "petrol": 39.8, "diesel": 39.1}
        ]
    },
    "at": {
        "name": "Austria",
        "subdomain": "at.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "OMV", "petrol": 1.68, "diesel": 1.66},
            {"name": "Shell", "petrol": 1.72, "diesel": 1.70},
            {"name": "BP", "petrol": 1.70, "diesel": 1.68},
            {"name": "Jet", "petrol": 1.62, "diesel": 1.58}
        ]
    },
    "be": {
        "name": "Belgia",
        "subdomain": "be.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "TotalEnergies", "petrol": 1.78, "diesel": 1.82},
            {"name": "Shell", "petrol": 1.81, "diesel": 1.85},
            {"name": "Q8", "petrol": 1.75, "diesel": 1.79},
            {"name": "Esso", "petrol": 1.76, "diesel": 1.80}
        ]
    },
    "nl": {
        "name": "Olanda",
        "subdomain": "nl.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Shell", "petrol": 1.98, "diesel": 1.78},
            {"name": "BP", "petrol": 1.95, "diesel": 1.75},
            {"name": "Esso", "petrol": 1.92, "diesel": 1.72},
            {"name": "Total", "petrol": 1.89, "diesel": 1.69}
        ]
    },
    "sk": {
        "name": "Slovacia",
        "subdomain": "sk.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Slovnaft", "petrol": 1.64, "diesel": 1.58},
            {"name": "OMV", "petrol": 1.68, "diesel": 1.62},
            {"name": "Shell", "petrol": 1.67, "diesel": 1.61},
            {"name": "Jurki", "petrol": 1.58, "diesel": 1.52}
        ]
    },
    "gr": {
        "name": "Grecia",
        "subdomain": "gr.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "EKO", "petrol": 1.92, "diesel": 1.68},
            {"name": "Shell", "petrol": 1.96, "diesel": 1.72},
            {"name": "BP", "petrol": 1.95, "diesel": 1.71},
            {"name": "Aegean", "petrol": 1.89, "diesel": 1.65}
        ]
    },
    "pt": {
        "name": "Portugalia",
        "subdomain": "pt.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Galp", "petrol": 1.76, "diesel": 1.62},
            {"name": "Repsol", "petrol": 1.74, "diesel": 1.60},
            {"name": "BP", "petrol": 1.78, "diesel": 1.64},
            {"name": "Prio", "petrol": 1.65, "diesel": 1.52}
        ]
    },
    "hr": {
        "name": "Croația",
        "subdomain": "hr.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "INA", "petrol": 1.56, "diesel": 1.50},
            {"name": "Petrol", "petrol": 1.58, "diesel": 1.52},
            {"name": "Crodux", "petrol": 1.59, "diesel": 1.53},
            {"name": "Lukoil", "petrol": 1.55, "diesel": 1.49}
        ]
    },
    "rs": {
        "name": "Serbia",
        "subdomain": "rs.fuelo.net",
        "currency": "RSD",
        "symbol": "дин.",
        "baseline": [
            {"name": "NIS Petrol", "petrol": 192.0, "diesel": 202.0},
            {"name": "OMV", "petrol": 198.0, "diesel": 208.0},
            {"name": "Lukoil", "petrol": 195.0, "diesel": 205.0},
            {"name": "MOL", "petrol": 197.0, "diesel": 207.0}
        ]
    },
    "si": {
        "name": "Slovenia",
        "subdomain": "si.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Petrol", "petrol": 1.54, "diesel": 1.48},
            {"name": "MOL", "petrol": 1.55, "diesel": 1.49},
            {"name": "Shell", "petrol": 1.58, "diesel": 1.52},
            {"name": "MaxEN", "petrol": 1.52, "diesel": 1.45}
        ]
    },
    "md": {
        "name": "Moldova",
        "subdomain": "md.fuelo.net",
        "currency": "MDL",
        "symbol": "L",
        "baseline": [
            {"name": "Petrom", "petrol": 24.50, "diesel": 21.20},
            {"name": "Rompetrol", "petrol": 24.80, "diesel": 21.50},
            {"name": "Lukoil", "petrol": 24.60, "diesel": 21.30},
            {"name": "Bemol", "petrol": 24.40, "diesel": 21.10}
        ]
    },
    "me": {
        "name": "Muntenegru",
        "subdomain": "me.fuelo.net",
        "currency": "EUR",
        "symbol": "€",
        "baseline": [
            {"name": "Jugopetrol", "petrol": 1.58, "diesel": 1.42},
            {"name": "Petrol", "petrol": 1.59, "diesel": 1.43},
            {"name": "Lukoil", "petrol": 1.57, "diesel": 1.41},
            {"name": "Kalamper", "petrol": 1.56, "diesel": 1.40}
        ]
    },
    "mk": {
        "name": "Macedonia",
        "subdomain": "mk.fuelo.net",
        "currency": "MKD",
        "symbol": "ден",
        "baseline": [
            {"name": "Makpetrol", "petrol": 81.50, "diesel": 72.50},
            {"name": "OKTA", "petrol": 82.00, "diesel": 73.00},
            {"name": "Lukoil", "petrol": 81.80, "diesel": 72.80},
            {"name": "Detoil", "petrol": 81.20, "diesel": 72.20}
        ]
    }
}

# Cursuri valutare implicite în caz că interogarea BNR XML eșuează
DEFAULT_EXCHANGE_RATES = {
    "EUR": 5.2380,
    "USD": 4.5124,
    "CHF": 5.6891,
    "CZK": 0.2170,
    "DKK": 0.7008,
    "HUF": 0.014944, # valoare unitară (1 HUF = 0.014944 RON)
    "NOK": 0.4744,
    "PLN": 1.2341,
    "RSD": 0.0446,
    "SEK": 0.4812,
    "MDL": 0.2603,
    "MKD": 0.0851  # calculat ca EUR / 61.5
}

def get_html(url, timeout=6):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode('utf-8', errors='ignore')

def fetch_bnr_rates():
    print("Se descarcă cursurile valutare BNR XML...")
    url = "https://www.bnr.ro/nbrfxrates.xml"
    rates = {}
    try:
        xml_content = get_html(url, timeout=5)
        root = ET.fromstring(xml_content.encode('utf-8'))
        ns = {'ns': 'http://www.bnr.ro/xsd'}
        
        # Extrage data publicării
        pub_date_elem = root.find('.//ns:PublishingDate', ns)
        pub_date = pub_date_elem.text if pub_date_elem is not None else datetime.now().strftime("%Y-%m-%d")
        print(f"Data publicării cursului BNR: {pub_date}")
        
        for rate_elem in root.findall('.//ns:Rate', ns):
            currency = rate_elem.attrib.get('currency')
            multiplier_str = rate_elem.attrib.get('multiplier', '1')
            multiplier = int(multiplier_str) if multiplier_str else 1
            value = float(rate_elem.text)
            
            # Stocăm rata unitară (de exemplu, pentru 100 HUF împărțim valoarea la 100)
            rates[currency] = value / multiplier
            
        # Adăugăm MKD pegged la EUR
        if "EUR" in rates:
            rates["MKD"] = rates["EUR"] / 61.5
            
        print("Cursurile BNR au fost descărcate cu succes!")
        return rates, pub_date
    except Exception as e:
        print(f"Eroare la descărcarea cursurilor BNR: {e}. Se folosesc cursurile implicite.")
        # Generăm cursurile implicite
        return DEFAULT_EXCHANGE_RATES, datetime.now().strftime("%Y-%m-%d")

def classify_fuel(name):
    name_lower = name.lower()
    petrol_keywords = ["95", "super", "gasoline", "benzin", "fara plumb", "evo", "unleaded", "sans plomb", "sp95", "senza piombo", "98"]
    diesel_keywords = ["diesel", "motorina", "motorină", "gazole", "gasoil", "gasolio", "gas-oil"]
    
    if any(k in name_lower for k in diesel_keywords):
        return "diesel"
    if any(k in name_lower for k in petrol_keywords):
        return "petrol"
    return None

def scrape_brand_prices(subdomain, brand_id, brand_name):
    url = f"https://{subdomain}/brand/id/{brand_id}?lang=ro"
    try:
        html = get_html(url, timeout=5)
        # Căutăm structurile Highcharts: name: '...' și data: [...]
        series_pattern = r"name:\s*'([^']*)'[\s\S]*?data:\s*\[([\d.,\s]+)\]"
        matches = re.findall(series_pattern, html)
        
        petrol_options = []
        diesel_options = []
        
        for name, data_str in matches:
            nums = [float(x.strip()) for x in data_str.split(',') if x.strip()]
            if not nums:
                continue
            latest_price = nums[-1]
            
            fuel_type = classify_fuel(name)
            if fuel_type == "petrol":
                petrol_options.append((name, latest_price))
            elif fuel_type == "diesel":
                diesel_options.append((name, latest_price))
                
        petrol_price = None
        diesel_price = None
        
        if petrol_options:
            # Prioritizăm combustibilul standard de tip 95 sau EVO 95 sau Regular
            standard_petrol = None
            for name, price in petrol_options:
                n_low = name.lower()
                if "95" in name or "e10" in n_low or "regular" in n_low or "evo 95" in n_low or "fara plumb" in n_low:
                    standard_petrol = (name, price)
                    break
            if not standard_petrol:
                standard_petrol = petrol_options[0]
            petrol_price = standard_petrol[1]
            
        if diesel_options:
            # Prioritizăm motorina standard (fără Premium/Superioară/Ultimate)
            standard_diesel = None
            for name, price in diesel_options:
                n_low = name.lower()
                if "premium" not in n_low and "ultimate" not in n_low and ("diesel" in n_low or "motorina" in n_low or "gazole" in n_low):
                    standard_diesel = (name, price)
                    break
            if not standard_diesel:
                standard_diesel = diesel_options[0]
            diesel_price = standard_diesel[1]
            
        return petrol_price, diesel_price
    except Exception as e:
        print(f"    Eroare la scraping brand {brand_name} ({brand_id}): {e}")
        return None, None

def scrape_peco_romania():
    url = "https://www.peco-online.ro/index.php"
    target_brands = {"Petrom": "Petrom", "OMV": "OMV", "Mol": "MOL", "Lukoil": "Lukoil"}
    fuels = {"petrol": "Benzina_Regular", "diesel": "Motorina_Regular"}
    results = {"Petrom": {"petrol": None, "diesel": None},
               "OMV": {"petrol": None, "diesel": None},
               "MOL": {"petrol": None, "diesel": None},
               "Lukoil": {"petrol": None, "diesel": None}}
    
    for fuel_key, fuel_val in fuels.items():
        post_params = [
            ('carburant', fuel_val),
            ('locatie', 'Oras'),
            ('nume_locatie', 'Bucuresti'),
            ('retele[]', 'Petrom'),
            ('retele[]', 'OMV'),
            ('retele[]', 'Mol'),
            ('retele[]', 'Lukoil')
        ]
        
        data = urllib.parse.urlencode(post_params).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            match = re.search(r"var rezultate = JSON.parse\('([^']*)'\)", html)
            if match:
                js_str = match.group(1)
                stations = json.loads(js_str)
                
                # Brand prices lists
                brand_prices = {"Petrom": [], "OMV": [], "Mol": [], "Lukoil": []}
                for station in stations:
                    brand = station[0]
                    if brand in brand_prices:
                        price = float(station[5])
                        brand_prices[brand].append(price)
                        
                for b, prices in brand_prices.items():
                    target_b = target_brands[b] # map "Mol" to "MOL"
                    if prices:
                        results[target_b][fuel_key] = round(sum(prices) / len(prices), 2)
            else:
                print(f"    [Peco Scraper] Nu am putut gasi datele JSON pentru {fuel_key}")
        except Exception as e:
            print(f"    [Peco Scraper] Eroare la conectare pentru {fuel_key}: {e}")
            
    return results

def scrape_country_data(code, config):
    print(f"\n--- Colectare date pentru țara: {config['name'].upper()} ({code.upper()}) ---")
    
    scraped_brands = []
    
    if code == "ro":
        try:
            print("  Colectare date de pe peco-online.ro pentru Romania...")
            peco_data = scrape_peco_romania()
            priority_brands = ["Petrom", "OMV", "MOL", "Lukoil"]
            for brand_name in priority_brands:
                prices = peco_data.get(brand_name, {"petrol": None, "diesel": None})
                petrol = prices["petrol"]
                diesel = prices["diesel"]
                
                # Fallback if scraping failed
                fallback_match = next((fb for fb in config["baseline"] if fb["name"].lower() == brand_name.lower()), None)
                if fallback_match is None:
                    fallback_match = config["baseline"][0]
                    
                final_petrol = petrol if petrol is not None else fallback_match["petrol"]
                final_diesel = diesel if diesel is not None else fallback_match["diesel"]
                
                scraped_brands.append({
                    "brand_name": brand_name,
                    "petrol": final_petrol,
                    "diesel": final_diesel,
                    "source": "Peco Online Live" if (petrol is not None and diesel is not None) else "Fallback Baseline"
                })
                print(f"    {brand_name} - Petrol: {final_petrol} | Diesel: {final_diesel} ({scraped_brands[-1]['source']})")
            return scraped_brands
        except Exception as e:
            print(f"  Eroare la scraping peco-online.ro: {e}. Se folosesc datele din baseline.")
            for fb in config["baseline"]:
                scraped_brands.append({
                    "brand_name": fb["name"],
                    "petrol": fb["petrol"],
                    "diesel": fb["diesel"],
                    "source": "Fallback Baseline"
                })
            return scraped_brands
            
    subdomain = config["subdomain"]
    url = f"https://{subdomain}/?lang=ro"
    
    scraped_brands = []
    
    try:
        html = get_html(url, timeout=5)
        # Extragem brandurile și ID-urile lor de pe pagina principală
        # Format links: href="/brand/id/ID?lang=ro"
        pattern = r'href="/brand/id/(\d+)\?lang=ro".*?alt="(.*?)"'
        matches = re.findall(pattern, html)
        
        discovered_brands = []
        seen = set()
        for b_id, name in matches:
            name = name.strip()
            b_id = int(b_id)
            if name not in seen and name.lower() not in ["gpl", "lpg", "methane", "cng"]:
                seen.add(name)
                discovered_brands.append({"id": b_id, "name": name})
                
        # Selectăm top 4 branduri. Pentru România, prioritizăm: Petrom, OMV, MOL, Lukoil
        if code == "ro":
            priority_names = ["petrom", "omv", "mol", "lukoil", "rompetrol", "socar", "gazprom"]
            discovered_brands.sort(key=lambda b: priority_names.index(b["name"].lower()) if b["name"].lower() in priority_names else 999)

        print(f"  Branduri descoperite pe Fuelo: {[b['name'] for b in discovered_brands[:6]]}")
        
        selected_brands = discovered_brands[:4]
        
        for b in selected_brands:
            print(f"  Scraping prețuri pentru {b['name']} (ID: {b['id']})...")
            time.sleep(0.5) # O mică pauză de politețe
            petrol, diesel = scrape_brand_prices(subdomain, b["id"], b["name"])
            
            # Căutăm fallback-ul pentru acest brand specific în baseline, dacă scraping-ul a returnat None
            fallback_match = next((fb for fb in config["baseline"] if fb["name"].lower() == b["name"].lower()), None)
            if fallback_match is None:
                # Dacă nu avem o potrivire directă după nume, luăm un fallback generic bazat pe primul element
                fallback_match = config["baseline"][0]
                
            final_petrol = petrol if petrol is not None else fallback_match["petrol"]
            final_diesel = diesel if diesel is not None else fallback_match["diesel"]
            
            scraped_brands.append({
                "brand_name": b["name"],
                "petrol": final_petrol,
                "diesel": final_diesel,
                "source": "Fuelo Live" if (petrol is not None and diesel is not None) else "Fallback Baseline"
            })
            print(f"    Petrol: {final_petrol} | Diesel: {final_diesel} ({scraped_brands[-1]['source']})")
            
    except Exception as e:
        print(f"  Eroare la accesarea paginii principale pentru {config['name']}: {e}. Se folosesc datele implicite (baseline).")
        
    # Dacă nu s-au putut colecta branduri suficiente, completăm cu baseline-ul complet
    if len(scraped_brands) < 4:
        # Folosim configurația baseline
        scraped_brands = []
        for fb in config["baseline"]:
            scraped_brands.append({
                "brand_name": fb["name"],
                "petrol": fb["petrol"],
                "diesel": fb["diesel"],
                "source": "Fallback Baseline"
            })
            
    return scraped_brands[:4]

def main():
    start_time = time.time()
    
    # 1. Colectare Cursuri Valutare
    exchange_rates, bnr_date = fetch_bnr_rates()
    
    # 2. Colectare Prețuri Carburanți pentru fiecare țară
    compiled_countries = {}
    for code, config in COUNTRIES_CONFIG.items():
        brands_data = scrape_country_data(code, config)
        compiled_countries[code] = {
            "name": config["name"],
            "subdomain": config["subdomain"],
            "currency": config["currency"],
            "symbol": config["symbol"],
            "brands": brands_data
        }
        
    # 3. Structura finală de date
    output_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bnr_date": bnr_date,
        "exchange_rates": exchange_rates,
        "countries": compiled_countries,
        "concept_author": "vlad39"
    }
    
    # Salvare în folderul data din workspace
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, "data")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    json_path = os.path.join(data_dir, "fuel_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    duration = time.time() - start_time
    print(f"\n=======================================================")
    print(f"Datele au fost salvate cu succes în: {json_path}")
    print(f"Durata totală de rulare: {duration:.2f} secunde")
    print(f"=======================================================")

if __name__ == "__main__":
    main()
