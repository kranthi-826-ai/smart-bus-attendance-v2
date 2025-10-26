// Dashboard functionality for bus incharge
async function viewTodayAttendance() {
    const listDiv = document.getElementById('attendanceList');
    const dataDiv = document.getElementById('attendanceData');
    
    try {
        dataDiv.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Loading attendance...</p>';
        listDiv.style.display = 'block';
        
        const response = await fetch('/attendance/today-attendance');
        const result = await response.json();
        
        if (result.attendance.length > 0) {
            let html = `
                <div style="margin-bottom: 1rem;">
                    <strong>Present:</strong> ${result.stats.present} | 
                    <strong>Absent:</strong> ${result.stats.absent} | 
                    <strong>Total:</strong> ${result.stats.total}
                </div>
                <div style="max-height: 400px; overflow-y: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: var(--light);">
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--border);">University ID</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--border);">Name</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--border);">Time</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            result.attendance.forEach(record => {
                html += `
                    <tr style="border-bottom: 1px solid var(--border);">
                        <td style="padding: 0.75rem;">${record.university_id}</td>
                        <td style="padding: 0.75rem;">${record.name}</td>
                        <td style="padding: 0.75rem;">${new Date(record.time).toLocaleTimeString()}</td>
                    </tr>
                `;
            });
            
            html += `</tbody></table></div>`;
            dataDiv.innerHTML = html;
        } else {
            dataDiv.innerHTML = '<p>No attendance records for today.</p>';
        }
    } catch (error) {
        dataDiv.innerHTML = '<p style="color: var(--danger);">Error loading attendance data.</p>';
    }
}

async function downloadAttendance() {
    try {
        const response = await fetch('/attendance/download-attendance');
        const result = await response.json();
        
        if (result.success) {
            // Create and download CSV file
            const blob = new Blob([result.csv_data], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = result.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showNotification('Attendance sheet downloaded successfully', 'success');
        } else {
            showNotification('Error downloading attendance sheet', 'error');
        }
    } catch (error) {
        showNotification('Network error downloading file', 'error');
    }
}