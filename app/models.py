# File: models.py
#
# Description: Class objects defined to be used in the application

from flask_sqlalchemy import SQLAlchemy
from app import db

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    diagnosis = db.Column(db.String(200), nullable=False)

class TreatmentPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    patient = db.relationship("Patient", backref=db.backref("plans", cascade="all, delete-orphan"))
    name = db.Column(db.String(100), nullable=False)
    dose = db.Column(db.Float, nullable=False)
    fractionation = db.Column(db.Float, nullable=False)

class TreatmentMachine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    patient = db.relationship("Patient", backref=db.backref("machines", cascade="all, delete-orphan"))
    name = db.Column(db.String(100), nullable=False)
    energy = db.Column(db.String(100), nullable=False)

class MedicalImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    patient = db.relationship("Patient", backref=db.backref("images", cascade="all, delete-orphan"))
    type = db.Column(db.String(100), nullable=False)
    date_acquired = db.Column(db.Date, nullable=False)