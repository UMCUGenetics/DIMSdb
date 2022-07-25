# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Session info ------------------------------------------------------------
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
#
# USE:
#  This file is used to automatically make a single file of one patient
#  when multiple bloodspots have been made from that individual.
#  It can be run from the command line on mac, not on windows
#
# Input:
#  files: end result excel files DIMS pipeline + SP_DBS_xxx file (all info about
#  patients and bloodspots)
#  Patient number(s)
#
# Output
#  1 Excel file with 3 sheets:
#    all HMDB data from SP_DBS for Patient x
#    all enriched / depleted HMDB data from SP_DBS for Patient x,
#    including all overview pictures

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# INPUT -------------------------------------------------------------------
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

suppressMessages(library(data.table))
suppressMessages(library(openxlsx)) # reading and writing to excel
suppressMessages(library(loder)) # readPng function for dimensions of the images
suppressMessages(library(plyr))
suppressMessages(library(dplyr)) # must load after plyr
suppressMessages(library(stringr)) # for appending leading zeros when selecting runs
suppressMessages(library(tidyverse))

run_single_patients = function(patient_ID, path_monsters, path_plots, path_output, make_plots) {
  
  # Thresholds for the "Elevated" and "Decreased" sheet 
  Threshold_pos <- c(2, 1.75, 1, 1, 1)
  Threshold_neg <- c(-1.5, -1.25, -0.8, -0.8, -0.8)
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # FUNCTIONS ---------------------------------------------------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  # create worksheet with all HMDB codes (no pictures included)
  CreateWorkbookSheet_noImg <- function(wb, DT) {
    addWorksheet(wb, "All")
    # directly supplying the number of columns of DT in the form of ncol(DT)-1 raises errors when opening the xlsx file.
    ncols <- ncol(DT) - 1
    setColWidths(wb, "All", cols = c(1:ncols), widths = 16)
    writeData(wb, "All", DT)
    cat("Done with workbook: All HMDB \n")
  }
  
  # Write datatables & pictures to excel
  CreateWorkbookSheet <-
    function(wb,
             DT,
             filelist,
             imagesize_multiplier = 2,
             columns = NULL,
             path_plots) {
      # If the worksheet does not exist, create it with the correct number of columns reserved for all runs
      # Reason: accomodate future calls to CreateWorkbookSheet for the same worksheet --> avoid overloading memory by creating all columns at once.
      
      setattr(DT, "class", c("data.table", "data.frame"))
      rows_DT <- nrow(DT)
      cell_dim <- 1
      
      if (!filelist %in% sheets(wb)) {
        # Add as many columns as there are runs in which the patient occurs
        addCol <- matrix(c(""), nrow = rows_DT, ncol = length(runs))
        colnames(addCol) <- paste("Intensity", runs)
        
        addWorksheet(wb, sheetName = filelist)
        
        printit = cbind(addCol, DT)
      } else {
        addCol <- matrix(c(""), nrow = rows_DT, ncol = 1)
        colnames(addCol) <- paste("Intensity", runs[columns])
        printit = addCol
      }
      
      # Add images
      # !!! reasoning for going from the end to the front (length(run) --> 1)
      # The pictures are now added more conveniently for viewing the results. When manually enlarging the pictures, pictures will only
      # overlay others that were put in the excel sheet before that picture, and will be hidden from view by pictures added after.
      if (is.null(columns))
        columns <- rev(length(runs):1)
      if (make_plots == 1) {
        for (irun in columns) {
          sample_png <- NULL
          writeLines(paste("Start", runs[irun], filelist))
          plotdir <-
            paste0(path_plots, "/", runs[irun], "/plots/adducts")
          for (irow in rows_DT:1) {
            H_code <- DT[irow, HMDB_code]
            if (!length(H_code) == 0 && is.na(H_code) == FALSE) {
              file_png <- paste(plotdir, "/", H_code, "_box.png", sep = "")
              if (is.null(sample_png)) {
                sample_png <- readPng(file_png)
                img_dim <- dim(sample_png)[c(1, 2)]
                cell_dim <- img_dim * imagesize_multiplier
                setColWidths(wb,
                             filelist,
                             cols = irun,
                             widths = cell_dim[2] / 20)
              }
              tryCatch({
                insertImage(
                  wb,
                  filelist,
                  file_png,
                  startRow = irow + 1,
                  startCol = irun,
                  height = cell_dim[1],
                  width = cell_dim[2],
                  units = "px"
                )
              }, error = function(e) {
                writeLines(paste("image not available for", H_code, "in run", runs[irun]))
              })
              if (irow %% 100 == 0) {
                writeLines(paste("at row:", irow))
              }
            }
          }
          writeLines(paste("Done", runs[irun]))
        }
        setRowHeights(wb,
                      filelist,
                      rows = c(1:nrow(DT) + 1),
                      heights = cell_dim[1] / 4)
      }
      
      if (ncol(printit) == 1) {
        writeData(wb, printit, startCol = columns, sheet = filelist)
      } else {
        which_cols_start <- ncol(addCol) + 1
        which_cols_end <- ncol(printit) - 1
        setColWidths(wb,
                     filelist,
                     cols = which_cols_start:which_cols_end,
                     widths = 16)
        writeData(wb, printit, sheet = filelist)
      }
    }
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Data loading ------------------------------------------------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  # Get column names for PatientID and Number of DBS
  DBS_projectinfo_DT <-
    as.data.table(read.xlsx(xls_file, sheet = "Overzicht patienten"))
  Patient_col_name <-
    grep("Patient", names(DBS_projectinfo_DT), value = TRUE)
  names(DBS_projectinfo_DT)[names(DBS_projectinfo_DT) == Patient_col_name] <-
    "Patient.code"
  DBS_projectinfo_DT[, Patient.code := gsub(" ", "", Patient.code)]
  NumDBS_col_name <-
    grep("DBS", names(DBS_projectinfo_DT), value = TRUE)
  NumDBS_col_name <-
    NumDBS_col_name[nchar(grep("DBS", names(DBS_projectinfo_DT), value = TRUE)) < 6]
  names(DBS_projectinfo_DT)[names(DBS_projectinfo_DT) == NumDBS_col_name] <-
    "nr.DBS"
  DBS_patient_DT <- DBS_projectinfo_DT
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Check who is eligible to analyse ----------------------------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  #get patient and #DBS info
  select_cols <- c("Patient.code", "nr.DBS")
  DBS_DT_overzichtpatient <- DBS_patient_DT[, ..select_cols]
  DBS_DT_overzichtpatient <-
    na.omit(DBS_DT_overzichtpatient) # remove rows with NA (has no full run data)
  
  #get run info
  DBS_projectinfo_DT <-
    as.data.table(read.xlsx(xls_file, sheet = "Overzicht runs"))
  select_cols <-
    c("Patient.code", "Sample.code", "Single.Patients.Run")
  DBS_DT_overzichtruns <- DBS_projectinfo_DT[, ..select_cols]
  DBS_DT_overzichtruns <-
    na.omit(DBS_DT_overzichtruns) # remove rows with NA (has no full run data)
  DBS_DT_overzichtruns <-
    DBS_DT_overzichtruns[!grepl('/|DBS missing', DBS_DT_overzichtruns$Sample.code), ] # remove rows with weird sample codes (with / and "DBS missing") (are not directly correlated to the runs)
  
  #combine two dataframes to get full overview of patients and runs
  DBS_DT_full <-
    join(DBS_DT_overzichtpatient, DBS_DT_overzichtruns, type = "full")
  DBS_DT_full <-
    na.omit(DBS_DT_full) # remove rows with NA (has no full run data)
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Select runs for specific patient ----------------------------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  runs = list()
  patient_number_of_DBS = 0
  # Select the project-runs in which the DBS of the selected patient are and save the number of DBS
  for (patient in patient_ID) {
    patient_number_of_DBS <-
      as.integer(patient_number_of_DBS) + as.integer(DBS_DT_overzichtpatient[which(DBS_DT_overzichtpatient[, Patient.code] == patient), nr.DBS])
    # which runs is this patient in?
    runs <-
      c(runs, unique(
        subset(DBS_DT_full, Patient.code == patient, select = "Single.Patients.Run")
      ))
    runs <- unique(as.list(runs))
  }
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Select file(s) where analysis results for 'Patient' are -----------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  filenames <-
    list.files(path = path_monsters,
               pattern = '^RES_DBS.*.xlsx',
               full.names = FALSE)
  
  # to make SP2 not match run_SP25, we add "_" before each run and "_" or ".xlsx" after each run. add them together after
  runs <- unlist(runs)
  runs_xlsx <- paste0("_", runs, "_")
  runs_extra <- paste0("_", runs, ".xlsx")
  toMatch <- c(runs_xlsx, runs_extra)
  full_filenames <-
    unique(grep(paste(toMatch, collapse = "|"), filenames, value = TRUE))
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Open files associated with Patient and collate them into one ------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  DT_list <- list()
  print(full_filenames)
  
  for (i in 1:length(full_filenames)) {
    DT <-
      as.data.table(read.xlsx(paste0(path_monsters, full_filenames[[i]])))
    colnames_in_file <-
      vapply(strsplit(names(DT), ".", fixed = TRUE), `[`, 1, FUN.VALUE = character(1))
    if (length(DT_list) == 0) {
      patient_DT_subset <-
        DT[, grepl(paste0(patient_ID, "$", collapse = "|"),
                   colnames_in_file,
                   perl = TRUE) |
             names(DT) %in% c("HMDB_code", "name", "descr"), with = FALSE]
      DT_list[[i]] <- patient_DT_subset
    } else {
      patient_DT_subset <-
        DT[, grepl(paste0(patient_ID, "$", collapse = "|"),
                   colnames_in_file,
                   perl = TRUE) | names(DT) %in% c("HMDB_code"), with = FALSE]
      DT_list[[i]] <- patient_DT_subset
    }
  }
  
  # Create a single dataframe with all columns of the patient
  patient_DT <-
    data.table(join_all(DT_list, by = "HMDB_code", type = "full"))
  
  setcolorder(patient_DT, c(
    grep(
      "Zscore",
      names(patient_DT),
      invert = TRUE,
      value = TRUE
    ),
    grep("Zscore", names(patient_DT), value = TRUE)
  ))
  refcols <- c("name", "descr")
  named_cols <- c(refcols, "HMDB_code")
  setcolorder(patient_DT, c("HMDB_code", setdiff(names(patient_DT), named_cols), refcols))
  
  # Show which HMDB codes are not present in all files
  absent <-
    as.character(patient_DT[rowSums(is.na(patient_DT[, grep(paste(patient_ID, 
                                                            collapse = "|"), 
                                                            names(patient_DT)), 
                                                            with = FALSE])) > 0, 
                                                            "HMDB_code"])
  if (length(absent) == 0 | absent == "character(0)") {
    writeLines("No HMDB codes (partly) unique")
  } else {
    writeLines(paste(
      c("HMDB codes (partly) unique to some files: \n", absent, "\n"),
      collapse = " "
    ))
    write.table(
      absent,
      file = paste0(
        path_output,
        "/",
        paste(patient_ID, collapse = "_"),
        "_unique_HMDB_codes.txt"
      ),
      row.names = FALSE,
      col.names = FALSE,
      quote = FALSE
    )
  }
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Set the enrichment/depletion parameters ---------------------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  DT_criteria <-
    data.frame(
      "DBS" = c(1, 2, 3, 4, 5),
      "Elevated Threshold" = Threshold_pos,
      "Decreased Threshold" = Threshold_neg
    )
  if (patient_number_of_DBS > 5) {
    number_of_DBS <- 5
  } else {
    number_of_DBS <- patient_number_of_DBS
  }
  thresh_elevated <- DT_criteria$Elevated.Threshold[number_of_DBS]
  thresh_decreased <- DT_criteria$Decreased.Threshold[number_of_DBS]
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Determine decreased/elevated (by Z score) -------------------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  Z_score_cols <- grep("Zscore", colnames(patient_DT), value = TRUE)
  Z_scores_DT <-
    patient_DT[, .SD,  .SDcols = c("HMDB_code", Z_score_cols)]
  Z_scores_DT[, elevated_DBS := rowSums(.SD > thresh_elevated), .SDcols = Z_score_cols]
  Z_scores_DT[, decreased_DBS := rowSums(.SD < thresh_decreased), .SDcols = Z_score_cols]
  
  #if 3 or lower #DBS, all Z-scores need to be higher than the criteria
  if (number_of_DBS < 4) {
    HMDB_elevated <-
      Z_scores_DT[elevated_DBS == number_of_DBS, HMDB_code]
    HMDB_decreased <-
      Z_scores_DT[decreased_DBS == number_of_DBS, HMDB_code]
    #if 4 #DBS, 3 Z-scores or more need to be higher than the criteria to accept
  } else if (number_of_DBS == 4) {
    HMDB_elevated <- Z_scores_DT[elevated_DBS >= 3, HMDB_code]
    HMDB_decreased <- Z_scores_DT[decreased_DBS >= 3, HMDB_code]
    #if >=5 #DBS, 4 Z-scores or more need to be higher than the criteria to accept
  } else {
    HMDB_elevated <- Z_scores_DT[elevated_DBS >= 4, HMDB_code]
    HMDB_decreased <- Z_scores_DT[decreased_DBS >= 4, HMDB_code]
  }
  patient_DT_elevated <- patient_DT[HMDB_code %in% HMDB_elevated, ]
  
  column_name <- names(patient_DT_elevated)[2]
  patient_DT_elevated <- patient_DT_elevated %>%
    group_by_at(vars(all_of(column_name))) %>%
    mutate(
      all_HMDBs = paste(HMDB_code, collapse = " | "),
      all_descrs = paste(descr, collapse = " | "),
      all_names = paste(name, collapse = " | ")
    ) %>%
    distinct(all_HMDBs, .keep_all = TRUE) %>%
    ungroup()
  patient_DT_elevated$name <- NULL
  patient_DT_elevated$descr <- NULL
  
  patient_DT_decreased <- patient_DT[HMDB_code %in% HMDB_decreased, ]
  column_name <- names(patient_DT_decreased)[2]
  patient_DT_decreased <- patient_DT_decreased %>%
    group_by_at(vars(all_of(column_name))) %>%
    mutate(
      all_HMDBs = paste(HMDB_code, collapse = " | "),
      all_descrs = paste(descr, collapse = " | "),
      all_names = paste(name, collapse = " | ")
    ) %>%
    distinct(all_HMDBs, .keep_all = TRUE) %>%
    ungroup()
  patient_DT_decreased$name <- NULL
  patient_DT_decreased$descr <- NULL
  
  
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  # Function to create excel worksheets incl. pictures ----------------------
  # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  wb <- createWorkbook("SinglePatient")
  modifyBaseFont(wb,
                 fontSize = 10,
                 fontColour = "#000000",
                 fontName = "Arial Narrow")
  
  CreateWorkbookSheet_noImg(wb, patient_DT)
  CreateWorkbookSheet(wb = wb, DT = patient_DT_elevated, filelist = "Elevated", imagesize_multiplier = 2, path_plots = path_plots)
  CreateWorkbookSheet(wb = wb, DT = patient_DT_decreased, filelist = "Decreased", imagesize_multiplier = 2, path_plots = path_plots)
  if (make_plots == 1) {
    saveWorkbook(wb, paste0(path_output, paste(patient_ID, collapse = "_"), "_All_And_Aberrant_HMDB_plots", Sys.Date(), ".xlsx"), overwrite = TRUE)
  } else {
    saveWorkbook(wb, paste0(path_output, paste(patient_ID, collapse = "_"), "_All_And_Aberrant_HMDB_", Sys.Date(), ".xlsx"), overwrite = TRUE)
  }
  rm(wb)
  
  cat("Done with patient", patient_ID, "\n\n")
}
