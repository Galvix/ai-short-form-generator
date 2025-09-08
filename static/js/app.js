// AI Short-Form Content Generator - Frontend JavaScript

class ShortsGeneratorApp {
    constructor() {
        this.socket = null;
        this.currentSessionId = null;
        this.currentFile = null;
        
        this.init();
    }
    
    init() {
        this.initializeSocketIO();
        this.bindEvents();
        this.showSection('uploadSection');
    }
    
    initializeSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
            this.showToast('Connected to server', 'success');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
            this.showToast('Disconnected from server', 'warning');
        });
        
        this.socket.on('progress_update', (data) => {
            this.handleProgressUpdate(data);
        });
        
        this.socket.on('generation_complete', (data) => {
            this.handleGenerationComplete(data);
        });
        
        this.socket.on('generation_error', (data) => {
            this.handleGenerationError(data);
        });
    }
    
    bindEvents() {
        // Upload area events
        const uploadArea = document.getElementById('uploadArea');
        const videoInput = document.getElementById('videoInput');
        const uploadBtn = document.getElementById('uploadBtn');
        
        uploadArea.addEventListener('click', () => videoInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        
        videoInput.addEventListener('change', this.handleFileSelect.bind(this));
        uploadBtn.addEventListener('click', () => videoInput.click());
        
        // Settings events
        document.getElementById('backBtn').addEventListener('click', () => {
            this.showSection('uploadSection');
        });
        
        document.getElementById('generateBtn').addEventListener('click', this.startGeneration.bind(this));
        
        // Results events
        document.getElementById('newVideoBtn').addEventListener('click', () => {
            this.reset();
        });
        
        document.getElementById('downloadAllBtn').addEventListener('click', this.downloadAll.bind(this));
        
        // Error events
        document.getElementById('retryBtn').addEventListener('click', () => {
            this.showSection('settingsSection');
        });
    }
    
    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connectionStatus');
        statusEl.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
        statusEl.innerHTML = `
            <i class="fas fa-circle"></i>
            <span>${connected ? 'Connected' : 'Disconnected'}</span>
        `;
    }
    
    showSection(sectionId) {
        const sections = ['uploadSection', 'settingsSection', 'progressSection', 'resultsSection', 'errorSection'];
        sections.forEach(id => {
            document.getElementById(id).style.display = id === sectionId ? 'block' : 'none';
        });
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideInToast 0.3s ease reverse';
            setTimeout(() => container.removeChild(toast), 300);
        }, 3000);
    }
    
    showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }
    
    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }
    
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }
    
    processFile(file) {
        // Validate file type
        const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/wmv', 'video/webm'];
        if (!allowedTypes.includes(file.type) && !this.hasValidVideoExtension(file.name)) {
            this.showToast('Please select a valid video file', 'error');
            return;
        }
        
        // Validate file size (500MB max)
        if (file.size > 500 * 1024 * 1024) {
            this.showToast('File size must be less than 500MB', 'error');
            return;
        }
        
        this.currentFile = file;
        this.uploadFile(file);
    }
    
    hasValidVideoExtension(filename) {
        const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'];
        return validExtensions.some(ext => filename.toLowerCase().endsWith(ext));
    }
    
    async uploadFile(file) {
        this.showLoading(true);
        
        const formData = new FormData();
        formData.append('video', file);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSessionId = data.session_id;
                this.showFileInfo(data);
                this.showSection('settingsSection');
                this.showToast('Video uploaded successfully!', 'success');
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showToast('Upload failed: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    showFileInfo(data) {
        const fileInfo = document.getElementById('fileInfo');
        fileInfo.innerHTML = `
            <div class="file-name">
                <i class="fas fa-video"></i>
                ${data.filename}
            </div>
            <div class="file-size">
                ${this.formatFileSize(data.file_size)}
            </div>
        `;
    }
    
    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 Bytes';
        const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    async startGeneration() {
        if (!this.currentSessionId) {
            this.showToast('No video uploaded', 'error');
            return;
        }
        
        const maxShorts = parseInt(document.getElementById('maxShorts').value);
        const useGPT = document.getElementById('useGPT').checked;
        
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    max_shorts: maxShorts,
                    use_gpt: useGPT
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSection('progressSection');
                this.initializeProgress();
                this.showToast('Generation started!', 'success');
            } else {
                throw new Error(data.error || 'Generation failed to start');
            }
        } catch (error) {
            console.error('Generation error:', error);
            this.showToast('Failed to start generation: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    initializeProgress() {
        // Reset progress
        this.updateProgress(0);
        this.updateCurrentStatus('Preparing to start...');
        
        // Reset all steps
        const steps = ['initialization', 'transcription', 'analysis', 'processing', 'completion'];
        steps.forEach(step => {
            const stepEl = document.getElementById(`step-${step}`);
            stepEl.classList.remove('active', 'completed');
        });
    }
    
    updateProgress(percentage) {
        document.getElementById('progressFill').style.width = `${percentage}%`;
        document.getElementById('progressText').textContent = `${Math.round(percentage)}%`;
    }
    
    updateCurrentStatus(message) {
        document.getElementById('currentStatus').innerHTML = `<p>${message}</p>`;
    }
    
    updateProgressStep(stepName, status = 'active') {
        const stepEl = document.getElementById(`step-${stepName}`);
        if (stepEl) {
            stepEl.classList.remove('active', 'completed');
            stepEl.classList.add(status);
        }
    }
    
    handleProgressUpdate(data) {
        if (data.session_id !== this.currentSessionId) return;
        
        this.updateProgress(data.progress);
        this.updateCurrentStatus(data.message);
        
        // Update step status
        const stepMap = {
            'initialization': 'initialization',
            'transcription': 'transcription',
            'analysis': 'analysis',
            'processing': 'processing',
            'completion': 'completion'
        };
        
        const stepName = stepMap[data.step];
        if (stepName) {
            // Mark previous steps as completed
            const steps = ['initialization', 'transcription', 'analysis', 'processing', 'completion'];
            const currentIndex = steps.indexOf(stepName);
            
            steps.forEach((step, index) => {
                if (index < currentIndex) {
                    this.updateProgressStep(step, 'completed');
                } else if (index === currentIndex) {
                    this.updateProgressStep(step, 'active');
                }
            });
        }
    }
    
    handleGenerationComplete(data) {
        if (data.session_id !== this.currentSessionId) return;
        
        this.updateProgress(100);
        this.updateCurrentStatus('Generation completed successfully!');
        
        // Mark all steps as completed
        const steps = ['initialization', 'transcription', 'analysis', 'processing', 'completion'];
        steps.forEach(step => this.updateProgressStep(step, 'completed'));
        
        setTimeout(() => {
            this.showResults(data);
            // Auto-download all files
            this.autoDownloadAll();
        }, 1000);
    }
    
    handleGenerationError(data) {
        if (data.session_id !== this.currentSessionId) return;
        
        this.showError(data.error);
    }
    
    showResults(data) {
        this.showSection('resultsSection');
        
        const resultsGrid = document.getElementById('resultsGrid');
        resultsGrid.innerHTML = '';
        
        // Add download status message
        const downloadMessage = document.createElement('div');
        downloadMessage.className = 'download-status';
        downloadMessage.innerHTML = `
            <div style="background: var(--dark-elevated); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; text-align: center;">
                <i class="fas fa-download" style="color: var(--success-color); margin-right: 0.5rem;"></i>
                <strong>Auto-download started!</strong> Your shorts are being downloaded as a ZIP file.
                <br><small>If the download doesn't start, use the manual download buttons below.</small>
            </div>
        `;
        resultsGrid.appendChild(downloadMessage);
        
        data.outputs.forEach((filename, index) => {
            const card = this.createResultCard(filename, index + 1);
            resultsGrid.appendChild(card);
        });
        
        this.showToast('All shorts generated successfully!', 'success');
    }
    
    createResultCard(filename, index) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        const videoUrl = `/api/preview/${this.currentSessionId}/${filename}`;
        const downloadUrl = `/api/download/${this.currentSessionId}/${filename}`;
        
        card.innerHTML = `
            <video controls poster="">
                <source src="${videoUrl}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <div class="result-card-content">
                <h3>Short ${index}</h3>
                <div class="result-card-meta">
                    <span><i class="fas fa-file-video"></i> ${filename}</span>
                </div>
                <div class="result-card-actions">
                    <a href="${downloadUrl}" class="btn-small btn-primary" download>
                        <i class="fas fa-download"></i>
                        Download
                    </a>
                    <button class="btn-small btn-secondary" onclick="app.shareVideo('${filename}')">
                        <i class="fas fa-share"></i>
                        Share
                    </button>
                </div>
            </div>
        `;
        
        return card;
    }
    
    showError(errorMessage) {
        this.showSection('errorSection');
        
        document.getElementById('errorMessage').innerHTML = `
            <p><strong>Error:</strong> ${Array.isArray(errorMessage) ? errorMessage.join(', ') : errorMessage}</p>
            <p>Please try again or contact support if the problem persists.</p>
        `;
        
        this.showToast('Generation failed', 'error');
    }
    
    async autoDownloadAll() {
        if (!this.currentSessionId) return;
        
        try {
            this.showToast('Starting automatic download...', 'info');
            
            // Download as ZIP file
            const link = document.createElement('a');
            link.href = `/api/download-all/${this.currentSessionId}`;
            link.download = `ai_shorts_${this.currentSessionId.substring(0, 8)}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast('Download started! Check your downloads folder.', 'success');
            
        } catch (error) {
            console.error('Auto-download error:', error);
            this.showToast('Auto-download failed, use manual download buttons', 'warning');
        }
    }
    
    async downloadAll() {
        if (!this.currentSessionId) return;
        
        try {
            // Download as ZIP file
            const link = document.createElement('a');
            link.href = `/api/download-all/${this.currentSessionId}`;
            link.download = `ai_shorts_${this.currentSessionId.substring(0, 8)}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast('Downloading all shorts as ZIP...', 'success');
            
        } catch (error) {
            console.error('Download error:', error);
            this.showToast('Failed to download files', 'error');
        }
    }
    
    shareVideo(filename) {
        if (navigator.share) {
            const videoUrl = `${window.location.origin}/api/preview/${this.currentSessionId}/${filename}`;
            navigator.share({
                title: 'AI Generated Short Video',
                text: 'Check out this AI-generated short video!',
                url: videoUrl
            }).catch(err => console.log('Error sharing:', err));
        } else {
            // Fallback: copy link to clipboard
            const videoUrl = `${window.location.origin}/api/preview/${this.currentSessionId}/${filename}`;
            navigator.clipboard.writeText(videoUrl).then(() => {
                this.showToast('Video link copied to clipboard!', 'success');
            }).catch(() => {
                this.showToast('Unable to copy link', 'error');
            });
        }
    }
    
    reset() {
        this.currentSessionId = null;
        this.currentFile = null;
        
        // Reset form
        document.getElementById('videoInput').value = '';
        document.getElementById('maxShorts').value = '3';
        document.getElementById('useGPT').checked = true;
        
        // Clear results
        document.getElementById('resultsGrid').innerHTML = '';
        
        this.showSection('uploadSection');
        this.showToast('Ready for new video', 'info');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ShortsGeneratorApp();
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    if (window.app) {
        window.app.showToast('An unexpected error occurred', 'error');
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && window.app && window.app.socket) {
        // Reconnect socket if needed
        if (!window.app.socket.connected) {
            window.app.socket.connect();
        }
    }
});
