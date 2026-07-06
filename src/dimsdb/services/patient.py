"""Service module for managing Patient records.

This module provides business logic for performing CRUD operations on Patient
entities, including querying, creating, updating, and deleting records, as well
as establishing relationships with samples.
"""
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import Session

import dimsdb.crud.patient as patient_crud
from dimsdb.models.patient import Patient
from dimsdb.models.sample import Sample
from dimsdb.services.sample import SampleService
from dimsdb.utils.exceptions import NotFoundError, ExistsError

class PatientService:
    """Service for managing Patient entities and their relationships.
    
    This service acts as an intermediary between API endpoints and database
    operations, providing higher-level methods for querying, creating, updating,
    and deleting patient records and establishing relationships with samples.
    """
    
    def __init__(self, session: Session):
        """Initialize the PatientService.
        
        Args:
            session: SQLModel database session for executing queries.
        """
        self.session = session

    def get_patient_by_id(self, patient_id: str) -> Patient:
        """Retrieve a patient by their ID.
        
        Args:
            patient_id: The unique identifier of the patient.
        
        Returns:
            The Patient record with the given ID.
        
        Raises:
            NoResultFound: If no patient with the given ID exists.
        """
        try:
            return patient_crud.select_patient_by_id(self.session, patient_id)
        except NoResultFound:
            raise NotFoundError("Patient not found")

    def create_patient(self, patient: Patient) -> Patient:
        """Create a new patient record.
        
        The patient is validated using Pydantic before insertion. Raises an
        error if a patient with the same identifier already exists.
        
        Args:
            patient: The Patient record to create.
        
        Returns:
            The newly created Patient record.
        
        Raises:
            ExistsError: If a patient with the same ID already exists.
        """
        validated_patient = Patient.model_validate(patient)
        try:
            return patient_crud.insert_patient(self.session, validated_patient)
        except IntegrityError:
            raise ExistsError("Patient already exists")

    def update_patient(self, patient_id: str, patient: Patient) -> Patient:
        """Update an existing patient record.
        
        Retrieves the patient by ID and updates their fields with non-null
        values from the provided data.
        
        Args:
            patient_id: The ID of the patient to update.
            patient: The Patient record with updated field values.
        
        Returns:
            The updated Patient record.
        
        Raises:
            NoResultFound: If no patient with the given ID exists.
        """
        db_patient = self.get_patient_by_id(patient_id)
        patient_data = patient.model_dump(exclude_none=True)
        return patient_crud.update_patient(self.session, db_patient, patient_data)

    def delete_patient(self, patient_id: str) -> None:
        """Delete a patient record.
        
        Args:
            patient_id: The ID of the patient to delete.
        
        Raises:
            NoResultFound: If no patient with the given ID exists.
        """
        db_patient = self.get_patient_by_id(patient_id)
        patient_crud.delete_patient(self.session, db_patient)

    def link_or_create_patient_sample(
            self, patient_id: str, sample: Sample, sample_service_cls: SampleService) -> Patient:
        """Link an existing sample to a patient, or create the sample if needed.
        
        Retrieves the patient by ID and the sample using the provided service,
        then establishes a relationship between them.
        
        Args:
            patient_id: The ID of the patient to link to.
            sample: The Sample record to link.
            sample_service_cls: The SampleService instance for sample operations.
        
        Returns:
            The updated Patient record with the sample linked.
        
        Raises:
            NotFoundError: If no patient with the given ID exists.
        """
        patient = patient_crud.select_patient_by_id(self.session, patient_id)
        if patient is None:
            raise NotFoundError("Patient not found")

        db_sample = sample_service_cls.get_sample_by_id(sample.id)

        return patient_crud.link_sample(self.session, patient, db_sample)

    def get_or_create_patient(self, patient: Patient) -> Patient:
        """Get an existing patient or create a new one if not found.
        
        Attempts to retrieve a patient by their ID. If not found, creates a
        new patient record with the provided data.
        
        Args:
            patient: The Patient record with data to create if not found.
        
        Returns:
            The existing or newly created Patient record.
        """
        try:
            return self.get_patient_by_id(patient.patient_id)
        except NotFoundError:
            return self.create_patient(patient)

    def link_sample_to_patient(self, patient: Patient, sample: Sample) -> Patient:
        """Create a relationship between a patient and a sample.
        
        Links the sample to the patient if not already linked. Returns the
        patient unchanged if the sample is already in the patient's sample list.
        
        Args:
            patient: The Patient record to link to.
            sample: The Sample record to link.
        
        Returns:
            The updated Patient record with the sample relationship established.
        """
        if sample in patient.samples:
            return patient

        return patient_crud.link_sample(self.session, patient, sample)
