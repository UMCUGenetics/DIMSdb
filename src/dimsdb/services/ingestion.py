"""Service module for ingesting DIMS run data into the database.

This module orchestrates the complete ingestion pipeline, including parsing run
metadata, ensuring entities (samples, patients, measured m/z values, HMDB records,
and DIMS results) exist in the database, and establishing relationships between them.
"""
import os
import uuid
from pathlib import Path

from pandas import DataFrame, Index
from sqlmodel import Session

from dimsdb.models.patient import Patient
from dimsdb.models.measuredmz import MeasuredMZ
from dimsdb.models.dimsresults import DIMSResults
from dimsdb.models.sample import Sample
from dimsdb.models.dimsrun import DIMSRun
from dimsdb.models.hmdb import HMDB
from dimsdb.models.linktables import DIMSRunMeasuredMZ, HMDBMeasuredMZ, DIMSResultsMeasuredMZ, DIMSResultsSample
from dimsdb.services.dimsrun import DIMSRunService
from dimsdb.services.hmdb import HMDBService
from dimsdb.services.sample import SampleService
from dimsdb.services.patient import PatientService
from dimsdb.services.measuredmz import MeasuredMZService
from dimsdb.services.dimsresults import DIMSResultsService
from dimsdb.services.linktables import LinktablesService
from dimsdb.utils.exceptions import NotFoundError

from dimsdb.import_data.retrieve_functions import get_samples_run
from dimsdb.import_data.parse_files import parse_version_log_file, parse_run_parameters_file, parse_rdata_file

