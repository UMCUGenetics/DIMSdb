# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Session info ------------------------------------------------------------
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  # Script to create boxplots of the metabolite values accross the 2015-runs.
  # These boxplots can be used to create excel files for individual patients.


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# MAC COMPATIBLE, load in functions to be used ----------------------------
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

setwd("/Users/fdegruyt/extra/single_patients/")
source("Supportive_scripts/getPatients.R")
source("Supportive_scripts/initialize.R")
source("Supportive_scripts/plotBoxPlot.R")
source("Supportive_scripts/statistics_z.R")
source("Supportive_scripts/statistics_z_4export.R")
isRStudio <- Sys.getenv("RSTUDIO") == "1"


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Functions ---------------------------------------------------------------
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
stopQuietly <- function(...) {
  blankMsg <- sprintf("\r%s\r", paste(rep(" ", getOption("width")-1L), collapse=" "));
  stop(simpleError(blankMsg));
} # stopQuietly()


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Get to correct working directories --------------------------------------
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# matrix  <-"DBS"
args <- commandArgs(TRUE)
project_numbers <- args[1:length(args)]
all_projects <- NULL

# Location of the singlepatients projects
working_directory <- as.character(read.table("Directories_to_read/boxplots_input.txt", stringsAsFactors = FALSE))
HMDB_info <- as.character(read.table("Directories_to_read/HMDB_info.txt", stringsAsFactors = FALSE))

adducts <- TRUE
control_label <- "C"
case_label <- "P"

# Location of where the boxplots should be saved
outputfolder <- as.character(read.table("Directories_to_read/boxplots_output.txt", stringsAsFactors = FALSE))


for(num in 1:length(project_numbers)){
  #all_projects[num] <- paste0(project_numbers[num], "SinglePatients_", as.numeric(project_numbers[num]),"b")
  all_projects[num] <- paste0("SinglePatients_", as.numeric(project_numbers[num]))
  while(!dir.exists(paste0(working_directory, all_projects[num]))){
    
    cat("project '", all_projects[num], "' does not exist (yet) in this directory: ", working_directory,"\n")
    cat("Choose a different project number or type 'stop'")
    if(isRStudio){
      user_number <- readline(prompt="Enter file number or stype 'stop': ")
    } else {
      cat("Enter file number or type 'stop': ")
      user_number <- readLines(file("stdin"), n = 1)
    }
    if(user_number == "stop"){
      stopQuietly()
    } else {
      project_numbers[num] <- user_number
      rm(user_number)
    }
    all_projects[num] <- paste0("SinglePatients_", project_numbers[num])
  }
}

cat("\n\nStart script, \nchoosen runs:",all_projects,"\n")


# Get bioinformatics folder in all projects. The early ones contain 2, some contain none in 
# which the content of the bioinformatics folder is present in the project folder itself
for(project in all_projects){
  project_directory <- paste0(working_directory, project)
  bioinf_files <- grep("Bioinformatics", list.files(project_directory), value = TRUE)
  if(length(bioinf_files) == 1){
    initialize_input <- paste(project_directory, bioinf_files, sep = "/")
  } else {
    cat("Number of Bioinformatics files > 1, indicate which directory to use:\n", paste(bioinf_files, collapse = "\n "),"\n")
    if(isRStudio){
      user_input <- readline(prompt="Enter file name: ")
    } else {
      cat("Enter file name: ")
      user_input <- readLines(file("stdin"), n = 1)
    }
    initialize_input <- paste(project_directory, user_input, sep = "/")
    while(!dir.exists(initialize_input)){
      cat("Incorrect directory name supplied, check the spelling and indicate which directory to use:\n", paste(bioinf_files, collapse = "\n "),"\n")
      if(isRStudio){
        user_input <- readline(prompt="Enter file name: ")
      } else {
        cat("Enter file name: ")
        user_input <- readLines(file("stdin"), n = 1)
      }
      initialize_input <- paste(project_directory, user_input, sep = "/")
    }
  }
  cat("Name of directory:", initialize_input, "\n")


  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Initialise function, create data for plots ------------------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  # sum positive and negative adductsums
  cat("starting initialize, outputfolder:", outputfolder, "\n")
  outlist <- initialize(inputfolder = initialize_input, outputfolder = outputfolder, HMDB_info_folder = HMDB_info, project = project)
  outlist <- outlist$adducts
  outlist <- outlist[-grep("Exogenous", outlist[,"relevance"], fixed = TRUE),]
  outlist <- outlist[-grep("exogenous", outlist[,"relevance"], fixed = TRUE),]
  outlist <- outlist[-grep("Drug", outlist[,"relevance"], fixed = TRUE),]


  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Boxplots as they appear in the excel files ------------------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  # This function will create the boxplots via the scripts 'statistics_z_4export' and 'plotBoxPlot'
  cat("start boxplots for",project,"\n")
  outlist <- statistics_z_4export(peaklist = as.data.frame(outlist),
                                  plotdir = paste0(outputfolder, project, "/plots/adducts"),
                                  patients = getPatients(outlist),
                                  adducts = adducts,
                                  control_label = control_label,
                                  case_label = case_label)
}
