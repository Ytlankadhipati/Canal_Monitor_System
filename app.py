from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_dance.contrib.google import make_google_blueprint, google
from flask_mail import Mail, Message
import sqlite3
import os
from flask import render_template_string 

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# === Google OAuth ===
blueprint = make_google_blueprint(
    client_id="1035578749063-318ndmh9um2h1932arjpheonnjbltm25.apps.googleusercontent.com",
    client_secret="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",
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email"]
)
app.register_blueprint(blueprint, url_prefix="/login")

# === File upload route (optional use) ===
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config.get('UPLOAD_FOLDER', ''), filename)

# === Email Configuration (Flask-Mail) ===
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'rishuawasthi1020@gmail.com'
app.config['MAIL_PASSWORD'] = 'vrsz ttrt fukt rvia'
app.config['MAIL_DEFAULT_SENDER'] = 'rishuawasthi1020@gmail.com'

mail = Mail(app)

DB_FILE = 'community.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS community_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            alert_method TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('signup.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    address = request.form['address']
    phone = request.form['phone']
    email = request.form['email']
    alert_method = request.form['alert_method']

    if not name or not phone or not email or not alert_method:
        flash("All required fields must be filled!", "error")
        return redirect(url_for('index'))

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO community_members (name, address, phone, email, alert_method)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, address, phone, email, alert_method))
    conn.commit()
    conn.close()

    flash("Registration successful!", "success")
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info", 500

    email = resp.json().get("email", "").strip().lower()
    if email != "ayushawasthi5363@gmail.com":  # ✅ Your Ayush admin email
        return "Access denied", 403

    conn = get_db_connection()
    users = conn.execute("SELECT * FROM community_members").fetchall()
    conn.close()

    return render_template("admin.html", users=users)

@app.route('/trigger-alert', methods=['POST'])
def trigger_alert():
    data = request.get_json()
    water_level = data.get("water_level", 0)

    if water_level >= 80:
        send_email_alerts(water_level)
        return jsonify({"status": "Alert sent"}), 200
    else:
        return jsonify({"status": "Water level normal"}), 200

@app.route('/send-alert-now')
def send_alert_now():
    send_email_alerts(95)
    return "Alert sent to all registered emails."

def send_email_alerts(water_level):
    conn = get_db_connection()
    members = conn.execute("SELECT email FROM community_members").fetchall()
    conn.close()
    print(members)

    subject = "⚠️ Canal Water Level Alert"

    html_template = """
    <html>
    <head>
      <style>
        body {
          font-family: Arial, sans-serif;
          background-color: #f4f4f7;
          margin: 0;
          padding: 0;
        }
        .email-container {
          max-width: 600px;
          margin: 40px auto;
          background: #ffffff;
          padding: 30px;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        h2 {
          color: #d9534f;
        }
        p {
          font-size: 16px;
          color: #333333;
        }
        .cta-button {
          display: inline-block;
          margin-top: 20px;
          padding: 12px 20px;
          background-color: #007bff;
          color: white;
          text-decoration: none;
          border-radius: 5px;
          font-weight: bold;
        }
        footer {
          text-align: center;
          font-size: 13px;
          color: #888888;
          margin-top: 30px;
        }
      </style>
    </head>
    <body>
      <div class="email-container">
        <h2>⚠️ Water Level Alert</h2>
        <p>Dear Resident,</p>
        <p>The canal water level has risen to <strong>{{ water_level }}%</strong>.</p>
        <p>Please take necessary precautions and stay safe.</p>
        <a href="http://your-website.com" class="cta-button">View Status</a>
        <footer>
          You are receiving this alert as part of the Canal Monitoring Program.
        </footer>
      </div>
    </body>
    </html>
    """

    # Render HTML with the actual water level value
    rendered_html = render_template_string(html_template, water_level=water_level)

    for member in members:
        try:
            msg = Message(subject, recipients=[member['email']])
            msg.body = f"Water level alert: {water_level}%"  # fallback plain text
            msg.html = rendered_html
            print(msg)
            mail.send(msg)
            print(f"[✓] Alert sent to {member['email']}")
        except Exception as e:
            print(f"[x] Failed to send to {member['email']}: {e}")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)





