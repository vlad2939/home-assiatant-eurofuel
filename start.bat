@echo off
:: Configurare setari de codificare UTF-8 pentru terminal
chcp 65001 > nul
title EuroFuel Compare - Launcher

echo ========================================================
echo   EUROFUEL COMPARE - LANSARE APLICATIE (Windows 11)
echo ========================================================
echo.
echo [1] Pornire server local Python pe portul 8000...
echo.

:: Deschide browserul dupa o mica intarziere de 1 secunda pentru a asigura pornirea serverului
start /b cmd /c "timeout /t 1 >nul && start http://localhost:8000"

echo [2] Aplicatia a fost lansata in browser!
echo.
echo * IMPORTANT:
echo   - NU inchideti aceasta fereastra cat timp folositi aplicatia.
echo   - Pentru a opri serverul si aplicatia, inchideti ACEASTA fereastra
echo     sau apasati Ctrl+C in terminal.
echo ========================================================
echo.

:: Rulam serverul local Python in mod blocant pe portul 8000
python -m http.server 8000
