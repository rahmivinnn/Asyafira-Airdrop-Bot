@echo off
echo.
echo ========================================
echo    Asyafira Airdrop Bot - Launcher
echo ========================================
echo.
echo Pilihan menjalankan bot:
echo 1. Run sekali langsung (Recommended)
echo 2. Interactive mode (pilih opsi di dalam bot)
echo 3. Exit
echo.
set /p choice="Masukkan pilihan (1-3): "

if "%choice%"=="1" (
    echo.
    echo Menjalankan bot sekali langsung...
    echo.
    .\dist\AsyafiraAirdropBot.exe --run-once
    echo.
    echo Bot selesai dijalankan!
    pause
) else if "%choice%"=="2" (
    echo.
    echo Menjalankan interactive mode...
    echo.
    .\dist\AsyafiraAirdropBot.exe
    pause
) else if "%choice%"=="3" (
    echo Keluar...
    exit /b 0
) else (
    echo Pilihan tidak valid!
    pause
    goto :eof
)