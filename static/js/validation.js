// Validate numeric input only (removes all non-digits)
function validateNumericOnly(event) {
    const input = event.target;
    input.value = input.value.replace(/[^0-9]/g, '');
}

// Validate 10-digit university code
function validateUniversityCode(event) {
    const input = event.target;
    input.value = input.value.replace(/[^0-9]/g, '');
    
    if (input.value.length > 10) {
        input.value = input.value.slice(0, 10);
    }
    
    // Visual feedback
    if (input.value.length === 10) {
        input.style.borderColor = 'green';
        input.style.backgroundColor = '#f0fff0';
    } else if (input.value.length > 0) {
        input.style.borderColor = '#ff6b6b';
        input.style.backgroundColor = '#fff5f5';
    } else {
        input.style.borderColor = '';
        input.style.backgroundColor = '';
    }
}

// Validate phone number (10 digits)
function validatePhone(event) {
    validateNumericOnly(event);
    const input = event.target;
    if (input.value.length > 10) {
        input.value = input.value.slice(0, 10);
    }
}

// Initialize validation on page load
document.addEventListener('DOMContentLoaded', function() {
    // University ID / Code
    const univCode = document.getElementById('university_id');
    if (univCode) {
        univCode.addEventListener('input', validateUniversityCode);
    }
    
    // Phone number
    const phone = document.getElementById('phone');
    if (phone) {
        phone.addEventListener('input', validatePhone);
    }
    
    // Bus number
    const busNo = document.getElementById('bus_number');
    if (busNo) {
        busNo.addEventListener('input', validateNumericOnly);
    }
    
    // Roll number
    const rollNo = document.getElementById('roll_number');
    if (rollNo) {
        rollNo.addEventListener('input', validateNumericOnly);
    }
});
