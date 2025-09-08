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

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Open browser to http://localhost:5000
```

## Project Structure

```
Frontend/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── static/               # CSS, JS, assets
│   ├── css/
│   ├── js/
│   └── uploads/
├── templates/            # HTML templates
└── core/                # Backend logic
    └── shorts_generator.py
```

## Development

1. **Setup Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create `.env` file with your OpenAI API key

3. **Run Development Server**:
   ```bash
   python app.py
   ```

## Deployment

Ready for deployment on platforms like:
- Heroku
- Railway
- Vercel
- Digital Ocean
- AWS EC2

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🆘 Support & Issues

- 🐛 **Bug Reports**: [Create an Issue](https://github.com/Subh-kami/ai-short-form-generator/issues)
- 💡 **Feature Requests**: [Start a Discussion](https://github.com/Subh-kami/ai-short-form-generator/discussions)
- 📧 **Contact**: mrsubhanshud12@gmail.com

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

⭐ **If you find this project useful, please give it a star!**

Made with ❤️ by [Subh-kami](https://github.com/Subh-kami)
