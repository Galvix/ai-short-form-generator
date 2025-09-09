# 🎬 AI Short-Form Content Generator - Web Frontend

A modern web application for generating AI-powered short-form content from long videos.

## Features

- 🌐 **Modern Web Interface**: Professional React-like UI with responsive design
- 📤 **Drag & Drop Upload**: Easy video file upload with progress tracking
- 🤖 **AI-Powered Analysis**: GPT-4 content analysis and intelligent segmentation
- ⚡ **Real-time Progress**: Live updates during video processing
- 📱 **Mobile Optimized**: Perfect 9:16 output for social media
- 🎯 **Professional Subtitles**: OpenCV-powered subtitle generation
- 🔄 **Bulk Processing**: Generate multiple shorts from single video

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **AI**: OpenAI GPT-4, Whisper
- **Video Processing**: MoviePy, OpenCV
- **Real-time Updates**: WebSockets (Flask-SocketIO)

## 🚀 Running the Project

### Prerequisites
**Set up environment variables**:  
   Create a file named `.env` and copy the contents from `.env.example` in the project root
   
   Add your api key here:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```

---
Now, 
you have two options to run this project: **manually with Python** or **using Docker**.


### 🔹 Option 1: Run Manually (Python + Requirements)

1. **Create and activate a virtual environment (Optional as you can create the env any way you want)**:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / Mac
   venv\Scripts\activate      # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**:
   ```bash
   python app.py
   ```

5. **The project will be available at:**
   ```
   http://localhost:5000
   ```

---

### 🔹 Option 2: Run with Docker

1. **Build the image**:
   ```bash
   docker build -t ai-shorts-generator .
   ```

2. **Run the container**:
   ```bash
   docker run -d -p 5000:5000 --env-file .env ai-shorts-generator
   ```

3. Open in your browser:
   ```
   http://localhost:5000
   ```

---

## 🌍 Deployment (Free Option: Cloudflare Tunnel)

If you want to access your app **from anywhere** (without port forwarding):
Here is what I did. I am running a Ubuntu server on my Raspberry Pi and here are the steps I did to host and access this app from anywhere without port forwarding.

1. **Install Cloudflare Tunnel** on your server (Ubuntu):
   ```bash
   curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
   echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" |      sudo tee /etc/apt/sources.list.d/cloudflared.list
   sudo apt update && sudo apt install cloudflared -y
   ```

2. **Run tunnel pointing to your app**:
   ```bash
   cloudflared tunnel --url http://localhost:5000
   ```

   You’ll get a public URL like:
   ```
   https://random-id.trycloudflare.com
   ```

3. **Keep it running in background (so it survives closing SSH/PuTTY)**:

   - Quick way with `nohup`:
     ```bash
     nohup cloudflared tunnel --url http://localhost:5000 > cloudflared.log 2>&1 &
     ```

     Check your URL later:
     ```bash
     cat cloudflared.log | grep "trycloudflare.com"
     ```

   - **Recommended**: Create a systemd service so it auto-starts on reboot:
        (although the link would be different everytime)
     ```bash
     sudo nano /etc/systemd/system/cloudflared-tunnel.service
     ```

     Add:
     ```ini
     [Unit]
     Description=Cloudflare Tunnel for AI Shorts Generator
     After=network.target

     [Service]
     ExecStart=/usr/bin/cloudflared tunnel --url http://localhost:5000
     Restart=always
     User=pi
     WorkingDirectory=/home/pi

     [Install]
     WantedBy=multi-user.target
     ```

     Then enable + start:
     ```bash
     sudo systemctl daemon-reload
     sudo systemctl enable cloudflared-tunnel
     sudo systemctl start cloudflared-tunnel
     ```

     Check status:
     ```bash
     systemctl status cloudflared-tunnel
     ```

Now your app will always be accessible from a **public Cloudflare URL**, even if you close PuTTY or reboot your server.

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

⭐ **If you find this project useful, please give it a star!**

Made with ❤️ by [Subh-kami](https://github.com/Subh-kami)   
Deployment contribution by [Galvix](https://github.com/Galvix)