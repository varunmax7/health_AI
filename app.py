from flask import Flask, render_template, request, redirect, url_for, session, flash
import datetime, json, os
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# User database file
USER_DB = "users.json"
SYMPTOM_DB = {
    "fever": ("Take rest, stay hydrated, use paracetamol.", "Viral Infection or Flu", "General Physician"),
    "sore throat": ("Gargle with warm salt water, drink warm fluids.", "Throat Infection or Common Cold", "ENT Specialist"),
    "cough": ("Use cough syrup, inhale steam.", "Respiratory Infection", "Pulmonologist"),
    "headache": ("Rest in a quiet room, take painkillers if needed.", "Migraine or Tension Headache", "Neurologist"),
    "fatigue": ("Ensure good sleep, balanced diet, and hydration.", "Chronic Fatigue or Anemia", "General Physician"),
    "cold": ("Stay warm, drink fluids, use nasal decongestants.", "Common Cold", "General Physician"),
    "body aches": ("Use pain relievers, stay warm, rest.", "Flu or Viral Infection", "General Physician"),
    "runny nose": ("Use a saline nasal spray, stay hydrated.", "Allergic Rhinitis or Cold", "ENT Specialist"),
    "chills": ("Wear warm clothing, take warm liquids.", "Infection or Flu", "General Physician"),
    "nausea": ("Sip ginger tea or take anti-nausea medicine.", "Gastric Issue", "Gastroenterologist"),
    "vomiting": ("Stay hydrated, take antiemetic medication if needed.", "Food Poisoning or Stomach Flu", "Gastroenterologist"),
    "diarrhea": ("Stay hydrated, avoid dairy and high-fat foods.", "Gastrointestinal Infection", "Gastroenterologist"),
    "constipation": ("Eat fiber-rich foods, drink plenty of water.", "Digestive Problems", "Gastroenterologist"),
    "dizziness": ("Rest, stay hydrated, avoid sudden movements.", "Low Blood Pressure or Vertigo", "Neurologist"),
    "shortness of breath": ("Seek medical attention if severe; try slow, deep breathing.", "Asthma or Heart Issue", "Pulmonologist / Cardiologist"),
    "chest pain": ("Seek immediate medical attention, especially if it persists.", "Heart Problem", "Cardiologist"),
    "joint pain": ("Use pain relievers, rest, apply ice to reduce swelling.", "Arthritis", "Orthopedic Specialist"),
    "swelling": ("Apply ice or a cold compress, elevate the swollen area.", "Injury or Infection", "General Physician"),
    "rash": ("Avoid scratching, use anti-itch creams, stay cool.", "Skin Allergy", "Dermatologist"),
    "itchy skin": ("Use anti-itch creams or moisturizers.", "Dermatitis", "Dermatologist"),
    "abdominal pain": ("Rest, avoid heavy meals, use heat pads.", "Gastric Issue or Appendicitis", "Gastroenterologist"),
    "leg cramps": ("Stretch the muscle gently, stay hydrated.", "Muscle Fatigue", "Orthopedic Specialist"),
    "back pain": ("Rest, apply heat or cold compress, take pain relievers.", "Muscle Strain", "Orthopedic Specialist"),
    "numbness": ("Avoid pressure on affected area, rest.", "Nerve Compression", "Neurologist"),
    "blurry vision": ("Rest your eyes, take breaks, and consult a doctor if it persists.", "Eye Strain or Vision Problem", "Ophthalmologist"),
    "ringing in ears": ("Avoid loud environments, try relaxation techniques.", "Tinnitus", "ENT Specialist"),
    "insomnia": ("Try a sleep routine, limit caffeine, avoid screen time before bed.", "Sleep Disorder", "Psychiatrist / Sleep Specialist"),
    "dry mouth": ("Stay hydrated, use mouthwash, chew sugar-free gum.", "Dehydration or Diabetes", "General Physician"),
    "canker sores": ("Use soothing mouth rinses, avoid acidic foods.", "Mouth Ulcers", "Dentist"),
    "bloody nose": ("Pinch nostrils and lean forward, apply a cold compress.", "Nasal Irritation", "ENT Specialist"),
    "nosebleeds": ("Pinch nostrils, stay calm, and apply a cold compress.", "Nasal Dryness or Trauma", "ENT Specialist"),
    "pale skin": ("Ensure proper hydration and nutrition, avoid extreme heat.", "Anemia", "General Physician"),
    "weight loss": ("Consult a doctor, eat balanced meals, stay hydrated.", "Malnutrition or Thyroid Disorder", "Endocrinologist"),
    "weight gain": ("Monitor diet, engage in physical activity, stay hydrated.", "Obesity or Thyroid Problem", "Endocrinologist"),
    "anxiety": ("Practice relaxation techniques, deep breathing, or meditation.", "Anxiety Disorder", "Psychiatrist"),
    "depression": ("Seek professional help, maintain a routine, stay active.", "Depression", "Psychiatrist"),
    "food poisoning": ("Stay hydrated, avoid solid foods for a few hours.", "Bacterial or Viral Infection", "Gastroenterologist"),
    "stomachache": ("Rest, drink warm water, avoid heavy food.", "Gastritis or Infection", "Gastroenterologist"),
    "period cramps": ("Use heat pads, take pain relievers, avoid caffeine.", "Menstrual Pain", "Gynecologist")
}

