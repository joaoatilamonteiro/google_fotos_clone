@echo off
chcp 65001 >nul
setlocal

REM Usa os argumentos se vierem; senão pergunta ao usuário
set "PASTA=%~1"
set "DESTINO=%~2"

if "%PASTA%"=="" set /p "PASTA=Informe o caminho completo da pasta com as fotos/videos: "
if "%DESTINO%"=="" set /p "DESTINO=Nome do lote (Enter para 'importacao'): "
if "%DESTINO%"=="" set "DESTINO=importacao"

REM Remove aspas e a barra final do caminho
set "PASTA=%PASTA:"=%"
if "%PASTA:~-1%"=="\" set "PASTA=%PASTA:~0,-1%"

REM Valida antes de apagar qualquer coisa
if not exist "%PASTA%\" goto pasta_invalida

REM ===== ATENÇÃO: passos 1 e 2 reconstruídos, compare com o seu original =====
echo [1/4] Apagando o banco de dados antigo...
if exist db.sqlite3 del /f /q db.sqlite3

echo [2/4] Recriando o banco e as migrações...
py manage.py makemigrations
py manage.py migrate
REM ============================================================================

echo [3/4] Importando mídias (Fotos e Vídeos)...
py manage.py importar_midia "%PASTA%" --destino "%DESTINO%"

echo [4/4] Gerando proxies otimizados para Web e limpando antigos...
py manage.py gerar_proxies

echo =======================================
echo PROCESSO FINALIZADO COM SUCESSO!
echo =======================================
pause
exit /b 0

:pasta_invalida
echo Pasta nao encontrada: %PASTA%
pause
exit /b 1