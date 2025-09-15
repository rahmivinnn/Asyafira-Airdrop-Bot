@echo off
echo ========================================
echo     ASYAFIRA AIRDROP BOT - EXE VERSION
echo ========================================
echo.
echo Pilihan:
echo 1. Run sekali (immediate claim)
echo 2. Schedule harian
echo 3. Schedule waktu tertentu
echo 4. Test Telegram
echo 5. Validasi config
echo 6. Help
echo.
set /p choice="Pilih opsi (1-6): "

if "%choice%"=="1" goto run_once
if "%choice%"=="2" goto daily
if "%choice%"=="3" goto schedule
if "%choice%"=="4" goto test_telegram
if "%choice%"=="5" goto validate
if "%choice%"=="6" goto help
goto invalid

:run_once
echo.
echo Running bot once (URL will be auto-extracted from cookie)...
dist\AsyafiraAirdropBot.exe --run-once
pause
goto end

:daily_schedule
echo.
set /p time="Masukkan waktu (HH:MM): "
echo.
echo Starting daily schedule at %time% (URL will be auto-extracted from cookie)...
dist\AsyafiraAirdropBot.exe --daily-time "%time%"
pause
goto end

:schedule
set /p url="Masukkan URL task: "
set /p datetime="Masukkan tanggal waktu (YYYY-MM-DD HH:MM:SS): "
dist\AsyafiraAirdropBot.exe --task-url "%url%" --run-datetime "%datetime%"
pause
goto end

:test_telegram
dist\AsyafiraAirdropBot.exe --test-telegram
pause
goto end

:validate
dist\AsyafiraAirdropBot.exe --validate-config
pause
goto end

:help
dist\AsyafiraAirdropBot.exe --help
pause
goto end

:invalid
echo Pilihan tidak valid!
pause
goto end

:end
echo.
echo Terima kasih telah menggunakan Asyafira Airdrop Bot!
pause