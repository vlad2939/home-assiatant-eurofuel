/**
 * EuroFuel - Comparator Prețuri Carburanți Europa
 * Concept și realizare: vlad39
 * 
 * Logică actualizată pentru a se alinia cu designul din screenshot:
 * 1. Încărcarea datelor (cache LocalStorage, 2 ore).
 * 2. Culegerea cursului live (Frankfurter API, cu MDL/RSD din JSON și MKD pegged la EUR).
 * 3. Gestionarea temei Light / Dark prin butoane rotunde.
 * 4. Actualizarea selectoarelor de țări plasate deasupra coloanelor.
 * 5. Calculul mediei naționale (EUR și RON) și randarea cardurilor.
 * 6. Colorarea prețurilor (verde = cel mai ieftin, roșu = cel mai scump din coloană).
 */

const state = {
    fuelData: null,
    exchangeRates: {},
    selectedCountries: ["ro", "de", "fr", "it"],
    activeFuel: "petrol",
    theme: "light",
    lastFetchTime: null,
    liveRatesDate: null,
    ratesSource: ""
};

const CACHE_KEY = "eurofuel_data_cache";
const CACHE_TIME_KEY = "eurofuel_data_timestamp";
const CACHE_DURATION_MS = 2 * 60 * 60 * 1000;

// Culorile bulinelor pentru rețelele din tabel
const ROW_BULLET_COLORS = ["#ef4444", "#f59e0b", "#3b82f6", "#10b981"];

document.addEventListener("DOMContentLoaded", async () => {
    initTheme();
    setupEventListeners();
    
    // Încărcare date
    const loaded = await loadFuelData(false);
    if (!loaded) {
        showError("Nu s-au putut încărca datele comparative.");
        return;
    }
    
    // Cursuri valutare live
    await fetchLiveExchangeRates();
    
    // Inițializare interfață
    populateDropdowns();
    updateUISelections();
    
    // Randare inițială
    renderComparison();
});