def load_users():
    if os.path.exists(USER_DB) and os.path.getsize(USER_DB) > 0:
        try:
            with open(USER_DB, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_user(username, password):
    users = load_users()
    if username in users:
        return False  # User already exists

    users[username] = {
        "password": generate_password_hash(password),
        "created_at": str(datetime.datetime.now())
    }

    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)
    return True

def save_log(symptoms, username="guest"):
    with open("symptoms.txt", "a") as file:
        file.write(f"{datetime.datetime.now()} - {username}: {symptoms}\n")

    # Load existing data or create new dict
    if os.path.exists("user_data.json") and os.path.getsize("user_data.json") > 0:
        try:
            with open("user_data.json", "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    # Initialize user's data if not exists
    if username not in data:
        data[username] = []

    # Add new symptom log
    data[username].append({"date": str(datetime.date.today()), "symptoms": symptoms})

    # Save back to file
    with open("user_data.json", "w") as f:
        json.dump(data, f, indent=4)

def get_user_trends(username="guest"):
    trends = {}
    if not os.path.exists("user_data.json") or os.path.getsize("user_data.json") == 0:
        return trends

    try:
        with open("user_data.json", "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return trends

    if username not in data:
        return trends

    for log in data[username]:
        for s in log["symptoms"].split(","):
            s = s.strip().lower()
            trends[s] = trends.get(s, 0) + 1

    return trends

def delete_symptom_from_data(username, symptom_to_delete):
    if not os.path.exists("user_data.json"):
        return False

    try:
        with open("user_data.json", "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return False

    if username not in data:
        return False

    # Filter out the symptom from all logs
    updated = False
    for log in data[username]:
        symptoms = [s.strip().lower() for s in log["symptoms"].split(",")]
        if symptom_to_delete in symptoms:
            symptoms = [s for s in symptoms if s != symptom_to_delete]
            log["symptoms"] = ", ".join(symptoms)
            updated = True

    if updated:
        with open("user_data.json", "w") as f:
            json.dump(data, f, indent=4)
        return True

    return False

@app.route("/", methods=["GET", "POST"])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    output = {}
    if request.method == "POST":
        symptoms = request.form.get("symptoms")
        save_log_option = request.form.get("save_log")
        username = session['username']

        if not symptoms or not symptoms.strip():
            return render_template("index.html", error="❌ Please enter valid symptoms.")

        symptoms_cleaned = symptoms.lower()
        symptoms_cleaned = re.sub(r"\b(i have|i am|i'm|having|experiencing|suffering from|feeling|a|and)\b", '', symptoms_cleaned)
        symptoms_cleaned = re.sub(r'[^\w\s]', '', symptoms_cleaned)
        symptoms_cleaned = symptoms_cleaned.strip()

        matched = []
        for key_symptom in SYMPTOM_DB.keys():
            if re.search(r'\b' + re.escape(key_symptom) + r'\b', symptoms_cleaned):
                matched.append((key_symptom, SYMPTOM_DB[key_symptom]))

        if matched:
            output["issue"] = "🧠 Possible Issues: " + ", ".join([m[1][1] for m in matched])
            output["suggestions"] = matched
            output["advice"] = "💡 Advice: If symptoms last more than 3 days, please consult a doctor."

            if save_log_option and save_log_option.lower() == "yes":
                save_log(symptoms, username)
                output["log"] = "📥 Log saved successfully."
        else:
            output["issue"] = "⚠️ Unknown symptoms. Please consult a doctor."
            output["advice"] = "Try entering common symptoms like fever, cough, etc."

    return render_template("index.html", output=output, username=session.get('username'))

@app.route("/history")
def history():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    trends = get_user_trends(username)
    session['trends'] = trends
    return render_template("history.html", trends=trends, username=username)

@app.route('/delete_symptom/<symptom>', methods=['POST'])
def delete_symptom(symptom):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Delete from persistent storage
    delete_symptom_from_data(username, symptom)

    # Update session trends
    trends = session.get('trends', {})
    if symptom in trends:
        del trends[symptom]
        session['trends'] = trends

    return redirect(url_for('history'))

@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Clear symptoms.txt
    with open("symptoms.txt", "w") as file:
        file.truncate(0)

    # Clear user_data.json for this user only
    if os.path.exists("user_data.json") and os.path.getsize("user_data.json") > 0:
        try:
            with open("user_data.json", "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    if username in data:
        data[username] = []

        with open("user_data.json", "w") as f:
            json.dump(data, f, indent=4)

    # Clear session trends
    if 'trends' in session:
        del session['trends']

    return redirect(url_for("index"))

@app.route("/research")
def research():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("research.html", username=session.get('username'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()

        if username in users and check_password_hash(users[username]["password"], password):
            session['username'] = username
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not username or not password:
            flash("Username and password are required", "danger")
        elif password != confirm_password:
            flash("Passwords do not match", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters", "danger")
        else:
            if save_user(username, password):
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("login"))
            else:
                flash("Username already exists", "danger")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
