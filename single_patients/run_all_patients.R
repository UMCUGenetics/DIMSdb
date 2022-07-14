suppressMessages(library(data.table))
suppressMessages(library(openxlsx)) # reading and writing to excel
suppressMessages(library(loder)) # readPng function for dimensions of the images
suppressMessages(library(plyr))
suppressMessages(library(dplyr)) # must load after plyr
suppressMessages(library(stringr)) # for appending leading zeros when selecting runs
suppressMessages(library(tidyverse))

################
## maken van de Single patients plot. Hierbij is het extra script nodig CreateIndividualSPMonsters.R"
################
# input: de eind excelfile [run_naam].xlsx van de DIMS pipeline
# input2: de adduct plaatjes van alle runs. Deze kan gemaakt worden met het script "CreateBoxPlot.R"
# bij het gebruik van controle samples (maar ook bij patientensamples) moet in elke run een opvolgend nummer zijn voor dezelfde patient. P123.1, P123.2 ect.
# bij controlesamples waar dit niet standaard is kan eenvoudig de header van het excel aangepast worden van Cxx.1 naar Cxx.xx (met find and replace)
# output: bestand met alle gevonden HMDB_codes over alle geselecteerde runs, met voor elke run de gevonden intensiteit en gevonden Z-score. Daarbij ook gegevens over de HMDB_code (description ect.)

# script kan hier verbeterd worden door alle "hardcoded" gegevens, zoals file-locatie, filename pattern, hier op te kunnen geven ipv in het script "CreateIndividualSPMonsters_new.R"
rm(list=ls())
setwd("<path_to_local>/DIMSdb/single_patients/")
source("CreateIndividualSPMonsters.R")
path_monsters <- "<path_to_local>/excels/"
path_plots <- "<path_to_local>/Boxplots_SinglePatients"
path_output <- "<path_to_local>/xls/"
xls_file <- paste0(path_monsters,"")
make_plots = 0 # 1 = on, 0 = off


# for each patient a singlePatients excel file will be created using the "CreateIndividualSPMonsters.R" script.
patients <- c("P360", "P361", "P375")
for (patient_ID in patients){
  print(patient_ID)
  run_single_patients(patient_ID, path_monsters, path_plots, path_output, make_plots)
}

# if you want to run more than one patients as one run this script
patient_ID <- c("P360", "P369")
run_single_patients(patient_ID, path_monsters, path_plots, path_output, make_plots)