function formatTimeHHMM(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

function formatDateTimeStr(dateTimeStr) {
    if (!dateTimeStr) return "N/A";
    const parts = dateTimeStr.split(" ");
    const dateStr = parts[0];
    const timeStr = parts[1] ? parts[1].substring(0, 5) : "";
    
    const months = [
        "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
        "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"
    ];
    try {
        const dParts = dateStr.split("-");
        if (dParts.length === 3) {
            const year = dParts[0];
            const monthIdx = parseInt(dParts[1]) - 1;
            const day = parseInt(dParts[2]);
            return `${day} ${months[monthIdx]} ${year} ${timeStr}`;
        }
    } catch(e) {}
    return dateTimeStr;
}

/**
 * Încarcă datele de carburant din LocalStorage sau descarcă fuel_data.json
 * @param {boolean} forceRefresh - Dacă este true, ignoră cache-ul și re-descarcă fișierul
 */
async function loadFuelData(forceRefresh = false) {
    const cachedData = localStorage.getItem(CACHE_KEY);
    const cachedTimestamp = localStorage.getItem(CACHE_TIME_KEY);
    const now = Date.now();
    
    if (!forceRefresh && cachedData && cachedTimestamp && (now - parseInt(cachedTimestamp) < CACHE_DURATION_MS)) {
        state.fuelData = JSON.parse(cachedData);
        state.lastFetchTime = formatTimeHHMM(new Date(parseInt(cachedTimestamp)));
        state.exchangeRates = { ...state.fuelData.exchange_rates };
        updateHeaderDate(state.fuelData.last_updated.split(" ")[0]);
        return true;
    }
    
    try {
        const response = await fetch("data/fuel_data.json?t=" + now);
        if (!response.ok) throw new Error("Eroare fetch date.");
        const data = await response.json();
        
        state.fuelData = data;
        state.exchangeRates = { ...data.exchange_rates };
        state.lastFetchTime = formatTimeHHMM(new Date());
        
        localStorage.setItem(CACHE_KEY, JSON.stringify(data));
        localStorage.setItem(CACHE_TIME_KEY, now.toString());
        
        updateHeaderDate(data.last_updated.split(" ")[0]);
        return true;
    } catch (e) {
        console.error(e);
        if (cachedData) {
            state.fuelData = JSON.parse(cachedData);
            state.exchangeRates = { ...state.fuelData.exchange_rates };
            state.lastFetchTime = cachedTimestamp ? formatTimeHHMM(new Date(parseInt(cachedTimestamp))) : "N/A";
            updateHeaderDate(state.fuelData.last_updated.split(" ")[0]);
            return true;
        }
        return false;
    }
}

function updateHeaderDate(dateStr) {
    const dateLabel = document.getElementById("date-label");
    if (!dateLabel) return;
    
    if (dateStr) {
        // Transformare format YYYY-MM-DD în format românesc (ex: 15 Iunie 2026)
        const months = [
            "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
            "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"
        ];
        try {
            const parts = dateStr.split("-");
            if (parts.length === 3) {
                const year = parts[0];
                const monthIdx = parseInt(parts[1]) - 1;
                const day = parseInt(parts[2]);
                dateLabel.textContent = `Date: ${day} ${months[monthIdx]} ${year}`;
                return;
            }
        } catch(e) {}
        dateLabel.textContent = `Date: ${dateStr}`;
    } else {
        dateLabel.textContent = "Date: Curent";
    }
}

/**
 * Cursuri live din Frankfurter API
 */
async function fetchLiveExchangeRates() {
    const symbols = "RON,HUF,PLN,CZK,SEK,DKK,CHF,NOK";
    try {
        const response = await fetch(`https://api.frankfurter.dev/v1/latest?base=EUR&symbols=${symbols}`);
        if (!response.ok) throw new Error("Frankfurter API error");
        const data = await response.json();
        
        const eurInRon = data.rates.RON;
        state.exchangeRates["EUR"] = eurInRon;
        
        state.exchangeRates["HUF"] = eurInRon / data.rates.HUF;
        state.exchangeRates["PLN"] = eurInRon / data.rates.PLN;
        state.exchangeRates["CZK"] = eurInRon / data.rates.CZK;
        state.exchangeRates["CHF"] = eurInRon / data.rates.CHF;
        state.exchangeRates["SEK"] = eurInRon / data.rates.SEK;
        state.exchangeRates["NOK"] = eurInRon / data.rates.NOK;
        state.exchangeRates["DKK"] = eurInRon / data.rates.DKK;
        state.exchangeRates["MKD"] = eurInRon / 61.5;
        
        // Menținem restul (MDL, RSD) din fuel_data.json
        state.liveRatesDate = data.date;
        state.ratesSource = "Frankfurter API (BCE Live)";
    } catch (e) {
        state.liveRatesDate = state.fuelData.bnr_date || "N/A";
        state.ratesSource = "BNR XML de referință (stocare locală)";
    }
}

// --- Conversii Valutare ---

function convertPrice(value, fromCurrency) {
    let priceInLocal = value;
    let priceInEur = 0;
    let priceInRon = 0;
    
    const eurInRon = state.exchangeRates["EUR"] || 5.2380;
    
    if (fromCurrency === "RON") {
        priceInRon = value;
        priceInEur = value / eurInRon;
    } else if (fromCurrency === "EUR") {
        priceInEur = value;
        priceInRon = value * eurInRon;
    } else {
        const localInRon = state.exchangeRates[fromCurrency];
        if (localInRon) {
            priceInRon = value * localInRon;
            priceInEur = priceInRon / eurInRon;
        } else {
            // Peg-uri speciale
            if (fromCurrency === "MKD") {
                priceInEur = value / 61.5;
                priceInRon = priceInEur * eurInRon;
            } else {
                priceInRon = 0;
                priceInEur = 0;
            }
        }
    }
    
    return {
        local: priceInLocal,
        eur: priceInEur,
        ron: priceInRon
    };
}

// --- Selectoare UI ---

function populateDropdowns() {
    const countries = state.fuelData.countries;
    const selectIds = ["country-select-1", "country-select-2", "country-select-3", "country-select-4"];
    
    selectIds.forEach((selectId, index) => {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        select.innerHTML = "";
        
        // Sortăm țările după nume pentru selectoare ordonate
        const sortedCodes = Object.keys(countries).sort((a, b) => 
            countries[a].name.localeCompare(countries[b].name)
        );
        
        sortedCodes.forEach(code => {
            const option = document.createElement("option");
            option.value = code;
            // Format format: RO România, DE Germania, etc.
            option.textContent = `${code.toUpperCase()} ${countries[code].name}`;
            select.appendChild(option);
        });
        
        select.value = state.selectedCountries[index];
    });
}

function updateUISelections() {
    const selectIds = ["country-select-1", "country-select-2", "country-select-3", "country-select-4"];
    
    selectIds.forEach((selectId, index) => {
        const select = document.getElementById(selectId);
        if (select) {
            state.selectedCountries[index] = select.value;
        }
    });
    
    selectIds.forEach((selectId, index) => {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        Array.from(select.options).forEach(option => {
            const val = option.value;
            const isSelectedElsewhere = state.selectedCountries.some((selectedCode, idx) => {
                return selectedCode === val && idx !== index;
            });
            option.disabled = isSelectedElsewhere;
        });
    });
}

// --- Setup Evenimente ---

function setupEventListeners() {
    // Selectoare țări
    const selectIds = ["country-select-1", "country-select-2", "country-select-3", "country-select-4"];
    selectIds.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.addEventListener("change", () => {
                updateUISelections();
                renderComparison();
            });
        }
    });
    
    // Butoane combustibil (Benzină / Motorină pe aceeași linie)
    const petrolBtn = document.getElementById("fuel-petrol-btn");
    const dieselBtn = document.getElementById("fuel-diesel-btn");
    if (petrolBtn && dieselBtn) {
        petrolBtn.addEventListener("click", () => {
            if (state.activeFuel !== "petrol") {
                state.activeFuel = "petrol";
                petrolBtn.classList.add("active");
                dieselBtn.classList.remove("active");
                updateSubtitles();
                renderComparison();
            }
        });
        
        dieselBtn.addEventListener("click", () => {
            if (state.activeFuel !== "diesel") {
                state.activeFuel = "diesel";
                dieselBtn.classList.add("active");
                petrolBtn.classList.remove("active");
                updateSubtitles();
                renderComparison();
            }
        });
    }
    
    // Buton Refresh
    const refreshBtn = document.getElementById("refresh-data-btn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", async () => {
            refreshBtn.classList.add("fa-spin-once");
            // Forțăm reîncărcarea datelor
            const loaded = await loadFuelData(true);
            if (loaded) {
                await fetchLiveExchangeRates();
                renderComparison();
                // Animare de succes
                showNotification("Datele au fost reîmprospătate!");
            } else {
                showNotification("Eroare la reîmprospătarea datelor.");
            }
            setTimeout(() => refreshBtn.classList.remove("fa-spin-once"), 600);
        });
    }
    
    // Buton Temă (Moon/Sun)
    const themeBtn = document.getElementById("theme-toggle-btn");
    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            const newTheme = state.theme === "light" ? "dark" : "light";
            setTheme(newTheme);
        });
    }
    
    // Modal README
    const authorBtn = document.getElementById("author-popup-trigger");
    const modalOverlay = document.getElementById("readme-modal-overlay");
    const modalClose = document.getElementById("modal-close-btn");
    
    if (authorBtn && modalOverlay) {
        authorBtn.addEventListener("click", () => {
            openReadmeModal();
        });
    }
    
    if (modalClose && modalOverlay) {
        modalClose.addEventListener("click", () => {
            modalOverlay.classList.remove("active");
        });
        modalOverlay.addEventListener("click", (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.classList.remove("active");
            }
        });
    }
}



