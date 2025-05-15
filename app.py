from flask import Flask, render_template, request, redirect, url_for
import csv, os
from werkzeug.utils import secure_filename
from flask import send_from_directory

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
#app.config['UPLOAD_FOLDER'] = 'uploads'
DATA_FILE = 'applicants.csv'
HEADERS = ['name', 'email', 'phone', 'position', 'resumepath']

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Ensure required files/folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)

def read_applicants():
    with open(DATA_FILE, 'r') as f:
        return list(csv.DictReader(f))

def write_applicants(applicants):
    with open(DATA_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(applicants)

@app.route('/')
def index():
    applicants = read_applicants()
    print("Applicants loaded:", applicants)
    return render_template('index.html', applicants=applicants)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = request.form
        resume = request.files['resume']
        filename = secure_filename(resume.filename)
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume.save(resume_path)

        with open(DATA_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                data['name'],
                data['email'],
                data['phone'],
                data['position'],
                resume_path
            ])
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/delete/<email>')
def delete(email):
    applicants = read_applicants()
    applicants = [a for a in applicants if a['email'] != email]
    write_applicants(applicants)
    return redirect(url_for('index'))

@app.route('/modify/<email>', methods=['GET', 'POST'])
def modify_old(email):
    applicants = read_applicants()
    applicant = next((a for a in applicants if a['email'] == email), None)
    if not applicant:
        return "Applicant not found", 404

    if request.method == 'POST':
        data = request.form
        resume = request.files.get('resume')
        if resume and resume.filename:
            filename = secure_filename(resume.filename)
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume.save(resume_path)
        else:
            resume_path = applicant['resumepath']

        updated = {
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'position': data['position'],
            'resumepath': resume_path
        }

        applicants = [updated if a['email'] == email else a for a in applicants]
        write_applicants(applicants)
        return redirect(url_for('index'))

    return render_template('modify.html', applicant=applicant)

@app.route('/modify/<email>', methods=['GET', 'POST'])
def modify(email):
    applicants = read_applicants()
    applicant = next((a for a in applicants if a['email'] == email), None)
    if not applicant:
        return "Applicant not found", 404

    if request.method == 'POST':
        try:
            data = request.form
            name = data['name'].strip()
            email_new = data['email'].strip()
            phone = data['phone'].strip()
            position = data['position'].strip()

            if not all([name, email_new, phone, position]):
                return "All fields are required", 400

            resume = request.files.get('resume')
            if resume and resume.filename:
                filename = secure_filename(resume.filename)
                resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                resume.save(resume_path)
            else:
                resume_path = applicant['resumepath']

            updated = {
                'name': name,
                'email': email_new,
                'phone': phone,
                'position': position,
                'resumepath': resume_path
            }

            # Safely replace the matching applicant by original email
            for idx, a in enumerate(applicants):
                if a['email'] == email:
                    applicants[idx] = updated
                    break

            write_applicants(applicants)
            return redirect(url_for('index'))

        except Exception as e:
            return f"An error occurred: {e}", 500

    return render_template('modify.html', applicant=applicant)


# Add a print statement to confirm app is running
if __name__ == "__main__":
    print("Starting the Flask application...")
    app.run(host='0.0.0.0', port=5001, debug=True)

