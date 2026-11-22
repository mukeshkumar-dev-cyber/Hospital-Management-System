
# HOSPITAL MANAGEMENT SYSTEM

from getpass import getpass
import mysql.connector
import os
import hashlib
import secrets
import hmac
import datetime

print("""
================================
     WELCOME TO MY HOSPITAL
================================
""")

db_password = os.getenv("MYSQL_PASSWORD")
if not db_password:
    db_password = getpass("Enter MySQL root password: ")
# Database connectivity
mysql = mysql.connector.connect(
    host="localhost",
    user="root",
    password=db_password,
    port=3306
)

mycursor = mysql.cursor()

# Creating and selecting database
mycursor.execute("CREATE DATABASE IF NOT EXISTS hospital")
mycursor.execute("USE hospital")

# Creating patient table
mycursor.execute("""
CREATE TABLE IF NOT EXISTS patient_details(
    puid VARCHAR(10) PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    age INT,
    address VARCHAR(50),
    contact VARCHAR(15),
    date_of_visit DATE NOT NULL,
    doctor_prescribed VARCHAR(30),
    medicine_prescribed VARCHAR(20),
    qty INT
)
""")

# Adding username column to patient_details table if it doesn't exist

mycursor.execute("""
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = 'hospital'
    AND table_name = 'patient_details'
    AND column_name = 'username'
""")

if mycursor.fetchone()[0] == 0:
    mycursor.execute("""
        ALTER TABLE patient_details
        ADD COLUMN username VARCHAR(30) UNIQUE
    """)

# Creating doctor table
mycursor.execute("""
CREATE TABLE IF NOT EXISTS doctor_details(
    duid VARCHAR(10) PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    specialisation VARCHAR(40),
    age INT,
    address VARCHAR(30),
    contact VARCHAR(15),
    fees INT,
    monthly_salary INT
)
""")

# Creating nurse table
mycursor.execute("""
CREATE TABLE IF NOT EXISTS nurse_details(
    nuid VARCHAR(10) PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    age INT,
    address VARCHAR(30),
    contact VARCHAR(15),
    monthly_salary INT
)
""")

# Creating other workers table
mycursor.execute("""
CREATE TABLE IF NOT EXISTS other_workers_details(
    wuid VARCHAR(10) PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    age INT,
    address VARCHAR(30),
    contact VARCHAR(15),
    monthly_salary INT
)
""")

# Creating user table
mycursor.execute("""
CREATE TABLE IF NOT EXISTS user_data(
    username VARCHAR(30) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'PATIENT'
)
""")

# Updating existing user table if necessary
mycursor.execute("""
ALTER TABLE user_data
MODIFY password VARCHAR(255) NOT NULL
""")

mycursor.execute("""
SELECT COUNT(*)
FROM information_schema.columns
WHERE table_schema = 'hospital'
AND table_name = 'user_data'
AND column_name = 'role'
""")

if mycursor.fetchone()[0] == 0:
    mycursor.execute("""
    ALTER TABLE user_data
    ADD role VARCHAR(10) NOT NULL DEFAULT 'PATIENT'
    """)

# Creating medicine inventory table
mycursor.execute("""
CREATE TABLE IF NOT EXISTS inventory(
    medicine_name VARCHAR(15) PRIMARY KEY,
    stock INT NOT NULL
)
""")

mysql.commit()

print("Database and tables created successfully.")

# PASSWORD HASHING

def hash_password(password):
    salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        200000
    ).hex()

    return salt + "$" + hashed


def verify_password(password, stored_password):
    try:
        salt, stored_hash = stored_password.split("$")

        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            200000
        ).hex()

        return hmac.compare_digest(new_hash, stored_hash)

    except ValueError:
        return False


# ACCOUNT MENU

