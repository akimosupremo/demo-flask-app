# File: routes.py
#
# Description:  Main routing definitions and data logic for each API (route).
#               Most routes return a rendered template to be displayed on the frontend.
#               We implement a CRUD methodology using Flask-SQLAlchemy for ORM db management
#               and pydicom for DICOM manipulations

from app import app
from flask import render_template, request, redirect, url_for, send_file
from app.models import Patient, TreatmentPlan, TreatmentMachine, MedicalImage
import os
import pydicom
from PIL import Image
from app import db
from datetime import datetime

# global variables to be used across pages
diagnoses = ["Breast Cancer", "Lung Cancer",
             "Prostate Cancer", "Colorectal Cancer", "Leukemia"]

# full path to the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Home page
@app.route('/')
def home():
    patients = Patient.query.all() # ORM
    return render_template('home.html', patients=patients)

# Basic "About radiotherapy" page
@app.route('/radiotherapy')
def radiotherapy():
    return render_template('radiotherapy.html')

# Create Patient page
@app.route('/create_patient', methods=['GET', 'POST'])
def create_patient():

    # submit button clicked
    if request.method == "POST":

        # get all form fields
        patient_name = request.form["patient_name"]
        patient_dob = datetime.strptime(request.form["patient_dob"], '%Y-%m-%d')
        patient_diagnosis = request.form["patient_diagnosis"]
        treatment_plan_names = request.form.getlist("plan_name[]")
        treatment_plan_doses = request.form.getlist("plan_dose[]")
        treatment_plan_fractions = request.form.getlist("plan_fractionation[]")
        machine_name = request.form["machine_name"]
        machine_energy = request.form["machine_energy"]
        medical_image_types = request.form.getlist("image_type[]")
        medical_image_dates = request.form.getlist("image_date_acquired[]")

        patient = Patient(name=patient_name, date_of_birth=patient_dob, diagnosis=patient_diagnosis)
        db.session.add(patient)
        db.session.commit() # save changes to allow retrieval of patient id

        # Create treatment plan objects
        for i in range(len(treatment_plan_names)):
            treatment_plan = TreatmentPlan(patient_id=patient.id, name=treatment_plan_names[i], dose=treatment_plan_doses[i], fractionation=treatment_plan_fractions[i])
            db.session.add(treatment_plan)

        # Create medical image objects
        for i in range(len(medical_image_types)):
            medical_image = MedicalImage(patient_id=patient.id, type=medical_image_types[i], date_acquired=datetime.strptime(medical_image_dates[i], '%Y-%m-%d'))
            db.session.add(medical_image)

        # Create treatment machine object
        treatment_machine = TreatmentMachine(patient_id=patient.id, name=machine_name, energy=machine_energy)
        db.session.add(treatment_machine)

        db.session.commit()

        return redirect(url_for("home")) # go back home on submission
    return render_template("create_patient.html", diagnoses=diagnoses)

# Update/Edit Patient page
@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    patient = Patient.query.get(id)
    # Get the existing treatment plans for this patient
    existing_plans = TreatmentPlan.query.filter_by(patient_id=id).all()
    existing_plan_ids = [plan.id for plan in existing_plans]

    treatment_machine = TreatmentMachine.query.filter_by(patient_id=id).first()

    # Get the existing treatment plans for this patient
    existing_images = MedicalImage.query.filter_by(patient_id=id).all()
    existing_image_ids = [image.id for image in existing_images]

    # submit button clicked
    if request.method == 'POST':

        # get all form fields and update each patient object parameter
        patient.name = request.form['patient_name']
        patient.date_of_birth = datetime.strptime(request.form['patient_dob'], '%Y-%m-%d')
        patient.diagnosis = request.form['patient_diagnosis']
        db.session.commit()
        
        treatment_plan_names = request.form.getlist("plan_name[]")
        treatment_plan_doses = request.form.getlist("plan_dose[]")
        treatment_plan_fractions = request.form.getlist("plan_fractionation[]")

        # Update existing plans
        for i, plan in enumerate(existing_plans):
            plan.plan_name = treatment_plan_names[i]
            plan.dose = treatment_plan_doses[i]
            plan.fractionation = treatment_plan_fractions[i]
     
         # Add new plans
        for i in range(len(existing_plans), len(treatment_plan_names)):
            new_plan = TreatmentPlan(
                name=treatment_plan_names[i], dose=treatment_plan_doses[i], fractionation=treatment_plan_fractions[i], patient_id=patient.id
            )
            db.session.add(new_plan)

        # Remove plans that were deleted from the form
        for plan in existing_plans:
            if plan.id not in existing_plan_ids:
                db.session.delete(plan)
        
        # Update the treatment machine information
        treatment_machine.name = request.form.get("machine_name")
        treatment_machine.energy = request.form.get("machine_energy")

        # Create medical image objects and overwrite old image info
        medical_image_types = request.form.getlist("image_type[]")
        medical_image_dates = request.form.getlist("image_date_acquired[]")

        # Update existing images
        for i, image in enumerate(existing_images):
            image.type = medical_image_types[i]
            image.date_acquired = datetime.strptime(medical_image_dates[i], '%Y-%m-%d')
     
         # Add new images
        for i in range(len(existing_images), len(medical_image_types)):
            new_image = MedicalImage(
                type=medical_image_types[i], date_acquired=datetime.strptime(medical_image_dates[i], '%Y-%m-%d'), patient_id=patient.id
            )
            db.session.add(new_image)

        # Remove plans that were deleted from the form
        for image in existing_images:
            if image.id not in existing_image_ids:
                db.session.delete(image)

        db.session.commit() # save all changes
        return redirect(url_for('home')) # redirect home after submission
    return render_template('update_patient.html', patient=patient, diagnoses=diagnoses, treatment_plans=existing_plans, treatment_machine=treatment_machine, medical_images=existing_images)

# Remove patient API
@app.route("/remove_patient/<int:id>")
def remove_patient(id):
    # use ORM to commit deletion from db
    patient = Patient.query.get(id)
    db.session.delete(patient)
    db.session.commit()

    return redirect(url_for("home"))

# View Patient page
@app.route('/view_patient/<int:id>')
def view_patient(id):
    patient = Patient.query.get(id)

    # get the number of dicom files
    dicom_dir = BASE_DIR + "/static/dicom"
    dicom_files = [f for f in os.listdir(dicom_dir) if f.endswith(".dcm")]
    num_slices = len(dicom_files)

    return render_template('view_patient.html', patient=patient, num_slices=num_slices)

# View dicom slice API
@app.route("/view_ct_slice/<int:slice_index>")
def view_ct_slice(slice_index):
    # paths
    dicom_dir = BASE_DIR + "/static/dicom"
    output_dir = BASE_DIR + "/static/dump/converted_dicom"

    # create directory for output and don't complain if it exists
    os.makedirs(output_dir, exist_ok=True)
  
    # Convert dicom files to PNG
    dicom_files = [f for f in os.listdir(dicom_dir) if f.endswith(".dcm")]
    dicom_files.sort()
    dicom_file = os.path.join(dicom_dir, f"{dicom_files[slice_index]}")
    dicom_data = pydicom.dcmread(dicom_file)
    image = dicom_data.pixel_array
    image = Image.fromarray(image)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(f"{output_dir}/slice_{slice_index}.png") # save location

    # return path for display
    return send_file(f"{output_dir}/slice_{slice_index}.png", mimetype="image/png")