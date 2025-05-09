## Animating Facial Expressions with AI Mood Detection ==> Integrated with Roundcube WebMail
This project integrates facial mood detection with email composition using [Roundcube Webmail](https://roundcube.net/). It allows users to capture their current facial expression, analyze their mood using AI, and generate an animated facial GIF that can be embedded directly into an email message.

The backend is powered by a **Flask API** using **OpenCV** and **py-feat** for facial recognition and emotion detection. The frontend is built into Roundcube as a custom plugin that communicates with the backend.


**Features**
- Detects facial expressions using your device’s camera.
- Analyses emotions with Action Unit (AU) extraction using `py-feat`.
- Generates animated facial expression GIFs.
- Injects GIFs directly into the Roundcube email composer.
- Sends emails via Gmail IMAP/SMTP using app passwords.

**Technology used**
- **Roundcube Webmail** (Frontend Email UI)
- **Python** (Backend Logic)
- **Flask** (Backend Web API)
- **OpenCV** (Camera Integration)
- **Py-Feat** (Facial Emotion Analysis)
- **Celluloid + Matplotlib** (GIF Animation)
- **Gmail App Passwords** (Email Integration)


**Installation**

The following steps are to be done in two different terminals.

1. Terminal 1:
It is recommneded to install the requirements for the Python Flask backend server to avoid dependency issues.
`python3 -m venv .venv`
`source .venv/bin/activate  # For Mac/Linux`
`pip install -r requirements.txt`

To run the flask backend server
`python finalProj.py`

2. Terminal 2:
`cd roundcubemail`
`composer install`

Create a database using MySQL:
`CREATE USER 'roundcubeuser'@'localhost' IDENTIFIED BY 'secretpassword';`
`GRANT ALL PRIVILEGES ON roundcube.* TO 'roundcubeuser'@'localhost';`
`FLUSH PRIVILEGES;`

Edit config/config.inc.php and fill in your database settings:
`$config['db_dsnw'] = 'mysql://roundcubeuser:secretpassword@localhost/roundcube';`

Before configuring generate a apps password, configure it for SMTP and IMAP in your gmail/email account and store this,
this along with your email username is what will be used to login into roundcube web email service. 
Edit config/config.inc.php and set up imap/smtp to route to your gmail Account:
`$config['smtp_host'] = 'tls://smtp.gmail.com';`
`$config['imap_host'] = 'ssl://imap.gmail.com';`
`$config['smtp_user'] = '%u';`
`$config['smtp_pass'] = '%p';`
`$config['mail_domain'] = 'gmail.com';`

To run roundcube:
`php -S localhost:8000 -t public_html`

- If you run into any issues with the Yarn installation use `yarn cache clean`then repeat the steps for Terminal 2.

**Troubleshooting**
- To quit either of the running servers use 'CTRL+C'.

