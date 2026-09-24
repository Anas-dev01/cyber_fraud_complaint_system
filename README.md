# CyberGuard Fraud Complaint and Tracking System

CyberGuard is a Django application for submitting fraud complaints, uploading evidence, tracking case status, and investigator review.

It provides separate victim and investigator workflows, unique case tracking IDs, encrypted victim phone numbers, and SHA-256 integrity checks for uploaded evidence.

This guide covers a complete Windows installation.

## Requirements

- Windows 10 or Windows 11
- Internet access and permission to install software
- Python 3.12 or newer
- Git (optional, for cloning)

## 1. Install Python

1. Visit [python.org/downloads/windows](https://www.python.org/downloads/windows/).
2. Download a stable Python 3.12-or-newer Windows installer.
3. Run it, select **Add python.exe to PATH**, and choose **Install Now**.
4. Reopen PowerShell and verify:

```powershell
python --version
python -m pip --version
```

If `python` opens the Microsoft Store, go to **Settings > Apps > Advanced app settings > App execution aliases** and turn off the App Installer aliases for `python.exe` and `python3.exe`.

## 2. Get the project

### Clone with Git

Install Git for Windows from [git-scm.com/download/win](https://git-scm.com/download/win), then run:

```powershell
cd "$env:USERPROFILE\Desktop"
git clone <REPOSITORY_URL> cyberguard_project
cd cyberguard_project
```

Replace `<REPOSITORY_URL>` with the project repository URL.

### Download a ZIP

Download and extract the ZIP to a location such as `C:\Users\YourName\Desktop\cyberguard_project`. Open the extracted folder, click its address bar, type `powershell`, and press Enter.

Confirm the project files are present:

```powershell
Get-ChildItem
```

You should see `manage.py` and `requirements.txt`.

## 3. Create and activate a virtual environment

From the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

The prompt should begin with `(.venv)`. If PowerShell blocks activation, run this once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Answer `Y`, reopen PowerShell, and activate again. In Command Prompt use `.venv\Scripts\activate.bat`.

## 4. Install dependencies

With `(.venv)` active:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m django --version
```

## 5. Configure email and evidence storage

The application sends registration and case-status emails through Gmail SMTP. Before running it, open `core\settings.py` and replace the email values with your own:

```python
EMAIL_HOST_USER = "your-email@gmail.com"
EMAIL_HOST_PASSWORD = "your-16-character-Gmail-app-password"
```

Use a Gmail **App Password**, not your normal Gmail password. For local testing without sending real email, temporarily set:

```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

Emails will then appear in the PowerShell window running Django.

> **Security warning:** Do not commit real passwords, API keys, or production secret keys. This project currently has sensitive-looking configuration values in `core\settings.py`; treat them as exposed, revoke or rotate them, and replace them before sharing the project. For deployment, load all secrets from environment variables and generate a new Django `SECRET_KEY`.

Uploaded evidence is stored by default in:

```text
C:\Users\YourName\Desktop\evidence_files
```

Create the folder if needed:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\Desktop\evidence_files"
```

## 6. Prepare the database

The project uses SQLite. The database file (`db.sqlite3`) is created locally when migrations run and is intentionally ignored by Git. Apply migrations:

```powershell
python manage.py migrate
```

To start with a new empty database, stop the server and rename or remove `db.sqlite3` before migrating. Do not do this if you need its existing data.

## 7. Create an investigator/admin account

```powershell
python manage.py createsuperuser
```

Enter a username, email, and strong password. This staff account can access the investigator dashboard and `/admin/`.

## 8. Check and test

```powershell
python manage.py check
python manage.py test
```

## 9. Start the website

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Keep PowerShell open while using the site; press `Ctrl+C` to stop it.

Useful pages:

| Page | Address |
| --- | --- |
| Home | `http://127.0.0.1:8000/` |
| Register | `http://127.0.0.1:8000/register/` |
| Login | `http://127.0.0.1:8000/login/` |
| Django admin | `http://127.0.0.1:8000/admin/` |
| Investigator login | `http://127.0.0.1:8000/investigator/login/` |

## 10. Victim workflow

1. Register at `/register/`.
2. Log in and submit a fraud complaint.
3. Upload evidence if available.
4. Save the generated tracking ID.
5. Use the dashboard or `/track/` page to check status.

## 11. Investigator workflow

1. Open `/investigator/login/`.
2. Sign in with the `createsuperuser` account.
3. Review complaints and evidence.
4. Update statuses and investigator remarks.

## 12. Start the project later

```powershell
cd "C:\path\to\cyberguard_project"
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

If `.venv` is missing, recreate it and reinstall with `python -m venv .venv`, `.\.venv\Scripts\Activate.ps1`, and `python -m pip install -r requirements.txt`.

## Troubleshooting

**Python not recognized:** reinstall Python with **Add python.exe to PATH**, or use `py --version` and `py -m venv .venv`.

**Django not found:** activate `.venv` and run `python -m pip install -r requirements.txt`.

**Port 8000 is busy:** run `python manage.py runserver 8001` and open `http://127.0.0.1:8001/`.

**Migration errors:** first run `python manage.py migrate`. Only run `python manage.py makemigrations` after you intentionally change a model, then run `python manage.py migrate`. Do not delete a database containing required data.

**Email errors:** check `core\settings.py`, or use the console email backend for local development.

**Missing evidence:** check that `C:\Users\YourName\Desktop\evidence_files` exists and is writable.

## Security and deployment note

This is a local-development setup using `DEBUG = True`, SQLite, development security settings, and Django’s development server. Do not expose it directly to the public internet. Production requires environment variables for secrets, HTTPS, a production WSGI/ASGI server, a production database, restricted hosts, secure cookies, and reviewed email settings.

## Deactivate the environment

```powershell
deactivate
```
