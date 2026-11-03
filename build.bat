@echo off
rem Builds "FNV Radio Generator.exe" next to this file (needs Python 3.10+).
cd /d "%~dp0"
if not exist .venv-build python -m venv .venv-build
.venv-build\Scripts\python -m pip install --quiet pyinstaller
.venv-build\Scripts\python -m PyInstaller --noconfirm --onefile --windowed --name "FNV Radio Generator" --distpath . --workpath build --specpath build "FNV Radio Generator.pyw"