function updateSubtitles() {
    const brandSubtitle = document.getElementById("brand-subtitle");
    const sectionSubtitle = document.getElementById("section-subtitle");
    
    if (state.activeFuel === "petrol") {
        if (brandSubtitle) brandSubtitle.textContent = "COMPARATOR PREȚURI BENZINĂ - EUROPA";
        if (sectionSubtitle) sectionSubtitle.textContent = "Alege până la 4 țări din Europa continentală pentru a compara prețurile la benzină Euro 95";
    } else {
        if (brandSubtitle) brandSubtitle.textContent = "COMPARATOR PREȚURI MOTORINĂ - EUROPA";
        if (sectionSubtitle) sectionSubtitle.textContent = "Alege până la 4 țări din Europa continentală pentru a compara prețurile la motorină";
    }
}

function setTheme(theme) {
    state.theme = theme;
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("eurofuel_theme", theme);
    
    const themeIcon = document.getElementById("theme-btn-icon");
    if (themeIcon) {
        if (theme === "dark") {
            themeIcon.className = "fas fa-sun";
        } else {
            themeIcon.className = "fas fa-moon";
        }
    }
}

function initTheme() {
    const savedTheme = localStorage.getItem("eurofuel_theme");
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    
    state.theme = savedTheme || (systemPrefersDark ? "dark" : "light");
    setTheme(state.theme);
}

