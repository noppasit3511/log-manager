<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mini SIEM - Security Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        body { background-color: #f4f6f9; color: #333; font-family: 'Segoe UI', Tahoma, sans-serif; }
        .card { border: none; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05); }
        .card-header { background-color: #ffffff; border-bottom: 1px solid #eee; font-weight: bold; color: #444; }
        .badge-error { background-color: #dc3545; color: white; }
        .badge-warning { background-color: #ffc107; color: black; }
        .badge-info { background-color: #17a2b8; color: white; }
        .role-selector { background: #fff; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #0d6efd; }
    </style>
</head>
<body>

<div class="container mt-4">
    <h2><i class="fa-solid fa-shield-halved text-primary"></i> Security Operations Center (SOC)</h2>
    <p class="text-muted">Multi-tenant Log Management System</p>

    <div class="role-selector d-flex align-items-center justify-content-between">
        <div>
            <strong>จำลองสิทธิ์ผู้ใช้งาน (RBAC & Multi-tenant):</strong>
            <span id="currentUserLabel" class="badge bg-primary ms-2">Admin (All Tenants)</span>
        </div>
        <div>
            <select id="roleSelect" class="form-select w-auto d-inline-block" onchange="changeRole()">
                <option value="admin-key">Admin (ดูได้ทุกระบบ)</option>
                <option value="viewer-a-key">Viewer (เฉพาะ Tenant A)</option>
                <option value="viewer-b-key">Viewer (เฉพาะ Tenant B)</option>
            </select>
            <button class="btn btn-sm btn-success ms-2" onclick="fetchDashboardData()">
                <i class="fa-solid fa-rotate-right"></i> รีเฟรชข้อมูล
            </button>
        </div>
    </div>

    <div class="row">
        <div class="col-md-3"><div class="card p-3 text-center"><h5 class="text-muted">Total Events</h5><h3 id="totalEvents">0</h3></div></div>
        <div class="col-md-3"><div class="card p-3 text-center"><h5 class="text-danger">Critical Alerts</h5><h3 id="errorEvents" class="text-danger">0</h3></div></div>
        <div class="col-md-3"><div class="card p-3 text-center"><h5 class="text-muted">Unique Sources</h5><h3 id="uniqueSources">0</h3></div></div>
        <div class="col-md-3"><div class="card p-3 text-center"><h5 class="text-muted">Active Tenant</h5><h3 id="activeTenant" class="text-primary">ALL</h3></div></div>
    </div>

    <div class="row">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">Timeline (Recent Events)</div>
                <div class="card-body"><canvas id="timelineChart" height="100"></canvas></div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">Top Event Sources</div>
                <div class="card-body"><canvas id="sourceChart" height="200"></canvas></div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header d-flex justify-content-between">
            <span>Recent Security Logs</span>
        </div>
        <div class="card-body p-0 table-responsive">
            <table class="table table-hover mb-0 text-nowrap">
                <thead class="table-light">
                    <tr>
                        <th>Time</th>
                        <th>Tenant</th>
                        <th>Source</th>
                        <th>Event Type</th>
                        <th>Level</th>
                        <th>Source IP</th>
                        <th>Message</th>
                        <th>Raw Data</th>
                    </tr>
                </thead>
                <tbody id="logTableBody">
                    </tbody>
            </table>
        </div>
    </div>
</div>

<div class="modal fade" id="jsonModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Raw JSON Data</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <pre><code id="jsonContent"></code></pre>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
    const API_URL = 'http://localhost:8000/logs?limit=50';
    let timelineChartInstance = null;
    let sourceChartInstance = null;
    let currentApiKey = 'admin-key'; // Default เป็น Admin

    function changeRole() {
        const select = document.getElementById('roleSelect');
        currentApiKey = select.value;
        const label = document.getElementById('currentUserLabel');
        const activeTenantLabel = document.getElementById('activeTenant');
        
        if(currentApiKey === 'admin-key') {
            label.className = "badge bg-primary ms-2";
            label.innerText = "Admin (All Tenants)";
            activeTenantLabel.innerText = "ALL";
            activeTenantLabel.className = "text-primary";
        } else if (currentApiKey === 'viewer-a-key') {
            label.className = "badge bg-info ms-2";
            label.innerText = "Viewer (Tenant A)";
            activeTenantLabel.innerText = "demoA";
            activeTenantLabel.className = "text-info";
        } else {
            label.className = "badge bg-secondary ms-2";
            label.innerText = "Viewer (Tenant B)";
            activeTenantLabel.innerText = "demoB";
            activeTenantLabel.className = "text-secondary";
        }
        fetchDashboardData();
    }

    function showJson(jsonStr) {
        document.getElementById('jsonContent').innerText = JSON.stringify(JSON.parse(decodeURIComponent(jsonStr)), null, 2);
        new bootstrap.Modal(document.getElementById('jsonModal')).show();
    }

    async function fetchDashboardData() {
        try {
            // ยิง API พร้อมแนบ X-API-Key เพื่อทำ AuthN/AuthZ
            const response = await fetch(API_URL, {
                headers: {
                    'X-API-Key': currentApiKey
                }
            });

            if (!response.ok) {
                if(response.status === 401 || response.status === 403) {
                    alert("Access Denied: คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้");
                }
                throw new Error('Network response was not ok');
            }

            const logsData = await response.json();

            // --- 1. Update Metrics ---
            document.getElementById('totalEvents').innerText = logsData.length;
            document.getElementById('errorEvents').innerText = logsData.filter(l => l.level === 'ERROR').length;
            const uniqueSources = [...new Set(logsData.map(l => l.source))].length;
            document.getElementById('uniqueSources').innerText = uniqueSources;

            // --- 2. อัปเดตกราฟเส้น (Timeline) ---
            const timeCounts = {};
            // จัดเรียงใหม่จากเก่าไปใหม่ เพื่อให้กราฟเส้นวาดจากซ้ายไปขวา
            const reversedLogs = [...logsData].reverse();
            reversedLogs.forEach(log => {
                const timeStr = new Date(log.timestamp + 'Z').toLocaleTimeString('th-TH');
                timeCounts[timeStr] = (timeCounts[timeStr] || 0) + 1;
            });
            const timelineCtx = document.getElementById('timelineChart').getContext('2d');
            if (timelineChartInstance) timelineChartInstance.destroy();
            timelineChartInstance = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: Object.keys(timeCounts),
                    datasets: [{
                        label: 'Events per Second',
                        data: Object.values(timeCounts),
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.2)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                }
            });

            // --- 3. อัปเดตกราฟแท่ง (Sources) ---
            const sourceCounts = {};
            logsData.forEach(log => {
                sourceCounts[log.source] = (sourceCounts[log.source] || 0) + 1;
            });
            const sourceCtx = document.getElementById('sourceChart').getContext('2d');
            if (sourceChartInstance) sourceChartInstance.destroy();
            sourceChartInstance = new Chart(sourceCtx, {
                type: 'bar',
                data: {
                    labels: Object.keys(sourceCounts),
                    datasets: [{ label: 'Events', data: Object.values(sourceCounts), backgroundColor: '#0d6efd' }]
                },
                options: {
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                }
            });

            // --- 4. อัปเดตตารางข้อมูล ---
            const tableBody = document.getElementById('logTableBody');
            tableBody.innerHTML = ''; 

            logsData.slice(0, 15).forEach(log => {
                let badgeClass = 'badge-info';
                if (log.level === 'ERROR') badgeClass = 'badge-error';
                if (log.level === 'WARNING') badgeClass = 'badge-warning';

                let localTime = new Date(log.timestamp + 'Z').toLocaleString('th-TH');
                
                // แปลง raw_data เป็น string สำหรับปุ่ม JSON
                let safeJson = encodeURIComponent(JSON.stringify(log.raw_data));

                const row = `
                    <tr>
                        <td style="font-size: 0.85rem;">${localTime}</td>
                        <td><span class="badge bg-secondary">${log.tenant}</span></td>
                        <td><strong>${log.source}</strong></td>
                        <td>${log.event_type || '-'}</td>
                        <td><span class="badge ${badgeClass} px-2 py-1">${log.level}</span></td>
                        <td><code>${log.src_ip || '-'}</code></td>
                        <td>${log.message}</td>
                        <td><button class="btn btn-sm btn-outline-primary" onclick="showJson('${safeJson}')"><i class="fa-solid fa-code"></i> JSON</button></td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });

        } catch (error) {
            console.error("เชื่อมต่อ API ไม่สำเร็จ:", error);
        }
    }

    // โหลดข้อมูลครั้งแรก
    fetchDashboardData();
    // รีเฟรชอัตโนมัติทุก 5 วินาทีให้ดู Real-time สวยๆ ตอนอัดคลิป
    setInterval(fetchDashboardData, 5000);
</script>
</body>
</html>