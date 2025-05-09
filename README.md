## Animating Facial Expressions with AI Mood Detection ==> Integrated with Roundcube WebMail
This project integrates facial mood detection with email composition using [Roundcube Webmail](https://roundcube.net/). It allows users to capture their current facial expression, analyse their mood using AI, and generate an animated facial GIF that can be embedded directly into an email message.

The backend is powered by a **Flask API** using **OpenCV** and **Py-Feat** for facial recognition and emotion detection. The frontend is built into Roundcube as a custom plugin that communicates with the backend.


**Features**
- Detects facial expressions using your device’s camera.
- Ues ResMaskNet model for expression detection and MobileFaceNet for landmark extraction through `Py-Feat`.
- Generates animated facial expression GIFs.
- Allows direct download of GIF from interface to be used as an email attachment on Roundcube.
- Sends emails via Gmail IMAP/SMTP using app passwords.

**Technology used**
- **Roundcube Webmail** (Frontend Email UI)
- **Python** (Backend Logic)
- **Flask** (Backend Web API)
- **OpenCV** (Camera Integration)
- **ResMaskNet** (Facial Emotion Analysis)
- **Delaunay + Affine warping and transformation** (GIF Creation)
- **Gmail App Passwords** (Email Integration)


**Running the application**

The following steps are to be done in two different terminals.

1. Terminal 1:
It is recommneded to install the requirements for the Python Flask backend server to avoid dependency issues.
`python3 -m venv .venv`
`source .venv/bin/activate  # For Mac/Linux`
`pip install -r requirements.txt`

To run the flask backend server
`python finalProj.py`

- Add the generated 'cert.pem' file to your device's trusted certifcates through system setting or your web browser, make sure to grant "Always trust" on all levels. 
This will allow the application to use HTTPS.


2. Terminal 2:
`cd roundcubemail`
`composer install`

To configure Roundcube, follow the installer instruction when you open on localhost or refer to: "https://github.com/roundcube/roundcubemail/blob/master/INSTALL" and "https://github.com/roundcube/roundcubemail/blob/master/README.md"

Create a database using MySQL:
`CREATE USER 'roundcubeuser'@'localhost' IDENTIFIED BY 'secretpassword';`
`GRANT ALL PRIVILEGES ON roundcube.* TO 'roundcubeuser'@'localhost';`
`FLUSH PRIVILEGES;`

Edit config/config.inc.php and fill in your database settings:
`$config['db_dsnw'] = 'mysql://roundcubeuser:secretpassword@localhost/roundcube';`

Before configuring generate a App password, configure it for SMTP and IMAP in your gmail/email account and store this,
this along with your email username is what will be used to login into roundcube web email service. 
Edit config/config.inc.php and set up imap/smtp to route to your gmail Account:
`$config['smtp_host'] = 'tls://smtp.gmail.com';`
`$config['imap_host'] = 'ssl://imap.gmail.com';`
`$config['smtp_user'] = '%u';`
`$config['smtp_pass'] = '%p';`
`$config['mail_domain'] = 'gmail.com';`

Also add these for console log info. on errors:
`$config['debug_level'] = 1;`
`$config['smtp_debug'] = true;`
 
Update or add "mood_plugin" to the list of plugins:
`$config['plugins'] = array('mood_plugin');`

To run roundcube:
`php -S localhost:8000 -t public_html`


**Troubleshooting**
- To quit either of the running servers use 'CTRL+C'.
- The application has been constructed to log any issues on the console, refer to this for debugging.
