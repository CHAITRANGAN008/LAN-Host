# 🚀 LAN Host

### Host files. Share locally. No cables required.

LAN Host is a Windows desktop application that allows you to host and share files and folders over your local Wi-Fi network.

Simply select a file or folder, start the HTTP server, and share the generated URL with another device connected to the same network.

**Built with Python and PySide6.**

---

## ✨ Features

- 🖥️ **Windows Desktop Application** – Modern dark-themed graphical interface.
- 📁 **Folder Sharing** – Select and host an entire folder.
- 📄 **File Selection** – Select an individual file; its parent directory is used as the hosting root.
- 📡 **Automatic Wi-Fi Detection** – Detect the active Wi-Fi adapter and IPv4 address.
- 🔗 **Shareable URL** – Automatically generates a local network sharing link.
- 📋 **Copy URL** – Copy the sharing link with one click.
- ⚡ **Start / Stop Server** – Easily control the HTTP server.
- 🔌 **Custom Port** – Configure your preferred HTTP server port.
- 🔄 **Refresh IP** – Refresh the detected Wi-Fi IPv4 address.
- 🎨 **Modern Dark UI** – Clean and professional desktop interface.

---

## 🛠️ Built With

| Technology | Purpose |
|---|---|
| Python 3 | Core programming language |
| PySide6 | Desktop GUI framework |
| Qt | GUI and process management |
| Python http.server | HTTP file hosting |
| QProcess | Server process management |
| psutil | Network interface information |

---

## 📋 Requirements

Before installing LAN Host, make sure you have:

- Windows 10 or Windows 11.
- Python 3.10 or newer.
- Internet connection for installing dependencies.
- Wi-Fi network for sharing files with other devices.

---

# 📥 Installation Guide

Follow these steps in order.

### STEP 1 – Install Python

Download Python from the official website:

https://www.python.org/downloads/

During installation, make sure you enable:

**Add Python to PATH**

After installation, open PowerShell and check:

```powershell
python --version
```

Also verify pip:

```powershell
python -m pip --version
```

### STEP 2 – Open the LAN Host Project Folder

Open your existing LAN Host project folder in VS Code.

Open the integrated terminal:

**Terminal → New Terminal**

Make sure PowerShell is running inside your LAN Host project directory.

Verify your location:

```powershell
Get-Location
```

### STEP 3 – Install Required Dependencies

Install PySide6:

```powershell
python -m pip install PySide6
```

Install psutil:

```powershell
python -m pip install psutil
```

If the project contains a requirements.txt file, install the complete dependency list:

```powershell
python -m pip install -r requirements.txt
```

**Note:** LAN Host uses globally installed Python packages. Creating or activating a virtual environment is not required.

### STEP 4 – Launch LAN Host

Run the application from its project directory:

```powershell
python main.py
```

LAN Host should now open.

---

# 🚀 How to Use LAN Host

### STEP 1 – Open the Application

Launch LAN Host using the installation instructions above.

### STEP 2 – Select Files or Folders

You have two options:

- **Browse Folder:** Select an entire folder to share.
- **Browse File:** Select an individual file. Its parent directory will be hosted.

### STEP 3 – Check Your Wi-Fi Connection

Open the Network Information section.

Verify that:
- Your Wi-Fi adapter is detected.
- Your IPv4 address is displayed.
- Your connection status is Connected.

### STEP 4 – Configure Server Port

The default HTTP server port is:

```text
8000
```

You can change the port using Server Settings.

### STEP 5 – Start the Server

Click:

**HOST SERVER**

Wait until the server status displays:

```text
RUNNING
```

### STEP 6 – Copy the Shareable URL

Once the server starts successfully, LAN Host generates a URL using your active Wi-Fi IPv4 address and configured port.

Example:

```text
http://192.168.1.105:8000/
```

Click **Copy URL** to copy the link.

### STEP 7 – Open on Another Device

1. Connect your phone, tablet, or another computer to the same Wi-Fi network.
2. Open a web browser on that device.
3. Paste the copied URL.
4. Access the hosted files and folders.

### STEP 8 – Stop the Server

When you finish sharing, return to LAN Host and click:

**STOP SERVER**

Your HTTP server will stop.

---

# 🌐 Example of Sharing

Suppose your computer has this Wi-Fi IPv4 address:

```text
192.168.1.105
```

Your server port is:

```text
8000
```

The generated sharing URL will be:

```text
http://192.168.1.105:8000/
```

Another device connected to the same local network can use this address to access the hosted directory.

---

# 🔐 Security and Privacy

LAN Host is designed for local network file sharing.

Important considerations:

- Only share folders containing files you intend to expose.
- Devices that can reach the server may access hosted content.
- Use LAN Host on trusted networks.
- Stop the server when sharing is complete.
- Do not expose the HTTP server directly to the public internet.
- HTTP does not encrypt file transfers.
- Windows Firewall may require permission for Python to accept incoming connections.

**Important:** LAN Host is a local network sharing tool, not a secure public cloud storage service.

---

# 🧰 Troubleshooting

### 1. Python is not recognized

Verify Python installation:

```powershell
python --version
```

If Python is not recognized, check your PATH configuration or reinstall Python with Add Python to PATH enabled.

### 2. PySide6 module not found

Run:

```powershell
python -m pip install PySide6
```

### 3. psutil module not found

Run:

```powershell
python -m pip install psutil
```

### 4. Server does not start

- Verify that a valid file or folder is selected.
- Check whether the configured port is available.
- Check the application error message.
- Verify Python installation.
- Check Windows Firewall permissions.

### 5. Shareable URL does not work

- Ensure both devices are connected to the same Wi-Fi network.
- Verify that the active Wi-Fi IPv4 address is correct.
- Ensure server status displays RUNNING.
- Check Windows Firewall permissions.
- Check whether router AP/client isolation is enabled.

### 6. Port 8000 is already occupied

Check the port using PowerShell:

```powershell
netstat -ano | findstr :8000
```

If necessary, choose another available port in LAN Host.

---

# 🗺️ Future Improvements

Potential future enhancements:

- QR code generation for sharing URLs.
- File upload functionality.
- Download progress monitoring.
- Password-protected sharing.
- Multiple sharing sessions.
- Server activity logs.
- Windows executable installer.
- Improved file management.

---

# 👨‍💻 Author

**Chaitrangan V Thengekar**

Created with ❤️ using Python and PySide6.

---


⭐ If you find LAN Host useful, consider giving this repository a star on GitHub!

