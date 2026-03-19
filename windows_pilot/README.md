# VetCoreSoft Desktop — Pilot Test Guide

## Prerequisites

- **Windows 10/11** with Python 3.10+ installed
  - Download: https://www.python.org/downloads/
  - **Important:** Check "Add Python to PATH" during installation
- **Internet connection** to the LAN server running VetCoreSoft Cloud

---

## Server Setup (Linux machine)

1. Start all services:
   ```bash
   cd vetcoresoft
   docker compose up -d --build
   ```

2. Find your LAN IP:
   ```bash
   hostname -I | awk '{print $1}'
   ```

3. Verify nginx is responding:
   ```bash
   curl -H "Host: api.vetcoresoft.app" http://localhost/health
   curl -H "Host: vetcoresoft.app" http://localhost/download/
   ```

---

## Windows Client Setup

### 1. Configure hosts file

Open **Notepad as Administrator**, then open `C:\Windows\System32\drivers\etc\hosts`.

Add these lines (replace `192.168.1.XX` with the Linux machine's LAN IP):

```
192.168.1.XX    api.vetcoresoft.app
192.168.1.XX    vetcoresoft.app
```

Save and close.

### 2. Verify connectivity

Open Command Prompt:
```
ping api.vetcoresoft.app
```
Should resolve to the Linux machine's IP.

### 3. Download VetCoreSoft

Visit `http://vetcoresoft.app/download/` in your browser and download the ZIP.

Or copy the `windows_pilot/` folder + `backend/` folder to the Windows machine.

### 4. Run VetCoreSoft

Double-click `start_vetcoresoft.bat`. It will:
1. Create a Python virtual environment
2. Install dependencies
3. Run database migrations
4. Start the local server

### 5. Complete Setup

Open `http://localhost:8000` in your browser.

The Setup Wizard will ask for:
- Company name, tax ID, address, phone, email
- Admin username and password

Upon completion, VetCoreSoft will:
- Create a 30-day TRIAL license locally
- Register the trial with the Cloud API at `api.vetcoresoft.app`
- The license will appear in the Admin Portal at `http://vetcoresoft.app/platform/`

---

## What to Test

| Feature | How to test |
|---------|-------------|
| Setup Wizard | Complete first-time setup on Windows |
| Trial Registration | Check Admin Portal → Licenses for the new trial |
| License Check | VetCoreSoft validates against `api.vetcoresoft.app` on startup |
| Offline Mode | Disconnect WiFi → VetCoreSoft keeps working (grace period) |
| Clients & Patients | Create, edit, search |
| Clinical Records | New consultation, medical history |
| Inventory | Add products, stock movements |
| Sales / POS | Create a sale, print receipt |
| Admin Portal | View licenses, grant/revoke from `vetcoresoft.app/platform/` |

---

## Troubleshooting

**"Python is not installed"** → Install Python and ensure "Add to PATH" is checked.

**Cannot connect to api.vetcoresoft.app** → Verify hosts file entry and that Docker is running on the Linux machine.

**License check fails** → Check that `vetcoresoft.ini` has the correct `api_url` and that the `api_secret` matches the server.

**Port 8000 already in use** → Another app is using the port. Stop it or edit `start_vetcoresoft.bat` to use a different port.
