class CameraHandler {
    constructor() {
        this.stream = null;
        this.currentFacingMode = 'user'; // 'user' for front, 'environment' for back
        this.isScanning = false;
    }

    async initializeCamera(facingMode = 'user') {
        try {
            // Stop existing stream
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }

            const constraints = {
                video: { 
                    facingMode: facingMode,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            const videoElement = document.getElementById('cameraFeed');
            
            if (videoElement) {
                videoElement.srcObject = this.stream;
                videoElement.play();
            }

            this.currentFacingMode = facingMode;
            return true;
        } catch (error) {
            console.error('Camera initialization error:', error);
            showNotification('Camera access failed: ' + error.message, 'error');
            return false;
        }
    }

    async switchCamera() {
        const newFacingMode = this.currentFacingMode === 'user' ? 'environment' : 'user';
        const success = await this.initializeCamera(newFacingMode);
        
        if (success) {
            showNotification(`Switched to ${newFacingMode === 'user' ? 'Front' : 'Back'} Camera`, 'success');
        }
        
        return success;
    }

    captureFrame() {
        const video = document.getElementById('cameraFeed');
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        return canvas.toDataURL('image/jpeg');
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }
}

// Global camera instance
const camera = new CameraHandler();

// Camera controls
function setupCameraControls() {
    // Switch camera button
    const switchBtn = document.getElementById('switchCamera');
    if (switchBtn) {
        switchBtn.addEventListener('click', () => camera.switchCamera());
    }

    // Capture button
    const captureBtn = document.getElementById('captureBtn');
    if (captureBtn) {
        captureBtn.addEventListener('click', processAttendance);
    }
}

// Process attendance
async function processAttendance() {
    if (camera.isScanning) return;
    
    camera.isScanning = true;
    const captureBtn = document.getElementById('captureBtn');
    const originalText = captureBtn.innerHTML;
    
    captureBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
    captureBtn.disabled = true;

    try {
        // Capture frame
        const imageData = camera.captureFrame();
        
        // Send to server for face recognition
        const response = await fetch('/attendance/process-attendance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imageData })
        });

        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            
            // Show student info
            if (result.student) {
                showStudentInfo(result.student);
            }
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    } finally {
        captureBtn.innerHTML = originalText;
        captureBtn.disabled = false;
        camera.isScanning = false;
    }
}

function showStudentInfo(student) {
    const infoDiv = document.getElementById('studentInfo');
    if (infoDiv) {
        infoDiv.innerHTML = `
            <div style="background: var(--success); color: white; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
                <h4><i class="fas fa-check-circle"></i> Attendance Marked</h4>
                <p><strong>Name:</strong> ${student.name}</p>
                <p><strong>University ID:</strong> ${student.university_id}</p>
                <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
            </div>
        `;
        
        // Auto hide after 3 seconds
        setTimeout(() => {
            infoDiv.innerHTML = '';
        }, 3000);
    }
}

// Initialize camera when page loads
document.addEventListener('DOMContentLoaded', async function() {
    if (document.getElementById('cameraFeed')) {
        const success = await camera.initializeCamera();
        if (success) {
            setupCameraControls();
            showNotification('Camera ready for attendance scanning', 'success');
        }
    }
});

// Cleanup camera when leaving page
window.addEventListener('beforeunload', () => {
    camera.stopCamera();
});

// Special camera functions for student signup
let signupCamera = null;

function initializeSignupCamera() {
    if (!signupCamera) {
        signupCamera = new CameraHandler();
    }
    return signupCamera.initializeCamera();
}

function stopSignupCamera() {
    if (signupCamera) {
        signupCamera.stopCamera();
        signupCamera = null;
    }
}

// Make camera available globally for signup
window.camera = new CameraHandler();