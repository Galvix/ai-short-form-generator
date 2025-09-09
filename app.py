#!/usr/bin/env python3
"""
AI Short-Form Content Generator - Web Application
Flask backend with real-time progress tracking and modern UI
"""

import os
import sys
import json
import uuid
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
from datetime import datetime

# Add core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/outputs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize extensions
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store active sessions
active_sessions = {}

# Allowed video file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class ProgressTracker:
    """Track and emit progress updates via WebSocket."""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.current_step = ""
        self.progress = 0
        
    def update(self, step, progress, message=""):
        """Update progress and emit to client."""
        self.current_step = step
        self.progress = progress
        
        socketio.emit('progress_update', {
            'session_id': self.session_id,
            'step': step,
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"[{self.session_id}] {step}: {progress}% - {message}")

@app.route('/')
def index():
    """Main application page."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle video file upload."""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Supported: MP4, AVI, MOV, MKV, WMV, FLV, WebM'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(file_path)
        
        # Store session info
        active_sessions[session_id] = {
            'filename': filename,
            'file_path': file_path,
            'upload_time': datetime.now().isoformat(),
            'status': 'uploaded',
            'outputs': []
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'filename': filename,
            'file_size': os.path.getsize(file_path)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_shorts():
    """Start shorts generation process."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        max_shorts = data.get('max_shorts', 3)
        use_gpt = data.get('use_gpt', True)
        
        if not session_id or session_id not in active_sessions:
            return jsonify({'error': 'Invalid session ID'}), 400
        
        # Update session status
        active_sessions[session_id]['status'] = 'processing'
        active_sessions[session_id]['settings'] = {
            'max_shorts': max_shorts,
            'use_gpt': use_gpt
        }
        
        # Start generation in background thread
        thread = threading.Thread(
            target=generate_shorts_background,
            args=(session_id, max_shorts, use_gpt)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Generation started',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_shorts_background(session_id, max_shorts, use_gpt):
    """Background process for generating shorts."""
    try:
        from shorts_generator import AIShortFormGenerator
        
        # Initialize progress tracker
        tracker = ProgressTracker(session_id)
        
        # Get session info
        session = active_sessions[session_id]
        input_file = session['file_path']
        
        # Create output directory for this session
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        os.makedirs(output_dir, exist_ok=True)
        
        tracker.update("initialization", 10, "Initializing AI Short-Form Generator...")
        
        # Initialize generator
        api_key = os.environ.get('OPENAI_API_KEY') if use_gpt else None
        generator = AIShortFormGenerator(api_key)
        
        tracker.update("transcription", 20, "Starting video transcription...")
        
        # Custom generator with progress tracking
        class ProgressAwareGenerator(AIShortFormGenerator):
            def __init__(self, api_key, progress_tracker):
                super().__init__(api_key)
                self.tracker = progress_tracker
                
            def transcribe_video(self, video_path):
                self.tracker.update("transcription", 30, "Transcribing audio with Whisper...")
                result = super().transcribe_video(video_path)
                self.tracker.update("transcription", 50, "Transcription complete!")
                return result
                
            def analyze_content_for_shorts(self, transcript, duration):
                self.tracker.update("analysis", 60, "Analyzing content for best segments...")
                result = super().analyze_content_for_shorts(transcript, duration)
                self.tracker.update("analysis", 70, f"Found {len(result)} potential segments!")
                return result
        
        # Use progress-aware generator
        generator = ProgressAwareGenerator(api_key, tracker)
        
        tracker.update("processing", 75, "Starting video processing...")
        
        # Generate shorts
        results = generator.generate_shorts(
            input_video=input_file,
            output_dir=output_dir,
            max_shorts=max_shorts
        )
        
        tracker.update("completion", 100, "Generation complete!")
        
        # Update session with results
        if results.get('success', False):
            active_sessions[session_id]['status'] = 'completed'
            # Ensure output_files is a list of strings
            output_files = results.get('output_files', [])
            if isinstance(output_files, list):
                # Convert any dict entries to just filenames
                clean_outputs = []
                for item in output_files:
                    if isinstance(item, dict):
                        # Extract filename from dict if needed
                        filename = item.get('filename', item.get('path', str(item)))
                        clean_outputs.append(filename)
                    else:
                        clean_outputs.append(str(item))
                active_sessions[session_id]['outputs'] = clean_outputs
            else:
                active_sessions[session_id]['outputs'] = []
            
            active_sessions[session_id]['completion_time'] = datetime.now().isoformat()
            
            # Get just filenames for frontend
            output_filenames = [os.path.basename(f) for f in active_sessions[session_id]['outputs']]
            
            # Emit completion event
            socketio.emit('generation_complete', {
                'session_id': session_id,
                'results': {
                    'success': True,
                    'shorts_created': len(output_filenames),
                    'output_files': output_filenames
                },
                'outputs': output_filenames
            })
        else:
            active_sessions[session_id]['status'] = 'error'
            error_messages = results.get('errors', ['Generation failed'])
            active_sessions[session_id]['error'] = error_messages
            
            socketio.emit('generation_error', {
                'session_id': session_id,
                'error': error_messages
            })
            
    except Exception as e:
        active_sessions[session_id]['status'] = 'error'
        active_sessions[session_id]['error'] = str(e)
        
        socketio.emit('generation_error', {
            'session_id': session_id,
            'error': str(e)
        })

@app.route('/api/status/<session_id>')
def get_status(session_id):
    """Get current status of a session."""
    if session_id not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session = active_sessions[session_id]
    return jsonify({
        'session_id': session_id,
        'status': session['status'],
        'filename': session['filename'],
        'outputs': session.get('outputs', []),
        'upload_time': session['upload_time'],
        'completion_time': session.get('completion_time'),
        'error': session.get('error')
    })

@app.route('/api/download-all/<session_id>')
def download_all_zip(session_id):
    """Download all generated videos as a ZIP file."""
    try:
        import zipfile
        import io
        
        if session_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = active_sessions[session_id]
        outputs = session.get('outputs', [])
        
        if not outputs:
            return jsonify({'error': 'No files to download'}), 404
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename in outputs:
                file_path = os.path.join(app.config['OUTPUT_FOLDER'], session_id, filename)
                if os.path.exists(file_path):
                    zip_file.write(file_path, filename)
        
        zip_buffer.seek(0)
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'ai_shorts_{session_id[:8]}.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<session_id>/<filename>')
def download_file(session_id, filename):
    """Download generated video file."""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], session_id, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/preview/<session_id>/<filename>')
def preview_file(session_id, filename):
    """Preview generated video file."""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], session_id, filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'Connected to AI Shorts Generator'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    print("🎬 Starting AI Short-Form Content Generator Web App...")
    print("📱 Access the application at: http://localhost:5000")
    print("🔧 Make sure to set your OPENAI_API_KEY in .env file")
    
    # Run with SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
