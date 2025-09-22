// Global variables
let stream = null;
let cameraActive = false;

// DOM Elements
const videoElement = document.getElementById('videoElement');
const canvasElement = document.getElementById('canvasElement');
const startCameraBtn = document.getElementById('startCameraBtn');
const captureBtn = document.getElementById('captureBtn');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const resultContainer = document.getElementById('result');
const resultText = document.getElementById('resultText');

// Start camera
startCameraBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'environment',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        });
        videoElement.srcObject = stream;
        cameraActive = true;
        
        startCameraBtn.disabled = true;
        startCameraBtn.textContent = 'Camera Active';
        captureBtn.disabled = false;
        uploadBtn.disabled = false;
        
        // Auto-capture every 3 seconds (simulates continuous scanning)
        setTimeout(() => {
            if (cameraActive) {
                captureImage();
                setInterval(captureImage, 3000); // Scan every 3 seconds
            }
        }, 1000);
        
    } catch (error) {
        console.error('Error accessing camera:', error);
        showResult('❌ Could not access camera. Please check permissions.', 'error');
    }
});

// Capture image from camera
function captureImage() {
    if (!cameraActive) return;
    
    const context = canvasElement.getContext('2d');
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    
    // Convert to blob and send to server
    canvasElement.toBlob(blob => {
        // Create a filename with timestamp for simulation
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `scan-${timestamp}.jpg`;
        const file = new File([blob], filename, { type: 'image/jpeg' });
        
        sendImageToServer(file);
    }, 'image/jpeg', 0.8);
}

// Manual capture button
captureBtn.addEventListener('click', () => {
    captureImage();
});

// Upload image from file
uploadBtn.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        sendImageToServer(file);
    }
});

// Send image to server for face recognition
async function sendImageToServer(imageFile) {
    const formData = new FormData();
    formData.append('image', imageFile);

    showResult('🔄 Processing image...', 'loading');

    try {
        const response = await fetch('/mark_attendance', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (result.success) {
            if (result.status === 'already_marked') {
                showResult(`✅ ${result.message}<br>🕒 ${result.time}`, 'warning');
            } else {
                showResult(`✅ ${result.message}<br>🎓 ${result.student_name}<br>🔢 ${result.roll_number}<br>🕒 ${result.time}`, 'success');
            }
        } else {
            showResult(`❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showResult('❌ Network error. Please try again.', 'error');
    }
}

// Show result message
function showResult(message, type) {
    resultText.innerHTML = message;
    resultContainer.className = 'result-container';
    
    // Add type-based styling
    if (type === 'success') {
        resultContainer.style.borderLeftColor = '#28a745';
        resultContainer.style.backgroundColor = '#d4edda';
    } else if (type === 'error') {
        resultContainer.style.borderLeftColor = '#dc3545';
        resultContainer.style.backgroundColor = '#f8d7da';
    } else if (type === 'warning') {
        resultContainer.style.borderLeftColor = '#ffc107';
        resultContainer.style.backgroundColor = '#fff3cd';
    } else {
        resultContainer.style.borderLeftColor = '#17a2b8';
        resultContainer.style.backgroundColor = '#d1ecf1';
    }
    
    resultContainer.classList.remove('hidden');
    
    // Clear result after 5 seconds (except for errors)
    if (type !== 'error') {
        setTimeout(() => {
            resultContainer.classList.add('hidden');
        }, 5000);
    }
}

// Stop camera when leaving page
window.addEventListener('beforeunload', () => {
    stopCamera();
});

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    cameraActive = false;
    startCameraBtn.disabled = false;
    startCameraBtn.textContent = 'Start Camera';
}

// View report button
document.getElementById('viewReportBtn').addEventListener('click', () => {
    alert('This would show a modal with today\'s attendance report. We\'ll implement this next!');
});