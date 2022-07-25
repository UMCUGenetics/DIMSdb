# DIMSdb
DSatabase for Direct Infusion Mass Spectrometry pipeline 

# How to start
Programma om de database file die gecreeerd wordt te openen is "DB Browser for SQLite". https://sqlitebrowser.org/
1. Maak een virtual environment en installeer de juiste modules met behulp van de requirements.txt
```
$ python3 -m venv venv
$ source ./venv/bin/activate
$ pip3 install --upgrade pip  # nodig om Cython te kunnen installeren voor pyreadr
$ pip3 install -r requirements.txt
```
2. Ga naar de juiste folder /path/to/DIMSdb/extra
3. Pas in de `logging_config.yml` de filename path aan. Dit is de plaats waar de output.log aangevuld/gecreeerd wordt.
4. Start de virtual environment met `source ../venv/bin/activate` als dit nog niet gedaan is.
5. Bij het starten van het pythonscript zorgt argparse ervoor dat er info verschijnt.
```
$ python import_data.py
```
6. Bij de uitleg wordt aangegeven dat er excelfile(s) als input nodig zijn. Indien er meerdere tegelijk toegevoegd worden, wordt dit gescheiden met een spatie. Voorbeeld:
```
$ python import_data.py -f /path/to/DIMS_resultaat_RUNx.xlsx /path/to/DIMS_resultaat_RUNy.xlsx
```
7. Als de file extension .xlsx betreft, dan verwacht het een "DIMS resultaat eind-Excel" file en start het deze upload proces. Dit duurt best een tijd, aangezien er duizenden entries zijn (HMDBs + patienten + intensiteiten + zscores + (eventueel meerdere files))
(8. Als de input een .RData file betreft, verwacht het een HMDBdatabasefile. Dit proces moet nog verder uitgewerkt worden.)
```
$ python import_data.py -f /path/to/database.RData
```
9. Er wordt een DIMS.db bestand gegenereerd. Deze is te openen met "DB Browser for SQLite" en hiermee kan door de database genavigeerd worden.
10. Er wordt een `output.log` bestand gemaakt, met daarin wat er uitgevoerd is en wanneer. Deze is aan te vullen in de code met de logger python module. Dit is in combinatie met de `logging_config.yml`

# Single Patients script
Zie readme `single_patients` folder