def account_menu(user_type):

    while True:
        print("""
================================
        ACCOUNT MENU
================================
1. SIGN UP
2. LOGIN
3. BACK
""")

        choice = input("ENTER YOUR CHOICE: ")

        # SIGN UP
        if choice == "1":

            username = input("CREATE USERNAME: ")
            password = getpass("CREATE PASSWORD: ")

            if len(password) < 8:
                print("PASSWORD MUST BE AT LEAST 8 CHARACTERS.")
                continue

            hashed_password = hash_password(password)

            try:
                mycursor.execute(
                    """
                    INSERT INTO user_data (username, password, role)
                    VALUES (%s, %s, %s)
                    """,
                    (username, hashed_password, user_type)
                )

                mysql.commit()

                print("ACCOUNT CREATED SUCCESSFULLY!")

            except mysql.connector.IntegrityError:
                mysql.rollback()
                print("USERNAME ALREADY EXISTS.")

        # LOGIN
        elif choice == "2":

            username = input("ENTER USERNAME: ")
            password = getpass("ENTER PASSWORD: ")

            mycursor.execute(
                """
                SELECT password
                FROM user_data
                WHERE username = %s AND role = %s
                """,
                (username, user_type)
            )

            result = mycursor.fetchone()

            if result and verify_password(password, result[0]):
                print("LOGIN SUCCESSFUL!")

                if user_type == "PATIENT":
                    patient_menu(username)

                elif user_type == "EMPLOYEE":
                    employee_menu(username)

            else:
                print("INVALID USERNAME OR PASSWORD.")

        elif choice == "3":
            break

        else:
            print("INVALID CHOICE.")

# PATIENT REGISTRATION