// --- Randare Coloane Comparativ ---

function renderComparison() {
    const fuelBadgeText = state.activeFuel === "petrol" ? "BENZINĂ 95" : "MOTORINĂ";
    const fuelLabelText = state.activeFuel === "petrol" ? "BENZINĂ 95" : "MOTORINĂ";
    
    state.selectedCountries.forEach((countryCode, index) => {
        const cardContainer = document.getElementById(`country-card-${index + 1}`);
        if (!cardContainer) return;
        
        cardContainer.innerHTML = "";
        
        const countryData = state.fuelData.countries[countryCode];
        if (!countryData) return;
        
        // 1. Calculăm media națională a celor 4 benzinării
        const prices = countryData.brands.map(b => 
            state.activeFuel === "petrol" ? b.petrol : b.diesel
        );
        const avgLocal = prices.reduce((sum, p) => sum + p, 0) / prices.length;
        
        // Convertim media națională
        const avgConverted = convertPrice(avgLocal, countryData.currency);
        const formattedAvgEur = avgConverted.eur.toFixed(3);
        const formattedAvgRon = avgConverted.ron.toFixed(3);
        
        // 2. Aflăm min și max din listă pentru color-coding în coloană
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        
        // 3. Generare rânduri tabel
        let rowsHTML = "";
        countryData.brands.forEach((brand, idx) => {
            const rawPrice = state.activeFuel === "petrol" ? brand.petrol : brand.diesel;
            const converted = convertPrice(rawPrice, countryData.currency);
            
            // Verificare min/max pentru color-coding
            let colorClass = "";
            if (rawPrice === minPrice) {
                colorClass = "price-min"; // verde
            } else if (rawPrice === maxPrice) {
                colorClass = "price-max"; // roșu
            }
            
            const formattedLocal = formatVal(converted.local, countryData.currency);
            const formattedEur = formatVal(converted.eur, "EUR");
            const formattedRon = formatVal(converted.ron, "RON");
            
            const bulletColor = ROW_BULLET_COLORS[idx % ROW_BULLET_COLORS.length];
            
            rowsHTML += `
                <tr>
                    <td class="brand-name-cell">
                        <span class="brand-bullet" style="background-color: ${bulletColor}"></span>
                        <span class="brand-name-text">${brand.brand_name}</span>
                    </td>
                    <td class="price-cell">
                        <div class="price-num ${colorClass}">${formattedLocal}</div>
                        <div class="price-unit">${countryData.currency}</div>
                    </td>
                    <td class="price-cell">
                        <div class="price-num ${colorClass}">${formattedEur}</div>
                        <div class="price-unit">EUR</div>
                    </td>
                    <td class="price-cell">
                        <div class="price-num ${colorClass}">${formattedRon}</div>
                        <div class="price-unit">RON</div>
                    </td>
                </tr>
            `;
        });
        
        // 4. HTML complet pentru Cardul Țării
        const cardHTML = `
            <div class="country-card animate-fade-in">
                <!-- Card Header -->
                <div class="card-header">
                    <div class="header-left">
                        <span class="country-code">${countryCode.toUpperCase()}</span>
                        <div class="header-text-group">
                            <h3 class="country-title">${countryData.name.toUpperCase()}</h3>
                            <span class="moneda-label">MONEDĂ: ${countryData.currency}</span>
                        </div>
                    </div>
                    <span class="fuel-badge">${fuelBadgeText}</span>
                </div>
                
                <!-- National Average Box -->
                <div class="national-average-box">
                    <div class="avg-label-group">
                        <span class="avg-label-title">MEDIE NAȚIONALĂ</span>
                        <span class="avg-label-subtitle">${fuelLabelText}</span>
                    </div>
                    <div class="avg-value-group">
                        <span class="avg-large-val">${formattedAvgEur}</span>
                        <span class="avg-small-group">
                            <span class="avg-small-top">€/L - ${formattedAvgRon}</span>
                            <span class="avg-small-bottom">RON/L</span>
                        </span>
                    </div>
                </div>
                
                <!-- Top 4 Stations Table -->
                <div class="brand-table-section">
                    <div class="brand-table-title">TOP 4 BENZINĂRII • ${fuelLabelText}</div>
                    <table class="brand-table">
                        <thead>
                            <tr>
                                <th class="th-left">REȚEA</th>
                                <th class="th-right">${countryData.currency}/L</th>
                                <th class="th-right">€/L</th>
                                <th class="th-right">RON/L</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHTML}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        cardContainer.innerHTML = cardHTML;
    });
    
    updateInfoBar();
}

/**
 * Formatare număr în funcție de monedă
 */
function formatVal(value, code) {
    let decimals = (code === "HUF" || code === "RSD") ? 1 : 3;
    return value.toFixed(decimals);
}

function updateInfoBar() {
    const infoContainer = document.getElementById("info-bar-container");
    if (!infoContainer) return;
    
    const bnrDate = state.fuelData.bnr_date || "N/A";
    const liveDate = state.liveRatesDate || bnrDate;
    const source = state.ratesSource || "N/A";
    const eurInRon = state.exchangeRates["EUR"] ? state.exchangeRates["EUR"].toFixed(4) : "N/A";
    
    infoContainer.innerHTML = `
        <div class="info-bar animate-fade-in">
            <div class="info-bar-header">
                <i class="fas fa-info-circle"></i> Metadate & Curs Valutar
            </div>
            <div class="info-bar-grid">
                <div class="info-item">
                    <span class="info-item-label">Sursă Curs Valutar</span>
                    <span class="info-item-value">${source}</span>
                </div>
                <div class="info-item">
                    <span class="info-item-label">Curs EUR/RON utilizat</span>
                    <span class="info-item-value">1 EUR = ${eurInRon} lei (Data: ${liveDate})</span>
                </div>
                <div class="info-item">
                    <span class="info-item-label">Actualizare date carburant</span>
                    <span class="info-item-value">${formatDateTimeStr(state.fuelData.last_updated)} (Scraper backend)</span>
                </div>
                <div class="info-item">
                    <span class="info-item-label">Status cache LocalStorage</span>
                    <span class="info-item-value">Salvat local în browser. Ultimul import: ${state.lastFetchTime}</span>
                </div>
            </div>
        </div>
    `;
}

function showError(msg) {
    const grid = document.getElementById("comparison-grid-container");
    if (grid) {
        grid.innerHTML = `<div style="grid-column: span 4; padding: 2rem; background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger-color); border-radius: 12px; color: var(--danger-color); text-align: center; font-weight: 600;">Eroare: ${msg}</div>`;
    }
}

function showNotification(text) {
    // Creează o notificare temporară plutitoare
    const notification = document.createElement("div");
    notification.className = "toast-notification";
    notification.textContent = text;
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add("active"), 50);
    setTimeout(() => {
        notification.classList.remove("active");
        setTimeout(() => notification.remove(), 400);
    }, 2500);
}

// --- Modal README & Parser Markdown ---

async function openReadmeModal() {
    const modalOverlay = document.getElementById("readme-modal-overlay");
    const modalBody = document.getElementById("readme-modal-body");
    
    if (!modalOverlay || !modalBody) return;
    
    modalBody.innerHTML = `<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin fa-2x" style="color: var(--primary-color)"></i><p style="margin-top: 1rem; font-weight: 600;">Se încarcă documentația...</p></div>`;
    modalOverlay.classList.add("active");
    
    try {
        const response = await fetch("README.md");
        if (!response.ok) throw new Error("Nu s-a putut citi fișierul README.md");
        const markdown = await response.text();
        
        const html = parseMarkdown(markdown);
        modalBody.innerHTML = `<div class="markdown-body">${html}</div>`;
    } catch (e) {
        modalBody.innerHTML = `<div style="color: var(--danger-color); text-align: center; padding: 2rem; font-weight: 600;"><i class="fas fa-exclamation-triangle fa-2x"></i><p style="margin-top: 1rem;">Eroare la încărcarea documentației: ${e.message}</p></div>`;
    }
}

function parseMarkdown(md) {
    let text = md.replace(/\r\n/g, "\n");
    
    // 1. Extrae blocurile de cod ca să nu fie alterate de alți parseri (cum e cel de liste sau paragrafe)
    const codeBlocks = [];
    text = text.replace(/```([a-zA-Z0-9_-]+)?\n([\s\S]*?)\n```/g, (match, lang, code) => {
        const placeholder = `__CODE_BLOCK_PLACEHOLDER_${codeBlocks.length}__`;
        codeBlocks.push(`<pre><code>${code}</code></pre>`);
        return placeholder;
    });
    
    // 2. Alți înlocuitori simpli
    text = text.replace(/>\s*\[!NOTE\]\s*\n([\s\S]*?)(?=\n\n|\n[^\s>])/g, '<div style="background: rgba(var(--primary-rgb), 0.08); border-left: 4px solid var(--primary-color); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; font-weight: 500;"><strong>NOTĂ:</strong><br>$1</div>');
    text = text.replace(/>\s*\[!IMPORTANT\]\s*\n([\s\S]*?)(?=\n\n|\n[^\s>])/g, '<div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; font-weight: 500;"><strong>IMPORTANT:</strong><br>$1</div>');
    text = text.replace(/>\s*\[!TIP\]\s*\n([\s\S]*?)(?=\n\n|\n[^\s>])/g, '<div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid var(--accent-color); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; font-weight: 500;"><strong>RECOMANDARE:</strong><br>$1</div>');
    
    text = text.replace(/^>\s*(.*)$/gm, '<blockquote>$1</blockquote>');
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    text = text.replace(/^# (.*)$/gm, '<h1>$1</h1>');
    text = text.replace(/^## (.*)$/gm, '<h2>$1</h2>');
    text = text.replace(/^### (.*)$/gm, '<h3>$1</h3>');
    text = text.replace(/^#### (.*)$/gm, '<h4>$1</h4>');
    text = text.replace(/^##### (.*)$/gm, '<h5>$1</h5>');
    
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // 3. Procesare liste linie cu linie
    const lines = text.split("\n");
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trim();
        if (line.startsWith("- ")) {
            let content = line.substring(2);
            if (!inList) {
                lines[i] = "<ul><li>" + content + "</li>";
                inList = true;
            } else {
                lines[i] = "<li>" + content + "</li>";
            }
        } else {
            if (inList) {
                lines[i - 1] = lines[i - 1] + "</ul>";
                inList = false;
            }
        }
    }
    if (inList) {
        lines[lines.length - 1] = lines[lines.length - 1] + "</ul>";
    }
    text = lines.join("\n");
    
    text = text.replace(/^---$/gm, '<hr>');
    
    // 4. Paragrafe (grupate după linii goale)
    text = text.split(/\n\n+/).map(para => {
        para = para.trim();
        if (!para) return "";
        // Nu împachetăm în <p> dacă începe cu un tag bloc sau placeholder de cod
        if (para.startsWith("<h") || para.startsWith("<ul") || para.startsWith("<ol") || para.startsWith("<pre") || para.startsWith("<div") || para.startsWith("<blockquote") || para.startsWith("<hr") || para.startsWith("__CODE_BLOCK_PLACEHOLDER_")) {
            return para;
        }
        return `<p>${para}</p>`;
    }).join("\n");
    
    // 5. Punem înapoi blocurile de cod originale
    codeBlocks.forEach((codeHtml, idx) => {
        text = text.replace(`__CODE_BLOCK_PLACEHOLDER_${idx}__`, codeHtml);
    });
    
    return text;
}
