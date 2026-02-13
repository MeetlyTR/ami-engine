@echo off
REM AMI-ENGINE testleri - Python PATH'te olmasa da çalışır
set PYEXE=C:\Users\tsgal\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PYEXE%" (
  echo Python bulunamadi. Lutfen Python 3.10+ yukleyin veya PYEXE yolunu duzenleyin.
  pause
  exit /b 1
)
cd /d "%~dp0"
"%PYEXE%" run_all_tests.py
pause
