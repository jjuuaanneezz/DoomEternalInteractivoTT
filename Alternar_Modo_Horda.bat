@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Selector de Modo Horda - DOOM Eternal

cd /d "D:\SteamLibrary\steamapps\common\DOOMEternal"

set "MODS_DIR=D:\SteamLibrary\steamapps\common\DOOMEternal\Mods"
set "DISABLED_DIR=D:\SteamLibrary\steamapps\common\DOOMEternal\Mods_Disabled"

if not exist "%DISABLED_DIR%" mkdir "%DISABLED_DIR%"

cls
echo ========================================================
echo        SELECTOR DE MODO HORDA - DOOM ETERNAL
echo ========================================================
echo.

set "MOD_ACTIVO=0"
for %%F in ("%MODS_DIR%\*.zip") do (
    set "MOD_ACTIVO=1"
    set "MOD_NOMBRE=%%~nxF"
)

if "!MOD_ACTIVO!"=="1" (
    echo [ESTADO ACTUAL]: MOD ACTIVO
    echo Mod detectado: !MOD_NOMBRE!
    echo.
    echo Deseas DESACTIVAR el mod y restaurar el MODO HORDA ORIGINAL?
    echo Escribe S y pulsa Enter para desactivar.
    echo Escribe N o pulsa Enter para salir.
    echo.
    set /p "OPCION=Tu eleccion: "
    if /i "!OPCION!"=="S" (
        echo.
        echo [1/2] Moviendo mod a Mods_Disabled...
        move /y "%MODS_DIR%\*.zip" "%DISABLED_DIR%\" >nul
        echo [2/2] Ejecutando EternalModInjector para restaurar archivos oficiales...
        call ".\EternalModInjector.bat"
        echo.
        echo ========================================================
        echo  COMPLETADO: Modo Horda Original restaurado al 100%%.
        echo ========================================================
    ) else (
        echo Operacion cancelada.
    )
) else (
    echo [ESTADO ACTUAL]: MODO ORIGINAL - VANILLA
    echo.
    echo Deseas ACTIVAR Infinite Arena Mode de Nexus Mods?
    echo Escribe S y pulsa Enter para activar.
    echo Escribe N o pulsa Enter para salir.
    echo.
    set /p "OPCION=Tu eleccion: "
    if /i "!OPCION!"=="S" (
        echo.
        echo [1/2] Moviendo mod a la carpeta activa Mods...
        move /y "%DISABLED_DIR%\*.zip" "%MODS_DIR%\" >nul
        echo [2/2] Ejecutando EternalModInjector para aplicar el mod...
        call ".\EternalModInjector.bat"
        echo.
        echo ========================================================
        echo  COMPLETADO: Infinite Arena Mode ha sido ACTIVADO.
        echo ========================================================
    ) else (
        echo Operacion cancelada.
    )
)

echo.
echo Presiona cualquier tecla para salir...
pause >nul