class IngestionService:
    """Service for orchestrating the ingestion of DIMS run data.
    
    This service manages the complete workflow for importing DIMS run results
    into the database, including metadata parsing, entity creation, and
    relationship establishment between runs, samples, patients, measured m/z values,
    HMDB records, and measurement results.
    """
    def __init__(self, session: Session):
        """Initialize the IngestionService."""
        self.session = session

    def ingest_run(self, session, dir_path: Path, chunk_size: int):
        """Ingest a complete DIMS run from a directory.
        
        Processes a DIMS run directory by parsing metadata, creating or linking
        entities (samples, patients, measured m/z values), and establishing
        relationships between all components. Data is processed in chunks to manage
        memory usage on large datasets.
        
        Args:
            session: The database session for executing operations.
            dir_path: Path to the DIMS run directory containing result files.
            chunk_size: Number of peak groups to process per batch operation.
        """
        run_name = os.path.basename(dir_path)
        
        repo_version, run_params = self._load_run_metadata(dir_path)

        run = self._ensure_run_exists(session, DIMSRunService, run_name, run_params, repo_version)

        for polarity in ["positive", "negative"]:
            peakgroup_df = parse_rdata_file(str(dir_path / f"outlist_identified_{polarity}.RData"))

            list_samples = self._ensure_samples_patients_dimsrun(
                SampleService, PatientService, peakgroup_df.columns, run)

            for row_index in range(0, len(peakgroup_df), chunk_size):
                peakgroup_df_chunk = peakgroup_df[row_index:row_index + chunk_size]

                peakgroup_df_chunk, measuredmz_dimsrun_link = self._ensure_measuredmz(MeasuredMZService, peakgroup_df_chunk, polarity)

                measuredmz_hmdb_ids_link = self._ensure_hmdb(HMDBService, peakgroup_df_chunk)

                measuredmz_sample_dimsresults_link = self._ensure_dimsresults(
                    DIMSResultsService, peakgroup_df_chunk, list_samples
                )

                self._ensure_link_tables(
                    measuredmz_dimsrun_link, measuredmz_hmdb_ids_link,
                    measuredmz_sample_dimsresults_link, LinktablesService)


    def _load_run_metadata(self, dir_path: Path) -> tuple[str, DataFrame]:
        """Load repository version and run parameters from metadata files.
        
        Args:
            dir_path: Path to the directory containing metadata files.
        
        Returns:
            A tuple of (repository_version, run_parameters_dataframe).
        """
        repo_version = parse_version_log_file(dir_path / "repository_version.log", "DIMS")
        run_params = parse_run_parameters_file(dir_path / "workflow_params.txt")

        if repo_version is None:
            repo_version = "test"

        return repo_version, run_params

    def _ensure_run_exists(
            self, session, dimsrun_service: DIMSRunService, run_name: str, run_params: DataFrame, repo_version: str) -> DIMSRun:
        """Retrieve an existing DIMSRun or create one if it does not exist.
        
        Args:
            session: The database session for executing operations.
            run_name: The unique identifier for the run.
            run_params: DataFrame containing run parameters extracted from workflow metadata.
            repo_version: The repository version used for this run.
        
        Returns:
            The existing or newly created DIMSRun record.
        """
        try:
            run = dimsrun_service.get_dimsrun_by_runname(session, run_name)
        except NotFoundError:
            run = None
        
        if run:
            return run

        run = DIMSRun(
            run_id=run_name,
            name=run_name,
            email=run_params.at["email", "value"],
            nr_replicates=run_params.at["nr_replicates", "value"],
            date=run_params.at["date", "value"],
            ppm=run_params.at["ppm", "value"],
            resolution=run_params.at["resolution", "value"],
            matrix=run_params.at["matrix", "value"],
            repo_version=repo_version,
        )

        return dimsrun_service.create_dimsrun(session, run)

    def _ensure_samples_patients_dimsrun(
            self,
            sample_service: SampleService,
            patient_service: PatientService,
            df_columns: Index[str],
            dimsrun: DIMSRun) -> list[Sample]:
        """Ensure samples, patients, and their relationships to the run exist.
        
        Creates or retrieves samples and patients from the dataframe columns,
        establishes patient-sample relationships, and links samples to the run.
        
        Args:
            sample_service: Service instance for sample operations.
            patient_service: Service instance for patient operations.
            df_columns: Column names from the results dataframe representing samples.
            dimsrun: The DIMSRun to link samples to.
        
        Returns:
            A list of Sample records linked to the run.
        """
        sample_ids = get_samples_run(df_columns)
        list_samples = []

        for sample_id in sample_ids:
            patient_id = sample_id.split(".")[0]
            patient = Patient(patient_id=patient_id)
            patient = patient_service.get_or_create_patient(patient)

            sample = Sample(sample_id=sample_id)
            sample = sample_service.get_or_create_sample(sample)
            sample = sample_service.link_patient_to_sample(sample, patient)

            sample = sample_service.link_dimsrun_to_sample(sample, dimsrun)

            list_samples.append(sample)

        return list_samples

    def _ensure_measuredmz(
            self,
            measuredmz_service: MeasuredMZService,
            peakgroup_df_chunk: DataFrame,
            polarity: str,
            dimsrun: DIMSRun) -> tuple[DataFrame, list[dict]]:
        """Create MeasuredMZ records and link them to the run.
        
        Creates temporary keys for tracking m/z values, inserts them into the database,
        and builds link records connecting them to the DIMS run. Updates the dataframe
        with the assigned database IDs.
        
        Args:
            measuredmz_service: Service instance for MeasuredMZ operations.
            peakgroup_df_chunk: Dataframe chunk containing peak group data.
            polarity: Ion polarity mode ("positive" or "negative").
            dimsrun: The DIMSRun to link measured m/z values to.
        
        Returns:
            A tuple of (updated_dataframe, link_list) where link_list contains
            dictionaries mapping DIMSRun IDs to MeasuredMZ IDs.
        """

        temp_keys = [str(uuid.uuid4()) for _ in range(len(peakgroup_df_chunk))]
        peakgroup_df_chunk["_mz_temp_key"] = temp_keys

        list_measured_mzs = [
            MeasuredMZ(
                temp_key=row["_mz_temp_key"],
                mz=row["mz"],
                ppm_dev=row["ppmdev"],
                is_positive=True if polarity == "positive" else False,
            )
            for row in peakgroup_df_chunk.to_dict("records")
        ]

        measuredmz_service.create_measured_mzs_in_bulk(list_measured_mzs)
        id_map = measuredmz_service.create_id_map_measuredmzs(list_measured_mzs)

        peakgroup_df_chunk["measuredmz_id"] = peakgroup_df_chunk["_mz_temp_key"].map(id_map)

        peakgroup_df_chunk.drop(columns=["_mz_temp_key"], inplace=True)

        link_list = [
            {
                "dimsrun_id": dimsrun.id,
                "measuredmz_id": mz_id
            }
            for mz_id in peakgroup_df_chunk["measuredmz_id"]
        ]

        return peakgroup_df_chunk, link_list

    def _ensure_hmdb(self, hmdb_service: HMDBService, peakgroup_df_chunk: DataFrame) -> list[dict]:
        """Ensure HMDB records exist and create links from measured m/z to HMDB.
        
        Parses HMDB identifiers from the dataframe, creates missing HMDB records,
        and builds link entries with adduct information.
        
        Args:
            hmdb_service: Service instance for HMDB operations.
            peakgroup_df_chunk: Dataframe chunk containing peak group data with HMDB identifiers.
        
        Returns:
            A list of dictionaries containing links between measured m/z values and HMDB records.
        """
        peakgroup_df_chunk = peakgroup_df_chunk.dropna(subset=["HMDB_code"])

        peakgroup_df_chunk["hmdb_ids_list"] = (
            peakgroup_df_chunk["all_hmdb_ids"]
            .fillna("")
            .apply(
                lambda x: [
                    (
                        parts[0],
                        int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    )
                    for parts in (i.split("_") for i in x.split(";") if i)
                ]
            )
        )
        
        unique_hmdb_ids = list({
            hmdb_id
            for id_adduct_pairs in peakgroup_df_chunk["hmdb_ids_list"]
            for (hmdb_id, _) in id_adduct_pairs
        })

        existing_hmdbs = hmdb_service.get_hmdbs_by_list_hmdb_ids(unique_hmdb_ids)
        existing_ids = {hmdb.hmdb_id for hmdb in existing_hmdbs}

        missing_ids = list(set(unique_hmdb_ids) - existing_ids)

        hmdb_info_lookup = {}
        for row in peakgroup_df_chunk.itertuples(index=False):
            for hmdb_id in row.hmdb_ids_list:
                if hmdb_id not in hmdb_info_lookup:
                    hmdb_info_lookup[hmdb_id] = row

        if missing_ids:
            new_hmdbs = []
            for hmdb_id in missing_ids:
                row = hmdb_info_lookup[hmdb_id]

                new_hmdbs.append(
                    HMDB(
                        hmdb_key=hmdb_id,
                        hmdb_id=hmdb_id,
                        sec_hmdb_id="",
                        name="",
                        theor_mz=row.get("theormz_HMDB")
                    )
                )
            hmdb_service.create_hmdb_in_bulk(new_hmdbs)

        hmdbs_db = hmdb_service.get_hmdbs_by_list_hmdb_ids(unique_hmdb_ids)

        hmdb_map = {h.hmdb_id: h for h in hmdbs_db}

        link_list = []

        for row in peakgroup_df_chunk.itertuples(index=False):
            measuredmz_id = row.measuredmz_id

            for hmdb_id, adduct in row.hmdb_ids_list:
                db_id = hmdb_map.get(hmdb_id)
                if db_id:
                    link_list.append({
                        "measuredmz_id": measuredmz_id,
                        "hmdb_id": db_id,
                        "adduct": adduct
                    })

        return link_list


    def _ensure_dimsresults(
            self,
            dimsresult_service: DIMSResultsService,
            peakgroup_df_chunk: DataFrame,
            list_samples: list[Sample]) -> list[dict]:
        """Create DIMS result records for intensities and link to samples and measured m/z.
        
        Extracts intensity measurements and z-scores from the dataframe, creates
        DIMSResults records with temporary keys, and builds links to samples and
        measured m/z values.
        
        Args:
            dimsresult_service: Service instance for DIMSResults operations.
            peakgroup_df_chunk: Dataframe chunk containing measured intensities.
            list_samples: List of Sample records with established IDs.
        
        Returns:
            A list of dictionaries containing links between DIMSResults, measured m/z,
            and samples.
        """

        sample_name_to_id = {
            sample.sample_id: sample.id for sample in list_samples
        }

        intensity_columns = [
            col for col in peakgroup_df_chunk.columns
            if col in sample_name_to_id
        ]

        records = peakgroup_df_chunk.to_dict("records")

        list_dimsresults = []
        meta_list = []

        for row in records:
            measuredmz_id = row["measuredmz_id"]

            for col in intensity_columns:
                temp_key = str(uuid.uuid4())
                list_dimsresults.append(
                    DIMSResults(
                        temp_key=temp_key,
                        intensity=row[col],
                        z_score=row.get(f"{col}_Zscore")
                    )
                )

                meta_list.append({
                    "temp_key": temp_key,
                    "measuredmz_id": measuredmz_id,
                    "sample_id": sample_name_to_id[col]
                })

        id_map = dimsresult_service.create_bulk_dimsresults(list_dimsresults)

        link_list = []

        for meta in meta_list:
            link_list.append({
                "dimsresults_id": id_map[meta["temp_key"]],
                "measuredmz_id": meta["measuredmz_id"],
                "sample_id": meta["sample_id"]
            })

        return link_list


    def _ensure_link_tables(
            self,
            measuredmz_dimsrun_link: list[dict],
            measuredmz_hmdb_ids_link: list[dict],
            measuredmz_sample_dimsresults_link: list[dict],
            linktable_service: LinktablesService) -> None:
        """Create links in junction tables to establish entity relationships.
        
        Populates the junction tables that connect DIMSRun to MeasuredMZ, HMDB to
        MeasuredMZ, and DIMSResults to both MeasuredMZ and Samples. Deduplicates
        DIMSResults links to avoid redundant relationships.
        
        Args:
            measuredmz_dimsrun_link: List of links between DIMSRun and MeasuredMZ.
            measuredmz_hmdb_ids_link: List of links between HMDB and MeasuredMZ.
            measuredmz_sample_dimsresults_link: List of links between DIMSResults, MeasuredMZ, and Samples.
            linktable_service: Service instance for managing link table operations.
        """

        linktable_service.create_links_in_bulk(DIMSRunMeasuredMZ, measuredmz_dimsrun_link)

        linktable_service.create_links_in_bulk(HMDBMeasuredMZ, measuredmz_hmdb_ids_link)

        seen_mz = set()
        seen_sample = set()

        dimsresults_measuredmz_links = []
        dimsresults_sample_links = []

        for link in measuredmz_sample_dimsresults_link:
            dimsresults_id = link["dimsresults_id"]

            key_mz = (dimsresults_id, link["measuredmz_id"])
            if key_mz not in seen_mz:
                seen_mz.add(key_mz)
                dimsresults_measuredmz_links.append({
                    "dimsresults_id": dimsresults_id,
                    "measuredmz_id": link["measuredmz_id"]
                })

            key_sample = (dimsresults_id, link["sample_id"])
            if key_sample not in seen_sample:
                seen_sample.add(key_sample)
                dimsresults_sample_links.append({
                    "dimsresults_id": dimsresults_id,
                    "sample_id": link["sample_id"]
                })

        linktable_service.create_links_in_bulk(DIMSResultsSample, dimsresults_sample_links)
        linktable_service.create_links_in_bulk(DIMSResultsMeasuredMZ, dimsresults_measuredmz_links)
