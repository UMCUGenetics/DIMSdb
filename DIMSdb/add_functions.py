from models import *
from datetime import date


def set_patient(patient_id: str, patient_birth_year: int):
    patient = Patient()
    patient.intermediate_id = patient_id
    patient.birth_year = patient_birth_year
    return patient


def set_sample(sample_id: str, patient: Patient, sample_type: str):
    sample = Sample()
    sample.id = sample_id
    sample.patient = patient
    sample.type = sample_type
    return sample


def set_dims_run(run_name: str, email: str, num_replicates: int, date_run: str):
    dimsrun = DIMSRun()
    dimsrun.name = run_name
    dimsrun.email = email
    dimsrun.date = date_run
    dimsrun.num_replicates = num_replicates
    return dimsrun


def set_dims_result(dimsrun: DIMSRun(), sample: Sample(), polarity: bool, mz_value: float,
                    intensity: float, z_score: float):
    dims_result = DIMSResults()
    dims_result.run = dimsrun
    dims_result.polarity = polarity
    dims_result.m_z = mz_value
    dims_result.sample_id = sample
    dims_result.intensity = intensity
    dims_result.z_score = z_score
    return dims_result


def set_hmdb(name: str, hmdb_code: str, mz_value: float):
    hmdb = HMDB()
    hmdb.hmdb_id = hmdb_code
    hmdb.name = name
    hmdb.theor_MZ = mz_value
    return hmdb
