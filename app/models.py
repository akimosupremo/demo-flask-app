# File: models.py
#
# Description: Class objects defined to be used in the application
from app import db

class Patient(db.Model):
    __tablename__ = 'Patient'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    diagnosis = db.Column(db.String(200), nullable=False)

# PatientObj model
class PatientObj:
    def __init__(self, id, name, date_of_birth, diagnosis):
        self.id = id
        self.name = name
        self.date_of_birth = date_of_birth
        self.diagnosis = diagnosis

class TreatmentPlan(db.Model):
    __tablename__ = 'TreatmentPlan'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.id'), nullable=False)
    # enables all plans for a given patient to be deleted if the patient is deleted
    patient = db.relationship("Patient", backref=db.backref("plans", cascade="all, delete-orphan"))
    name = db.Column(db.String(100), nullable=False)
    dose = db.Column(db.Float, nullable=False)
    fractionation = db.Column(db.Float, nullable=False)

# TreatmentPlanObj model
class TreatmentPlanObj:
    def __init__(self, id, patient_id, name, dose, fractionation):
        self.id = id
        self.patient_id = patient_id
        self.name = name
        self.dose = dose
        self.fractionation = fractionation

class TreatmentMachine(db.Model):
    __tablename__ = 'TreatmentMachine'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.id'), nullable=False)
    # enables all machine info for a given patient to be deleted if the patient is deleted
    patient = db.relationship("Patient", backref=db.backref("machines", cascade="all, delete-orphan"))
    name = db.Column(db.String(100), nullable=False)
    energy = db.Column(db.String(100), nullable=False)

# TreatmentMachineObj model
class TreatmentMachineObj:
    def __init__(self, id, patient_id, name, energy):
        self.id = id
        self.patient_id = patient_id
        self.name = name
        self.energy = energy

class MedicalImage(db.Model):
    __tablename__ = 'MedicalImage'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('Patient.id'), nullable=False)
    # enables all image info for a given patient to be deleted if the patient is deleted
    patient = db.relationship("Patient", backref=db.backref("images", cascade="all, delete-orphan"))
    type = db.Column(db.String(100), nullable=False)
    date_acquired = db.Column(db.Date, nullable=False)
    
# MedicalImageObj model
class MedicalImageObj:
    def __init__(self, id, patient_id, type, date_acquired):
        self.id = id
        self.patient_id = patient_id
        self.type = type
        self.date_acquired = date_acquired

class Diagnosis(db.Model):
    __tablename__ = 'Diagnosis'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class DiagnosisObj:
    def __init__(self, id, name):
        self.id = id
        self.name = name