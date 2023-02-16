# File: routes.py
#
# Description:  Main routing definitions and data logic for each API (route).
#               Most routes return a rendered template to be displayed on the frontend.
#               We implement a CRUD methodology using Flask-SQLAlchemy for ORM db management
#               and pydicom for DICOM manipulations

from app import app
from flask import render_template, request, redirect, url_for, send_file, g
from app.models import Patient, TreatmentPlan, TreatmentMachine, MedicalImage, Diagnosis
from app.models import PatientObj, TreatmentPlanObj, TreatmentMachineObj, MedicalImageObj, DiagnosisObj
from app import cnxpool, cnx
import os
import pydicom
from PIL import Image
from app import db
from datetime import datetime

"""
PREAMBLE: 
In Flask, the 'g' object is a global object that can be used to store data during a request.
In this case, we use the g object to store a database connection that needs to be 
reused by multiple routes during a request. 

This allows use to define decorators that can be used to get and release a database connection.
This in turn allows us to avoid resource leaks and potential performance issues.

You can also avoid the decorators and use cnx instead of g.db, wherever defined in the routings.
"""

# Define a Flask before_request handler that gets a database connection 
# from the connection pool and stores it in the g object.
@app.before_request
def get_db():
    g.db = cnxpool.get_connection()

# Define a Flask teardown_request handler to release the database connection
@app.teardown_request
def release_db(error):
    if hasattr(g, 'db'):
        g.db.close()

# full path to the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global variable to toggle between ORM and SQL
USE_ORM = False

# Home page
@app.route('/')
def home():
    if USE_ORM:
        patients = Patient.query.all()
    else:
        cursor = g.db.cursor(dictionary=True)
        query = "SELECT id, name, date_of_birth, diagnosis FROM Patient"
        cursor.execute(query)
        patients = []
        for row in cursor:
            patient = PatientObj(row['id'], row['name'], row['date_of_birth'], row['diagnosis'])
            patients.append(patient)

        cursor.close()

    return render_template('home.html', patients=patients)

# Basic "About radiotherapy" page
@app.route('/radiotherapy')
def radiotherapy():
    return render_template('radiotherapy.html')

# Create Patient page
@app.route('/create_patient', methods=['GET', 'POST'])
def create_patient():

    # Get all diagnoses from the database
    if USE_ORM:
        diagnoses = Diagnosis.query.all()
    else:
        cursor = g.db.cursor(dictionary=True)
        query = "SELECT id, name FROM Diagnosis"
        cursor.execute(query)
        diagnoses = []
        for row in cursor:
            diagnosis = DiagnosisObj(row['id'], row['name'])
            diagnoses.append(diagnosis)

        cursor.close()
    
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

        if USE_ORM:
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
        else:
            cursor = g.db.cursor(dictionary=True)

            # Create patient object
            query = "INSERT INTO Patient (name, date_of_birth, diagnosis) VALUES (%s, %s, %s)"
            values = (patient_name, patient_dob, patient_diagnosis)
            cursor.execute(query, values)
            g.db.commit()

            # Get the patient id of the newly created patient
            patient_id = cursor.lastrowid

            # Create treatment plan objects
            for i in range(len(treatment_plan_names)):
                query = "INSERT INTO TreatmentPlan (patient_id, name, dose, fractionation) VALUES (%s, %s, %s, %s)"
                values = (patient_id, treatment_plan_names[i], treatment_plan_doses[i], treatment_plan_fractions[i])
                cursor.execute(query, values)

            # Create medical image objects
            for i in range(len(medical_image_types)):
                query = "INSERT INTO MedicalImage (patient_id, type, date_acquired) VALUES (%s, %s, %s)"
                values = (patient_id, medical_image_types[i], datetime.strptime(medical_image_dates[i], '%Y-%m-%d'))
                cursor.execute(query, values)

            # Create treatment machine object
            query = "INSERT INTO TreatmentMachine (patient_id, name, energy) VALUES (%s, %s, %s)"
            values = (patient_id, machine_name, machine_energy)
            cursor.execute(query, values)

            g.db.commit()
            cursor.close()

        return redirect(url_for("home")) # go back home on submission
    return render_template("create_patient.html", diagnoses=diagnoses)