def register_patient():
    print("\n===== PATIENT REGISTRATION =====")

    puid = "P" + secrets.token_hex(4).upper()

    name = input("Enter patient name: ")
    age = input("Enter patient age: ")
    address = input("Enter address: ")
    contact = input("Enter contact number: ")

    try:
        age = int(age)

        if age <= 0:
            print("Invalid age.")
            return

        mycursor.execute("""
            INSERT INTO patient_details
            (puid, name, age, address, contact, date_of_visit,
             doctor_prescribed, medicine_prescribed, qty)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            puid,
            name,
            age,
            address,
            contact,
            datetime.date.today(),
            "",
            "",
            0
        ))

        mysql.commit()

        print("\nPATIENT REGISTERED SUCCESSFULLY!")
        print("Patient ID:", puid)

    except ValueError:
        print("Age must be a valid number.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# DOCTOR REGISTRATION

def register_doctor():
    print("\n===== DOCTOR REGISTRATION =====")

    duid = "D" + secrets.token_hex(4).upper()

    name = input("Enter doctor name: ")
    specialisation = input("Enter specialisation: ")
    age = input("Enter doctor age: ")
    address = input("Enter address: ")
    contact = input("Enter contact number: ")
    fees = input("Enter consultation fees: ")
    monthly_salary = input("Enter monthly salary: ")

    try:
        age = int(age)
        fees = int(fees)
        monthly_salary = int(monthly_salary)

        if age <= 0 or fees < 0 or monthly_salary < 0:
            print("Invalid input values.")
            return

        mycursor.execute("""
            INSERT INTO doctor_details
            (duid, name, specialisation, age, address,
             contact, fees, monthly_salary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            duid, name, specialisation, age,
            address, contact, fees, monthly_salary
        ))

        mysql.commit()

        print("\nDOCTOR REGISTERED SUCCESSFULLY!")
        print("Doctor ID:", duid)

    except ValueError:
        print("Age, fees and salary must be valid numbers.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# VIEW PATIENT RECORD

def view_patient():
    print("\n===== SEARCH PATIENT =====")

    puid = input("Enter Patient ID: ").strip().upper()

    mycursor.execute("""
        SELECT puid, name, age, address, contact, date_of_visit,
               doctor_prescribed, medicine_prescribed, qty
        FROM patient_details
        WHERE puid = %s
    """, (puid,))

    patient = mycursor.fetchone()

    if patient:
        print("\n========== PATIENT RECORD ==========")
        print("Patient ID          :", patient[0])
        print("Name               :", patient[1])
        print("Age                :", patient[2])
        print("Address            :", patient[3])
        print("Contact            :", patient[4])
        print("Date of Visit      :", patient[5])
        print("Doctor Prescribed  :", patient[6])
        print("Medicine Prescribed:", patient[7])
        print("Quantity           :", patient[8])
        print("=================================")

    else:
        print("No patient found with this ID.")

# VIEW DOCTOR RECORD

def view_doctor():
    print("\n===== SEARCH DOCTOR =====")

    duid = input("Enter Doctor ID: ").strip().upper()

    mycursor.execute("""
        SELECT duid, name, specialisation, age, address,
               contact, fees, monthly_salary
        FROM doctor_details
        WHERE duid = %s
    """, (duid,))

    doctor = mycursor.fetchone()

    if doctor:
        print("\n===== DOCTOR DETAILS =====")
        print("Doctor ID:", doctor[0])
        print("Name:", doctor[1])
        print("Specialisation:", doctor[2])
        print("Age:", doctor[3])
        print("Address:", doctor[4])
        print("Contact:", doctor[5])
        print("Consultation Fees:", doctor[6])
        print("Monthly Salary:", doctor[7])
    else:
        print("Doctor not found.")
        
# UPDATE PATIENT DETAILS

def update_patient():
    print("\n===== UPDATE PATIENT DETAILS =====")

    puid = input("Enter Patient ID: ").strip().upper()

    mycursor.execute("""
        SELECT name, age, address, contact
        FROM patient_details
        WHERE puid = %s
    """, (puid,))

    patient = mycursor.fetchone()

    if not patient:
        print("Patient not found.")
        return

    print("\nLeave a field blank to keep its current value.")

    name = input(f"Name [{patient[0]}]: ").strip()
    age = input(f"Age [{patient[1]}]: ").strip()
    address = input(f"Address [{patient[2]}]: ").strip()
    contact = input(f"Contact [{patient[3]}]: ").strip()

    # Keep old values when inputs are blank
    name = name if name else patient[0]
    address = address if address else patient[2]
    contact = contact if contact else patient[3]

    if age:
        try:
            age = int(age)

            if age <= 0:
                print("Age must be a positive number.")
                return

        except ValueError:
            print("Invalid age.")
            return
    else:
        age = patient[1]

    try:
        mycursor.execute("""
            UPDATE patient_details
            SET name = %s, age = %s, address = %s, contact = %s
            WHERE puid = %s
        """, (name, age, address, contact, puid))

        mysql.commit()
        print("PATIENT DETAILS UPDATED SUCCESSFULLY!")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# UPDATE DOCTOR DETAILS

def update_doctor():
    print("\n===== UPDATE DOCTOR DETAILS =====")

    duid = input("Enter Doctor ID: ").strip().upper()

    mycursor.execute("""
        SELECT name, specialisation, age, address,
               contact, fees, monthly_salary
        FROM doctor_details
        WHERE duid = %s
    """, (duid,))

    doctor = mycursor.fetchone()

    if not doctor:
        print("Doctor not found.")
        return

    print("\nLeave a field blank to retain its existing value.")

    name = input(f"Name [{doctor[0]}]: ") or doctor[0]
    specialisation = input(
        f"Specialisation [{doctor[1]}]: "
    ) or doctor[1]

    age = input(f"Age [{doctor[2]}]: ") or doctor[2]
    address = input(f"Address [{doctor[3]}]: ") or doctor[3]
    contact = input(f"Contact [{doctor[4]}]: ") or doctor[4]
    fees = input(f"Fees [{doctor[5]}]: ") or doctor[5]
    monthly_salary = input(
        f"Monthly Salary [{doctor[6]}]: "
    ) or doctor[6]

    try:
        age = int(age)
        fees = int(fees)
        monthly_salary = int(monthly_salary)

        if age <= 0 or fees < 0 or monthly_salary < 0:
            print("Invalid values.")
            return

        mycursor.execute("""
            UPDATE doctor_details
            SET name = %s,
                specialisation = %s,
                age = %s,
                address = %s,
                contact = %s,
                fees = %s,
                monthly_salary = %s
            WHERE duid = %s
        """, (
            name, specialisation, age, address,
            contact, fees, monthly_salary, duid
        ))

        mysql.commit()
        print("\nDOCTOR DETAILS UPDATED SUCCESSFULLY!")

    except ValueError:
        print("Age, fees and salary must be valid numbers.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# DELETE PATIENT RECORD

def delete_patient():
    print("\n===== DELETE PATIENT RECORD =====")

    puid = input("Enter Patient ID: ").strip().upper()

    mycursor.execute("""
        SELECT name
        FROM patient_details
        WHERE puid = %s
    """, (puid,))

    patient = mycursor.fetchone()

    if not patient:
        print("Patient record not found.")
        return

    print("Patient Name:", patient[0])

    confirm = input(
        "Are you sure you want to delete this record? (YES/NO): "
    ).strip().upper()

    if confirm == "YES":
        try:
            mycursor.execute("""
                DELETE FROM patient_details
                WHERE puid = %s
            """, (puid,))

            mysql.commit()
            print("PATIENT RECORD DELETED SUCCESSFULLY.")

        except mysql.connector.Error as err:
            mysql.rollback()
            print("Database error:", err)

    else:
        print("Deletion cancelled.")

# DELETE DOCTOR RECORD

def delete_doctor():
    print("\n===== DELETE DOCTOR RECORD =====")

    duid = input("Enter Doctor ID: ").strip().upper()

    mycursor.execute("""
        SELECT name
        FROM doctor_details
        WHERE duid = %s
    """, (duid,))

    doctor = mycursor.fetchone()

    if not doctor:
        print("Doctor record not found.")
        return

    print("Doctor Name:", doctor[0])

    confirm = input(
        "Are you sure you want to delete this record? (YES/NO): "
    ).strip().upper()

    if confirm == "YES":
        try:
            mycursor.execute("""
                DELETE FROM doctor_details
                WHERE duid = %s
            """, (duid,))

            mysql.commit()
            print("DOCTOR RECORD DELETED SUCCESSFULLY.")

        except mysql.connector.Error as err:
            mysql.rollback()
            print("Database error:", err)

    else:
        print("Deletion cancelled.")

# NURSE REGISTRATION

def register_nurse():
    print("\n===== NURSE REGISTRATION =====")

    nuid = "N" + secrets.token_hex(4).upper()

    name = input("Enter nurse name: ")
    age = input("Enter nurse age: ")
    address = input("Enter address: ")
    contact = input("Enter contact number: ")
    monthly_salary = input("Enter monthly salary: ")

    try:
        age = int(age)
        monthly_salary = int(monthly_salary)

        if age <= 0 or monthly_salary < 0:
            print("Invalid input values.")
            return

        mycursor.execute("""
            INSERT INTO nurse_details
            (nuid, name, age, address, contact, monthly_salary)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nuid, name, age, address, contact, monthly_salary))

        mysql.commit()

        print("\nNURSE REGISTERED SUCCESSFULLY!")
        print("Nurse ID:", nuid)

    except ValueError:
        print("Age and salary must be valid numbers.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# VIEW NURSE RECORD

def view_nurse():
    print("\n===== SEARCH NURSE =====")

    nuid = input("Enter Nurse ID: ").strip().upper()

    mycursor.execute("""
        SELECT nuid, name, age, address, contact, monthly_salary
        FROM nurse_details
        WHERE nuid = %s
    """, (nuid,))

    nurse = mycursor.fetchone()

    if nurse:
        print("\n===== NURSE DETAILS =====")
        print("Nurse ID:", nurse[0])
        print("Name:", nurse[1])
        print("Age:", nurse[2])
        print("Address:", nurse[3])
        print("Contact:", nurse[4])
        print("Monthly Salary:", nurse[5])
    else:
        print("Nurse not found.")

# UPDATE NURSE DETAILS

def update_nurse():
    print("\n===== UPDATE NURSE DETAILS =====")

    nuid = input("Enter Nurse ID: ").strip().upper()

    mycursor.execute("""
        SELECT name, age, address, contact, monthly_salary
        FROM nurse_details
        WHERE nuid = %s
    """, (nuid,))

    nurse = mycursor.fetchone()

    if not nurse:
        print("Nurse not found.")
        return

    print("\nLeave a field blank to retain its existing value.")

    name = input(f"Name [{nurse[0]}]: ") or nurse[0]
    age = input(f"Age [{nurse[1]}]: ") or nurse[1]
    address = input(f"Address [{nurse[2]}]: ") or nurse[2]
    contact = input(f"Contact [{nurse[3]}]: ") or nurse[3]
    monthly_salary = input(
        f"Monthly Salary [{nurse[4]}]: "
    ) or nurse[4]

    try:
        age = int(age)
        monthly_salary = int(monthly_salary)

        if age <= 0 or monthly_salary < 0:
            print("Invalid values.")
            return

        mycursor.execute("""
            UPDATE nurse_details
            SET name = %s,
                age = %s,
                address = %s,
                contact = %s,
                monthly_salary = %s
            WHERE nuid = %s
        """, (
            name, age, address, contact, monthly_salary, nuid
        ))

        mysql.commit()
        print("\nNURSE DETAILS UPDATED SUCCESSFULLY!")

    except ValueError:
        print("Age and salary must be valid numbers.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# DELETE NURSE RECORD

def delete_nurse():
    print("\n===== DELETE NURSE RECORD =====")

    nuid = input("Enter Nurse ID: ").strip().upper()

    mycursor.execute("""
        SELECT name
        FROM nurse_details
        WHERE nuid = %s
    """, (nuid,))

    nurse = mycursor.fetchone()

    if not nurse:
        print("Nurse record not found.")
        return

    print("Nurse Name:", nurse[0])

    confirm = input(
        "Are you sure you want to delete this record? (YES/NO): "
    ).strip().upper()

    if confirm == "YES":
        try:
            mycursor.execute("""
                DELETE FROM nurse_details
                WHERE nuid = %s
            """, (nuid,))

            mysql.commit()
            print("NURSE RECORD DELETED SUCCESSFULLY.")

        except mysql.connector.Error as err:
            mysql.rollback()
            print("Database error:", err)

    else:
        print("Deletion cancelled.")

# OTHER WORKER REGISTRATION

def register_worker():
    print("\n===== STAFF REGISTRATION =====")

    wuid = "W" + secrets.token_hex(4).upper()

    name = input("Enter staff name: ")
    age = input("Enter staff age: ")
    address = input("Enter address: ")
    contact = input("Enter contact number: ")
    monthly_salary = input("Enter monthly salary: ")

    try:
        age = int(age)
        monthly_salary = int(monthly_salary)

        if age <= 0 or monthly_salary < 0:
            print("Invalid input values.")
            return

        mycursor.execute("""
            INSERT INTO other_workers_details
            (wuid, name, age, address, contact, monthly_salary)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (wuid, name, age, address, contact, monthly_salary))

        mysql.commit()

        print("\nSTAFF REGISTERED SUCCESSFULLY!")
        print("Staff ID:", wuid)

    except ValueError:
        print("Age and salary must be valid numbers.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# VIEW OTHER WORKER RECORD

def view_worker():
    print("\n===== SEARCH STAFF =====")

    wuid = input("Enter Staff ID: ").strip().upper()

    mycursor.execute("""
        SELECT wuid, name, age, address, contact, monthly_salary
        FROM other_workers_details
        WHERE wuid = %s
    """, (wuid,))

    worker = mycursor.fetchone()

    if worker:
        print("\n===== STAFF DETAILS =====")
        print("Staff ID:", worker[0])
        print("Name:", worker[1])
        print("Age:", worker[2])
        print("Address:", worker[3])
        print("Contact:", worker[4])
        print("Monthly Salary:", worker[5])
    else:
        print("Staff member not found.")

# UPDATE OTHER WORKER DETAILS

def update_worker():
    print("\n===== UPDATE STAFF DETAILS =====")

    wuid = input("Enter Staff ID: ").strip().upper()

    mycursor.execute("""
        SELECT name, age, address, contact, monthly_salary
        FROM other_workers_details
        WHERE wuid = %s
    """, (wuid,))

    worker = mycursor.fetchone()

    if not worker:
        print("Staff member not found.")
        return

    print("\nLeave a field blank to retain its existing value.")

    name = input(f"Name [{worker[0]}]: ") or worker[0]
    age = input(f"Age [{worker[1]}]: ") or worker[1]
    address = input(f"Address [{worker[2]}]: ") or worker[2]
    contact = input(f"Contact [{worker[3]}]: ") or worker[3]
    monthly_salary = input(
        f"Monthly Salary [{worker[4]}]: "
    ) or worker[4]

    try:
        age = int(age)
        monthly_salary = int(monthly_salary)

        if age <= 0 or monthly_salary < 0:
            print("Invalid values.")
            return

        mycursor.execute("""
            UPDATE other_workers_details
            SET name = %s,
                age = %s,
                address = %s,
                contact = %s,
                monthly_salary = %s
            WHERE wuid = %s
        """, (
            name, age, address, contact, monthly_salary, wuid
        ))

        mysql.commit()
        print("\nSTAFF DETAILS UPDATED SUCCESSFULLY!")

    except ValueError:
        print("Age and salary must be valid numbers.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# DELETE OTHER WORKER RECORD

def delete_worker():
    print("\n===== DELETE STAFF RECORD =====")

    wuid = input("Enter Staff ID: ").strip().upper()

    mycursor.execute("""
        SELECT name
        FROM other_workers_details
        WHERE wuid = %s
    """, (wuid,))

    worker = mycursor.fetchone()

    if not worker:
        print("Staff record not found.")
        return

    print("Staff Name:", worker[0])

    confirm = input(
        "Are you sure you want to delete this record? (YES/NO): "
    ).strip().upper()

    if confirm == "YES":
        try:
            mycursor.execute("""
                DELETE FROM other_workers_details
                WHERE wuid = %s
            """, (wuid,))

            mysql.commit()
            print("STAFF RECORD DELETED SUCCESSFULLY.")

        except mysql.connector.Error as err:
            mysql.rollback()
            print("Database error:", err)

    else:
        print("Deletion cancelled.")

# MEDICINE INVENTORY MANAGEMENT

# ADD MEDICINE

def add_medicine():
    print("\n===== ADD MEDICINE =====")

    medicine_name = input("Enter medicine name: ").strip().upper()
    stock = input("Enter stock quantity: ")

    if not medicine_name:
        print("Medicine name cannot be empty.")
        return

    try:
        stock = int(stock)

        if stock < 0:
            print("Stock cannot be negative.")
            return

        mycursor.execute("""
            INSERT INTO inventory (medicine_name, stock)
            VALUES (%s, %s)
        """, (medicine_name, stock))

        mysql.commit()
        print("MEDICINE ADDED SUCCESSFULLY!")

    except ValueError:
        print("Stock must be a valid number.")

    except mysql.connector.IntegrityError:
        mysql.rollback()
        print("Medicine already exists in inventory.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# VIEW INVENTORY

def view_inventory():
    print("\n===== MEDICINE INVENTORY =====")

    mycursor.execute("""
        SELECT medicine_name, stock
        FROM inventory
        ORDER BY medicine_name
    """)

    medicines = mycursor.fetchall()

    if not medicines:
        print("Inventory is empty.")
        return

    print("-" * 40)
    print(f"{'MEDICINE':<25}{'STOCK':>10}")
    print("-" * 40)

    for medicine in medicines:
        print(f"{medicine[0]:<25}{medicine[1]:>10}")

    print("-" * 40)

# UPDATE MEDICINE STOCK

def update_stock():
    print("\n===== UPDATE MEDICINE STOCK =====")

    medicine_name = input(
        "Enter medicine name: "
    ).strip().upper()

    mycursor.execute("""
        SELECT stock
        FROM inventory
        WHERE medicine_name = %s
    """, (medicine_name,))

    medicine = mycursor.fetchone()

    if not medicine:
        print("Medicine not found.")
        return

    print("Current stock:", medicine[0])

    new_stock = input("Enter new stock quantity: ")

    try:
        new_stock = int(new_stock)

        if new_stock < 0:
            print("Stock cannot be negative.")
            return

        mycursor.execute("""
            UPDATE inventory
            SET stock = %s
            WHERE medicine_name = %s
        """, (new_stock, medicine_name))

        mysql.commit()
        print("STOCK UPDATED SUCCESSFULLY!")

    except ValueError:
        print("Stock must be a valid number.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)


def delete_medicine():
    print("\n===== DELETE MEDICINE =====")

    medicine_name = input(
        "Enter medicine name: "
    ).strip().upper()

    mycursor.execute("""
        SELECT stock
        FROM inventory
        WHERE medicine_name = %s
    """, (medicine_name,))

    medicine = mycursor.fetchone()

    if not medicine:
        print("Medicine not found.")
        return

    print("Current stock:", medicine[0])

    confirm = input(
        "Delete this medicine from inventory? (YES/NO): "
    ).strip().upper()

    if confirm == "YES":
        try:
            mycursor.execute("""
                DELETE FROM inventory
                WHERE medicine_name = %s
            """, (medicine_name,))

            mysql.commit()
            print("MEDICINE DELETED SUCCESSFULLY.")

        except mysql.connector.Error as err:
            mysql.rollback()
            print("Database error:", err)

    else:
        print("Deletion cancelled.")

# PATIENT DASHBOARD FUNCTIONS

# PATIENT PROFILE REGISTRATION

def patient_register_profile(username):
    print("\n===== PATIENT PROFILE REGISTRATION =====")

    mycursor.execute("""
        SELECT puid
        FROM patient_details
        WHERE username = %s
    """, (username,))

    if mycursor.fetchone():
        print("You already have a registered patient profile.")
        return

    puid = "P" + secrets.token_hex(4).upper()

    name = input("Enter your name: ").strip()
    age = input("Enter your age: ")
    address = input("Enter address: ").strip()
    contact = input("Enter contact number: ").strip()

    if not name or not address or not contact:
        print("All fields must be completed.")
        return

    try:
        age = int(age)

        if age <= 0:
            print("Invalid age.")
            return

        mycursor.execute("""
            INSERT INTO patient_details
            (puid, name, age, address, contact, date_of_visit,
             doctor_prescribed, medicine_prescribed, qty, username)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            puid, name, age, address, contact,
            datetime.date.today(), "", "", 0, username
        ))

        mysql.commit()

        print("\nPROFILE REGISTERED SUCCESSFULLY!")
        print("Your Patient ID:", puid)

    except ValueError:
        print("Age must be a valid number.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# VIEW PATIENT PROFILE

def patient_view_profile(username):
    print("\n===== MY PATIENT PROFILE =====")

    mycursor.execute("""
        SELECT puid, name, age, address, contact, date_of_visit,
               doctor_prescribed, medicine_prescribed, qty
        FROM patient_details
        WHERE username = %s
    """, (username,))

    patient = mycursor.fetchone()

    if not patient:
        print("No patient profile found. Please register first.")
        return

    print("\nPatient ID:", patient[0])
    print("Name:", patient[1])
    print("Age:", patient[2])
    print("Address:", patient[3])
    print("Contact:", patient[4])
    print("Date of Registration/Visit:", patient[5])
    print("Doctor Prescribed:", patient[6] or "Not assigned")
    print("Medicine Prescribed:", patient[7] or "Not assigned")
    print("Quantity:", patient[8])

# UPDATE PATIENT PROFILE

def patient_update_profile(username):
    print("\n===== UPDATE MY PROFILE =====")

    mycursor.execute("""
        SELECT name, age, address, contact
        FROM patient_details
        WHERE username = %s
    """, (username,))

    patient = mycursor.fetchone()

    if not patient:
        print("No patient profile found. Please register first.")
        return

    print("Leave any field blank to keep the current value.")

    name = input(f"Name [{patient[0]}]: ").strip() or patient[0]
    age = input(f"Age [{patient[1]}]: ").strip() or patient[1]
    address = input(f"Address [{patient[2]}]: ").strip() or patient[2]
    contact = input(f"Contact [{patient[3]}]: ").strip() or patient[3]

    try:
        age = int(age)

        if age <= 0:
            print("Age must be greater than zero.")
            return

        mycursor.execute("""
            UPDATE patient_details
            SET name = %s,
                age = %s,
                address = %s,
                contact = %s
            WHERE username = %s
        """, (name, age, address, contact, username))

        mysql.commit()
        print("PROFILE UPDATED SUCCESSFULLY!")

    except ValueError:
        print("Age must be a valid number.")

    except mysql.connector.Error as err:
        mysql.rollback()
        print("Database error:", err)

# PATIENT DASHBOARD

def patient_menu(username):
    while True:
        print(f"""
================================
       PATIENT DASHBOARD
================================
Logged in as: {username}

1. Register Patient Profile
2. View My Profile
3. Update My Profile
4. Logout
""")

        choice = input("ENTER YOUR CHOICE: ").strip()

        if choice == "1":
            patient_register_profile(username)

        elif choice == "2":
            patient_view_profile(username)

        elif choice == "3":
            patient_update_profile(username)

        elif choice == "4":
            print("Logging out...")
            break

        else:
            print("Invalid choice.")

# EMPLOYEE DASHBOARD

def employee_menu(username):
    while True:
        print(f"""
================================
      EMPLOYEE DASHBOARD
================================
Logged in as: {username}

--- PATIENT MANAGEMENT ---
1. Register Patient
2. View Patient Record
3. Update Patient Details
4. Delete Patient Record

--- DOCTOR MANAGEMENT ---
5. Register Doctor
6. View Doctor
7. Update Doctor
8. Delete Doctor

--- NURSE MANAGEMENT ---
9. Register Nurse
10. View Nurse
11. Update Nurse
12. Delete Nurse

--- OTHER STAFF MANAGEMENT ---
13. Register Other Staff
14. View Other Staff
15. Update Other Staff
16. Delete Other Staff

--- INVENTORY MANAGEMENT ---
17. Add Medicine
18. View Inventory
19. Update Stock
20. Delete Medicine

21. Logout
""")

        choice = input("ENTER YOUR CHOICE: ")

        if choice == "1":
            register_patient()
        elif choice == "2":
            view_patient()
        elif choice == "3":
            update_patient()
        elif choice == "4":
            delete_patient()

        elif choice == "5":
            register_doctor()
        elif choice == "6":
            view_doctor()
        elif choice == "7":
            update_doctor()
        elif choice == "8":
            delete_doctor()

        elif choice == "9":
            register_nurse()
        elif choice == "10":
            view_nurse()
        elif choice == "11":
            update_nurse()
        elif choice == "12":
            delete_nurse()

        elif choice == "13":
            register_worker()
        elif choice == "14":
            view_worker()
        elif choice == "15":
            update_worker()
        elif choice == "16":
            delete_worker()

        elif choice == "17":
            add_medicine()
        elif choice == "18":
            view_inventory()
        elif choice == "19":
            update_stock()
        elif choice == "20":
            delete_medicine()

        elif choice == "21":
            print("Logging out...")
            break

        else:
            print("Invalid choice.")

# MAIN MENU

while True:
    print("""
================================
      HOSPITAL MAIN MENU
================================
1. PATIENT
2. EMPLOYEE
3. EXIT
""")

    choice = input("ENTER YOUR CHOICE: ")

    if choice == "1":
        account_menu("PATIENT")

    elif choice == "2":
        account_menu("EMPLOYEE")

    elif choice == "3":
        print("Thank you for visiting!")
        break

    else:
        print("Invalid choice. Try again.")
