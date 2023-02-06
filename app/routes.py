# File: routes.py
#
# Description:  Main routing definitions and data logic for each API (route).
#               Most routes return a rendered template to be displayed on the frontend.
#               For now, we simulate a CRUD methodology. No database connection as of yet.

from app import app
from flask import render_template, request, redirect, url_for
from app.models import Patient, TreatmentPlan, TreatmentMachine, MedicalImage
import os
from os import listdir
import random
from shutil import copy, rmtree

# global variables to be used across pages
patients = []
diagnoses = ["Breast Cancer", "Lung Cancer",
             "Prostate Cancer", "Colorectal Cancer", "Leukemia"]

# full path to the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Home page
@app.route('/')
def home():
    global patients
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
        patient_dob = request.form["patient_dob"]
        patient_diagnosis = request.form["patient_diagnosis"]
        treatment_plan_names = request.form.getlist("plan_name[]")
        treatment_plan_doses = request.form.getlist("plan_dose[]")
        treatment_plan_fractions = request.form.getlist("plan_fractionation[]")
        machine_name = request.form["machine_name"]
        machine_energy = request.form["machine_energy"]
        medical_image_types = request.form.getlist("image_type[]")
        medical_image_dates = request.form.getlist("image_date_acquired[]")

        # Create treatment plan objects
        treatment_plans = []
        for i in range(len(treatment_plan_names)):
            treatment_plan = TreatmentPlan(
                treatment_plan_names[i],
                treatment_plan_doses[i],
                treatment_plan_fractions[i]
            )
            treatment_plans.append(treatment_plan)

        # Create medical image objects
        medical_images = []
        for i in range(len(medical_image_types)):
            medical_image = MedicalImage(
                medical_image_types[i],
                medical_image_dates[i]
            )
            medical_images.append(medical_image)

        # Create treatment machine object
        treatment_machine = TreatmentMachine(machine_name, machine_energy)

        # Create patient object
        patient = Patient(patient_name, patient_dob, patient_diagnosis,
                          treatment_plans, treatment_machine, medical_images)
        
        # Assigning id to simply follow the size of the patient list
        patient.id = len(patients) + 1

        patients.append(patient) # add patient object to global list

        # Explanation:  Here we are simulating the retrieval of patient images.
        #               Essentially, we grab random files from sample_images folder and 
        #               put them in a subdirectory in the static/ folder where the 
        #               subdirectory name is just the patient id.
        #               To be used on the "view patient" page.
        patient_dir = os.path.join(BASE_DIR, f"static/{patient.id}")
        patient_images_dir = os.path.join(patient_dir, "images")

        # If patient's directory already exists, remove its contents
        if os.path.exists(patient_dir):
            rmtree(patient_dir)
        os.mkdir(patient_dir)  # create subfolder for patient
        os.mkdir(patient_images_dir)  # create images subfolder

        # copy random image to patient's images folder
        for i in range(len(medical_images)):
            src_path = random.choice(os.listdir(
                os.path.join(BASE_DIR, "static/sample_images")))
            src_path = os.path.join(
                BASE_DIR, f"static/sample_images/{src_path}")
            dst_path = patient_images_dir
            copy(src_path, dst_path)

        return redirect(url_for("home")) # go back home on submission
    return render_template("create_patient.html", diagnoses=diagnoses)

# Update/Edit Patient page
@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    global patients # use global list of patients

    patient = [p for p in patients if p.id == id][0] # find patient

    # submit button clicked
    if request.method == 'POST':

        # get all form fields and update each patient object parameter
        patient.name = request.form['patient_name']
        patient.dob = request.form['patient_dob']
        patient.diagnosis = request.form['patient_diagnosis']

        
        treatment_plan_names = request.form.getlist("plan_name[]")
        treatment_plan_doses = request.form.getlist("plan_dose[]")
        treatment_plan_fractions = request.form.getlist("plan_fractionation[]")

        # Create treatment plan objects and overwrite old treatment plan info
        patient.treatment_plans = []
        for i in range(len(treatment_plan_names)):
            treatment_plan = TreatmentPlan(
                treatment_plan_names[i],
                treatment_plan_doses[i],
                treatment_plan_fractions[i]
            )
            patient.treatment_plans.append(treatment_plan)

        # Overwrite treatment machine
        patient.treatment_machine = TreatmentMachine(
            request.form['machine_name'],
            request.form['machine_energy']
        )

        # Create medical image objects and overwrite old image info
        medical_image_types = request.form.getlist("image_type[]")
        medical_image_dates = request.form.getlist("image_date_acquired[]")

        patient.medical_images = []
        for i in range(len(medical_image_types)):
            medical_image = MedicalImage(
                medical_image_types[i],
                medical_image_dates[i]
            )
            patient.medical_images.append(medical_image)

        # Explanation:  Here we are simulating the retrieval of patient images.
        #               Essentially, we grab random files from sample_images folder and 
        #               put them in a subdirectory in the static/ folder where the 
        #               subdirectory name is just the patient id.
        #               To be used on the "view patient" page.
        patient_dir = os.path.join(BASE_DIR, f"static/{patient.id}")
        patient_images_dir = os.path.join(patient_dir, "images")

        # If patient's directory already exists, remove its contents
        if os.path.exists(patient_dir):
            rmtree(patient_dir)
        os.mkdir(patient_dir)  # create subfolder for patient
        os.mkdir(patient_images_dir)  # create images subfolder

        # copy random image to patient's images folder
        for i in range(len(patient.medical_images)):
            src_path = random.choice(os.listdir(
                os.path.join(BASE_DIR, "static/sample_images")))
            src_path = os.path.join(
                BASE_DIR, f"static/sample_images/{src_path}")
            dst_path = patient_images_dir
            copy(src_path, dst_path)

        return redirect(url_for('home')) # redirect home after submission
    return render_template('update_patient.html', patient=patient, diagnoses=diagnoses)

# Remove patient API
@app.route("/remove_patient/<int:id>")
def remove_patient(id):
    global patients # use global list of patients

    # splice patient from list
    patients = [patient for patient in patients if patient.id != id]

    # remove any patient images by deleting folder 
    patient_dir = os.path.join(BASE_DIR, f"static/{id}")
    if os.path.exists(patient_dir):
        rmtree(patient_dir)

    return redirect(url_for("home"))

# View Patient page
@app.route('/view_patient/<int:id>')
def view_patient(id):
    global patients # use global list of patients

    patient = [p for p in patients if p.id == id][0] # find patient

    # Explanation:  Static patient image directories were created (see about in 
    #               "create" or "edit" routes) to simulate retrieval of images from a "backend."
    #               Here we simply grab each image to be displayed on frontend
    image_dir = os.path.join(BASE_DIR, f"static/{patient.id}/images")
    image_files = [f for f in listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]

    return render_template('view_patient.html', patient=patient, image_files=image_files, enumerate=enumerate)
