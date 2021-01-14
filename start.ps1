if (!(Test-Path env:VIRTUAL_ENV)) {
	.\venv\Scripts\Activate.ps1
}
try {
	python.exe .\main.py
}
catch {
	Write-Host $_
}
finally {
	deactivate
}
