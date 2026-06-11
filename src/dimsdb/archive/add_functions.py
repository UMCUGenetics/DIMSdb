from dimsdb.archive.models import Patient, Sample, DIMSRun, DIMSResults, HMDB
from datetime import date, datetime


def add_patient(patient_id: str, patient_birth_year):
    patient = Patient()
    patient.id = patient_id
    if patient_birth_year is not None:
        patient.birth_year = patient_birth_year
    return patient


def add_sample(sample_id: str, patient: Patient):
    sample = Sample()
    sample.id = sample_id
    sample.patient = patient
    return sample


def add_dims_run(run_name: str,
                 email: str,
                 num_replicates: int,
                 date_run: date, ppm: int, resolution: int, matrix: str, pipeline_version: str):
    dimsrun = DIMSRun()
    dimsrun.name = run_name
    dimsrun.email = email
    dimsrun.date = datetime.strptime(date_run, "%d-%m-%Y").date()
    dimsrun.num_replicates = num_replicates
    dimsrun.ppm = ppm
    dimsrun.resolution = resolution
    dimsrun.matrix = matrix
    dimsrun.pipeline_version = pipeline_version
    return dimsrun


def add_dims_result(
    dimsrun: DIMSRun,
    sample_id: str,
    polarity: bool,
    mz_value: float,
    intensity: float,
    z_score: float,
    ppm_dev: float,
    row_hash: str,
    run_name: str,
    sample: Sample,
):
    dims_result = DIMSResults()
    dims_result.run = dimsrun
    dims_result.polarity = polarity
    dims_result.m_z = mz_value
    dims_result.intensity = intensity
    dims_result.z_score = z_score
    dims_result.ppm_dev = ppm_dev
    dims_result.row_hash = row_hash
    dims_result.sample_id = sample_id
    dims_result.run_name = run_name
    dims_result.sample = sample
    return dims_result


def add_hmdb(hmdb_key: str, hmdb_code: str, sec_hmdb_id: str, name: str, chem_formula: str, mz_value: float):
    hmdb = HMDB()
    hmdb.hmdb_key = hmdb_key
    hmdb.hmdb_id = hmdb_code
    hmdb.sec_hmdb_id = sec_hmdb_id
    hmdb.name = name
    hmdb.chem_formula = chem_formula
    hmdb.theor_mz = mz_value
    return hmdb


def add_dimsresult_hmdb_link(hmdb: HMDB, dims_result: DIMSResults, adduct: int):
    link = DIMSResultsHMDBLink()
    link.hmdb = hmdb
    link.dims_result = dims_result
    link.adduct = adduct
    return link
