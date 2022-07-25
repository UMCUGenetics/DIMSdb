# DIMSdb
database for Direct Infusion Mass Spectrometry pipeline 

# Single patients
Deze scripts worden uiteindelijk vervangen door de DIMS database. De webapplicatie en de bijbehorende database bevat alle data van eerdere runs, waardoor het apart verzamelen van data van 1 of meerdere patienten overbodig wordt. Voor meer informatie, zie documentatie over DIMSdb.

Het Single Patients script wordt gebruikt om informatie van de DIMS pipeline te verzamelen van individuele patiënten. Deze geven meerdere dry bloodspots (DBS) af (of ander patiëntmateriaal) en worden op verschillende momenten opgewerkt, gemeten en geanalyseerd. Daardoor is de betreffende informatie verspreid over verschillende DIMS analyses. Het single patients script voorziet in 3 doelen.
1.	Verzamelen van de correcte waarden (HMDB code/naam/descr, intensiteiten en Zscores) van de betreffende patiënt uit de eind resultaten Excel van de DIMS pipeline (<projectnaam>.xlsx). Dit wordt verzameld in de eerste sheet “All”
2.	Op basis van tabel 1 bepalen welke HMDB codes verhoogd of verlaagd zijn op basis van zowel het aantal gemeten DBS, Zscore en modus (positive/negative). Dit wordt verzameld in de tweede en derde sheet “Elevated” en “Decreased”.
3.	Het genereren van Adduct plots per HMDB en per run, om weer te geven in de Single Patients resultaten sheets (Elevated en Decreased).

TABEL 1
| DBS | Metaboliet verhoogd  | Metaboliet verlaagd |
| --- | ------------- | ------------- |
| 1 DBS | > 2.00  | < -1.50  |
| 2 DBS | > 1.75  | < -1.25  |
| 3 DBS | > 1.00  | < -0.80  |
| 4 DBS | 3 DBS > 1.00  | 3 DBS < -0.80  |
| 5 DBS | 4 DBS > 1.00  | 4 DBS < -0.80  |

De software Single Patients bestaat uit 3 scripts (+supportive scripts uit de DIMS pipeline).
-	CreateBoxPlot.R
Deze maakt de adductplots map op basis van de “bioinformatics” folder van de DIMS pipeline run.
-	CreateIndividualSPMonsters.R
Dit script maakt de verzamelde file met de 3 sheets. Het zoekt de juiste runs op basis van de “SP_DBS” file, waar alle patienten vernoemd staan. Hierin is ook de informatie aanwezig over hoeveel DBS er beschikbaar zijn en in welke DIMS pipeline runs deze geanalyseerd zijn.
-	Run_all_patients.R
Dit script maakt het mogelijk meerdere patiënten tegelijk te analyseren.


# HOW TO
1.	Clone het script lokaal
2.	Ga naar de single_patients folder
3.	Maak de volgende mappen aan “xls”, “Boxplots_SinglePatients”, “Data”, “excels” in de Single_patients folder
4.	Zet in de “Data” folder het bestand HMDB_with_info_relevance_IS_C5OH.RData. Deze is te vinden in de DIMS pipeline.
5.	In de “excels” folder komen de eindresultaten files (.xlsx) van alle runs staan die nodig zijn voor de patiënt(en) die verzameld moeten worden (single patients). Dit is de eindresultaten file van de DIMS pipeline `<runnaam>.xlsx`. 
6.	Tevens moet in de excels folder de file staan waar alle patiëntinformatie staat staan, de zogenoemde SP_DBS excel file.
7.	Open de bestanden in de “Directories_to_read” folder
a.	boxplots_input.txt - Vul hier de plaats in waar de single patients runs verzameld staan.
b.	boxplots_output.txt - Vul hier de locale map in, zoals gebruikt in stap 1 met folder waar de plots gemaakt worden m.b.v. script `CreateBoxPlot.R`. Voorbeeld: `<path_naar_clone>/DIMSdb/single_patients/Boxplots_SinglePatients/`
c.	Het bestand HMDB_info.txt bevat al de juiste informatie (als stap 4 juist uitgevoerd is)
8.	Open `run_all_patients.R`. Hierin moet bovenin de juiste informatie ingevuld worden. Vervang `<path_to_local>`.
9.	Als “make_plots” op 0 staat worden de Excels gemaakt zonder plots in de "Elevated" en "Decreased" sheets. Standaard zijn de plots wel noodzakelijk.
10. Indien "make_plots" op 0, ga verder vanaf stap 15. De volgende stappen beschrijven het creëren van de Adducts plots.
## Creëren Adduct plots
11.	Open het script `CreateBoxPlot.R`. Hierin moet bovenin de juiste informatie ingevuld worden. Vervang `<path_to_local>`.
12.	Ga via de terminal naar de plaats waar het script `CreateBoxPlot.R` is.
13.	Gebruik het commando `Rscript CreateBoxPlot.R XX YY` waar XX YY staat voor de runnummers van de betreffende single patients runs. Een voorbeeld is `Rscript CreateBoxPlot.R 12 34`, waarbij de boxplots gemaakt worden van run SP12 en SP34. Er kan ook 1 run opgegeven worden of meer dan twee (gebruik dan altijd spatie als scheidingsteken). Als de “bioinformatics” map niet gevonden kan worden in het betreffende runnummer, moet zelf een keuze gemaakt worden. Volg de aanwijzingen van het script.
14.	In de folder “Boxplots_SinglePatients” zijn de runnummers als folders toegevoegd met daarin een “plots” folder met daarin een “adducts” folder. Dit is dezelfde output als normaal gesproken in de DIMS pipeline gemaakt wordt. Hierin zit een grote hoeveelheid aan bestanden (>2000).
## Runnen Single patients
15.	Er kan op 2 verschillende manieren gerund worden.
a.	Als twee losse patiënten. Gebruik hiervoor het bovenste deel van het script. Vul voor “patients” de juiste P nummers, zoals op het voorbeeld. Zoals: `patients <- c("Pxxx", "Pxxx")`. Run vervolgens de for loop, om deze twee patiënten te analyseren.
b.	Alsof het 1 patiënt betreft. Gebruik hiervoor het onderste deel van het script. Vul voor “patient_ID” de juiste P nummers, zoals op het voorbeeld. Zoals `patient_ID <- c("Pxxx", "Pxxx")`. Run vervolgens het laatste deel van het script.
16.	Er wordt een Excel bestand gemaakt voor elke patiënt (stap 10a) of voor meerdere patiënten tegelijk (stap10b). Deze worden verzameld in de “xls” folder.