# Update/Edit Patient page
@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    if USE_ORM:
        patient = Patient.query.get(id)
        diagnoses = Diagnosis.query.all()
        # Get the existing treatment plans for this patient
        existing_plans = TreatmentPlan.query.filter_by(patient_id=id).all()
        existing_plan_ids = [plan.id for plan in existing_plans]

        treatment_machine = TreatmentMachine.query.filter_by(patient_id=id).first()

        # Get the existing treatment plans for this patient
        existing_images = MedicalImage.query.filter_by(patient_id=id).all()
        existing_image_ids = [image.id for image in existing_images]
    else:
        cursor = g.db.cursor(dictionary=True)
        query = "SELECT * FROM Patient WHERE id = %s"
        values = (id,)
        cursor.execute(query, values)
        result = cursor.fetchone()
        patient = PatientObj(**result)

        query = "SELECT id, name FROM Diagnosis"
        cursor.execute(query)
        diagnoses = []
        for row in cursor:
            diagnosis = DiagnosisObj(row['id'], row['name'])
            diagnoses.append(diagnosis)

        query = "SELECT * FROM TreatmentPlan WHERE patient_id = %s"
        values = (id,)
        cursor.execute(query, values)
        existing_plans = []
        existing_plan_ids = []
        for row in cursor:
            plan = TreatmentPlanObj(**row)
            existing_plans.append(plan)
            existing_plan_ids.append(plan.id)

        query = "SELECT * FROM TreatmentMachine WHERE patient_id = %s"
        values = (id,)
        cursor.execute(query, values)
        result = cursor.fetchone()
        treatment_machine = TreatmentMachineObj(**result)

        query = "SELECT * FROM MedicalImage WHERE patient_id = %s"
        values = (id,)
        cursor.execute(query, values)
        existing_images = []
        existing_image_ids = []
        for row in cursor:
            image = MedicalImageObj(**row)
            existing_images.append(image)
            existing_image_ids.append(image.id)
        
        cursor.close()

    # submit button clicked
    if request.method == 'POST':

        if USE_ORM:
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
        else:
            # get all form fields and update each patient object parameter
            cursor = g.db.cursor()
            query = "UPDATE Patient SET name = %s, date_of_birth = %s, diagnosis = %s WHERE id = %s"
            values = (request.form['patient_name'], request.form['patient_dob'], request.form['patient_diagnosis'], id)
            cursor.execute(query, values)
            g.db.commit()

            # Update treatment plans
            treatment_plan_names = request.form.getlist("plan_name[]")
            treatment_plan_doses = request.form.getlist("plan_dose[]")
            treatment_plan_fractions = request.form.getlist("plan_fractionation[]")

            # Update existing plans
            for i, plan_id in enumerate(existing_plan_ids):
                query = "UPDATE TreatmentPlan SET name = %s, dose = %s, fractionation = %s WHERE id = %s"
                values = (treatment_plan_names[i], treatment_plan_doses[i], treatment_plan_fractions[i], plan_id)
                cursor.execute(query, values)
                g.db.commit()

            # Add new plans
            for i in range(len(existing_plan_ids), len(treatment_plan_names)):
                query = "INSERT INTO TreatmentPlan (plan_name, dose, fractionation, patient_id) VALUES (%s, %s, %s, %s)"
                values = (treatment_plan_names[i], treatment_plan_doses[i], treatment_plan_fractions[i], id)
                cursor.execute(query, values)
                g.db.commit()

            # Remove plans that were deleted from the form
            for plan in existing_plans:
                if plan.id not in existing_plan_ids:
                    query = "DELETE FROM TreatmentPlan WHERE id = %s"
                    values = (plan.id,)
                    cursor.execute(query, values)
                    g.db.commit()

            # Update the treatment machine information
            query = "UPDATE TreatmentMachine SET name = %s, energy = %s WHERE patient_id = %s"
            values = (request.form.get("machine_name"), request.form.get("machine_energy"), id)
            cursor.execute(query, values)
            g.db.commit()

            # Update medical images
            medical_image_types = request.form.getlist("image_type[]")
            medical_image_dates = request.form.getlist("image_date_acquired[]")

            # Update existing images
            for i, image_id in enumerate(existing_image_ids):
                query = "UPDATE MedicalImage SET type = %s, date_acquired = %s WHERE id = %s"
                values = (medical_image_types[i], medical_image_dates[i], image_id)
                cursor.execute(query, values)
                g.db.commit()
            
            # Add new images
            for i in range(len(existing_image_ids), len(medical_image_types)):
                query = "INSERT INTO MedicalImage (type, date_acquired, patient_id) VALUES (%s, %s, %s)"
                values = (medical_image_types[i], medical_image_dates[i], id)
                cursor.execute(query, values)
                g.db.commit()

            # Remove images that were deleted from the form
            for image in existing_images:
                if image.id not in existing_image_ids:
                    query = "DELETE FROM MedicalImage WHERE id = %s"
                    values = (image.id,)
                    cursor.execute(query, values)
                    g.db.commit()

        return redirect(url_for('home')) # redirect home after submission
    return render_template('update_patient.html', patient=patient, diagnoses=diagnoses, treatment_plans=existing_plans, treatment_machine=treatment_machine, medical_images=existing_images)

# Remove patient API
@app.route("/remove_patient/<int:id>")
def remove_patient(id):
    if USE_ORM:
        patient = Patient.query.get(id)
        db.session.delete(patient)
        db.session.commit()
    else:
        # remove patient from database
        cursor = g.db.cursor()
        query = "DELETE FROM patient WHERE id = %s"
        cursor.execute(query, (id,))
        g.db.commit()
        cursor.close()

    return redirect(url_for("home"))

# View Patient page
@app.route('/view_patient/<int:id>')
def view_patient(id):
    if USE_ORM:
        patient = Patient.query.get(id)
    else:
        # get patient from database
        cursor = g.db.cursor(dictionary=True)
        query = "SELECT * FROM patient WHERE id = %s"
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        patient = PatientObj(**result)
        cursor.close()
        
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