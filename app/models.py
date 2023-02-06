# File: models.py
#
# Description: Class objects defined to be used in the application

class Patient:
    def __init__(self, name, dob, diagnosis, treatment_plans, treatment_machine, medical_images):
        self.id = None
        self.name = name
        self.dob = dob
        self.diagnosis = diagnosis
        self.treatment_plans = treatment_plans
        self.treatment_machine = treatment_machine
        self.medical_images = medical_images

class TreatmentPlan:
    def __init__(self, name, dose, fractionation):
        self.name = name
        self.dose = dose
        self.fractionation = fractionation

class TreatmentMachine:
    def __init__(self, name, energy):
        self.name = name
        self.energy = energy

class MedicalImage:
    def __init__(self, image_type, date_acquired):
        self.image_type = image_type
        self.date_acquired = date_acquired