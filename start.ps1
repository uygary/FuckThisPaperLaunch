if (!(Test-Path env:VIRTUAL_ENV))
{
	.\venv\Scripts\Activate.ps1
}
python.exe .\main.py
