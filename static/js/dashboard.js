// Dashboard JavaScript for Asyafira Airdrop Bot
// Real-time updates and interactive functionality

class Dashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.currentSection = 'dashboard';
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.initSocket();
        this.initCharts();
        this.loadInitialData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    initSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.updateConnectionStatus(true);
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.updateConnectionStatus(false);
            });

            this.socket.on('stats_update', (data) => {
                this.updateStats(data);
            });

            this.socket.on('claim_update', (data) => {
                this.updateClaimsTable(data);
            });

            this.socket.on('log_update', (data) => {
                this.addLogEntry(data);
            });

            this.socket.on('bot_status', (data) => {
                this.updateBotStatus(data);
            });

        } catch (error) {
            console.error('Socket.IO initialization failed:', error);
        }
    }

    initCharts() {
        // Performance Chart
        const ctx = document.getElementById('performanceChart');
        if (ctx) {
            this.charts.performance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Success Rate',
                        data: [],
                        borderColor: '#6f42c1',
                        backgroundColor: 'rgba(111, 66, 193, 0.1)',
                        tension: 0.4,
                        fill: true
                    }, {
                        label: 'Claims per Hour',
                        data: [],
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    }
                }
            });
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.sidebar .nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });

        // Auto-refresh logs
        document.getElementById('log-level')?.addEventListener('change', () => {
            this.loadLogs();
        });

        // Schedule type change
        document.getElementById('schedule-type')?.addEventListener('change', () => {
            this.updateScheduleInput();
        });

        // Twitter action change
        document.getElementById('twitter-action')?.addEventListener('change', () => {
            this.updateTwitterForm();
        });
    }

    loadInitialData() {
        this.loadStats();
        this.loadClaims();
        this.loadScheduledTasks();
        this.loadTwitterStats();
        this.loadCookieStats();
        this.loadLogs();
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, 30000); // Refresh every 30 seconds
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            this.updateStats(data);
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    updateStats(data) {
        document.getElementById('total-claims').textContent = data.total_claims || 0;
        document.getElementById('success-rate').textContent = `${data.success_rate || 0}%`;
        document.getElementById('twitter-actions').textContent = data.twitter_actions || 0;
        document.getElementById('scheduled-tasks').textContent = data.scheduled_tasks || 0;
        document.getElementById('active-claims').textContent = data.active_claims || 0;
        document.getElementById('last-claim-time').textContent = data.last_claim_time || 'Never';

        // Update performance chart
        if (this.charts.performance && data.chart_data) {
            this.updatePerformanceChart(data.chart_data);
        }
    }

    updatePerformanceChart(data) {
        const chart = this.charts.performance;
        chart.data.labels = data.labels || [];
        chart.data.datasets[0].data = data.success_rates || [];
        chart.data.datasets[1].data = data.claims_per_hour || [];
        chart.update();
    }

    updateBotStatus(data) {
        const statusElement = document.getElementById('bot-status');
        const currentStatusElement = document.getElementById('current-status');
        
        if (statusElement) {
            const indicator = data.online ? 'status-online' : 'status-offline';
            const text = data.online ? 'Online' : 'Offline';
            statusElement.innerHTML = `<span class="status-indicator ${indicator}"></span>${text}`;
        }

        if (currentStatusElement) {
            const badgeClass = data.online ? 'bg-success' : 'bg-secondary';
            currentStatusElement.className = `badge ${badgeClass}`;
            currentStatusElement.textContent = data.status || 'Idle';
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('bot-status');
        if (statusElement && !connected) {
            statusElement.innerHTML = '<span class="status-indicator status-warning"></span>Connecting...';
        }
    }

    async loadClaims() {
        try {
            const response = await fetch('/api/claims');
            const data = await response.json();
            this.updateClaimsTable(data);
        } catch (error) {
            console.error('Failed to load claims:', error);
        }
    }

    updateClaimsTable(data) {
        const tbody = document.querySelector('#claims-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        
        (data.claims || []).forEach(claim => {
            const row = document.createElement('tr');
            const statusBadge = claim.status === 'success' ? 'badge-success' : 'badge-danger';
            
            row.innerHTML = `
                <td><a href="${claim.url}" target="_blank" class="text-decoration-none">${this.truncateUrl(claim.url)}</a></td>
                <td><span class="badge ${statusBadge}">${claim.status}</span></td>
                <td>${claim.method}</td>
                <td>${this.formatTime(claim.timestamp)}</td>
                <td>${claim.response || 'N/A'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="dashboard.retryClaim('${claim.id}')">
                        <i class="fas fa-redo"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="dashboard.deleteClaim('${claim.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadScheduledTasks() {
        try {
            const response = await fetch('/api/schedule');
            const data = await response.json();
            this.updateScheduleTable(data);
        } catch (error) {
            console.error('Failed to load scheduled tasks:', error);
        }
    }

    updateScheduleTable(data) {
        const tbody = document.querySelector('#schedule-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        
        (data.tasks || []).forEach(task => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td>${task.name}</td>
                <td><a href="${task.url}" target="_blank" class="text-decoration-none">${this.truncateUrl(task.url)}</a></td>
                <td>${task.schedule}</td>
                <td>${this.formatTime(task.next_run)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-warning" onclick="dashboard.pauseTask('${task.id}')">
                        <i class="fas fa-pause"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="dashboard.deleteTask('${task.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async loadTwitterStats() {
        try {
            const response = await fetch('/api/twitter/stats');
            const data = await response.json();
            this.updateTwitterStats(data);
        } catch (error) {
            console.error('Failed to load Twitter stats:', error);
        }
    }

    updateTwitterStats(data) {
        const container = document.getElementById('twitter-stats');
        if (!container) return;

        container.innerHTML = `
            <div class="row">
                <div class="col-6">
                    <div class="text-center">
                        <h4 class="text-primary">${data.tweets || 0}</h4>
                        <small class="text-muted">Tweets</small>
                    </div>
                </div>
                <div class="col-6">
                    <div class="text-center">
                        <h4 class="text-success">${data.follows || 0}</h4>
                        <small class="text-muted">Follows</small>
                    </div>
                </div>
                <div class="col-6 mt-3">
                    <div class="text-center">
                        <h4 class="text-info">${data.likes || 0}</h4>
                        <small class="text-muted">Likes</small>
                    </div>
                </div>
                <div class="col-6 mt-3">
                    <div class="text-center">
                        <h4 class="text-warning">${data.retweets || 0}</h4>
                        <small class="text-muted">Retweets</small>
                    </div>
                </div>
            </div>
        `;
    }

    async loadCookieStats() {
        try {
            const response = await fetch('/api/cookies/stats');
            const data = await response.json();
            this.updateCookieStats(data);
        } catch (error) {
            console.error('Failed to load cookie stats:', error);
        }
    }

    updateCookieStats(data) {
        const container = document.getElementById('cookie-stats');
        if (!container) return;

        container.innerHTML = `
            <div class="row">
                <div class="col-6">
                    <div class="text-center">
                        <h4 class="text-primary">${data.total || 0}</h4>
                        <small class="text-muted">Total Cookies</small>
                    </div>
                </div>
                <div class="col-6">
                    <div class="text-center">
                        <h4 class="text-success">${data.valid || 0}</h4>
                        <small class="text-muted">Valid</small>
                    </div>
                </div>
                <div class="col-6 mt-3">
                    <div class="text-center">
                        <h4 class="text-warning">${data.expired || 0}</h4>
                        <small class="text-muted">Expired</small>
                    </div>
                </div>
                <div class="col-6 mt-3">
                    <div class="text-center">
                        <h4 class="text-info">${data.domains || 0}</h4>
                        <small class="text-muted">Domains</small>
                    </div>
                </div>
            </div>
            <div class="mt-3">
                <div class="progress">
                    <div class="progress-bar bg-success" style="width: ${(data.valid / data.total * 100) || 0}%"></div>
                    <div class="progress-bar bg-warning" style="width: ${(data.expired / data.total * 100) || 0}%"></div>
                </div>
                <small class="text-muted">Cookie Health: ${Math.round((data.valid / data.total * 100) || 0)}% Valid</small>
            </div>
        `;
    }

    async loadLogs() {
        try {
            const level = document.getElementById('log-level')?.value || 'all';
            const response = await fetch(`/api/logs?level=${level}&limit=100`);
            const data = await response.json();
            this.updateLogs(data);
        } catch (error) {
            console.error('Failed to load logs:', error);
        }
    }

    updateLogs(data) {
        const container = document.getElementById('log-container');
        if (!container) return;

        container.innerHTML = '';
        
        (data.logs || []).forEach(log => {
            this.addLogEntry(log, false);
        });

        container.scrollTop = container.scrollHeight;
    }

    addLogEntry(log, scroll = true) {
        const container = document.getElementById('log-container');
        if (!container) return;

        const entry = document.createElement('div');
        entry.className = `log-entry log-${log.level}`;
        entry.innerHTML = `
            <span class="text-muted">[${this.formatTime(log.timestamp)}]</span>
            <span class="fw-bold">[${log.level.toUpperCase()}]</span>
            ${log.message}
        `;

        container.appendChild(entry);

        if (scroll) {
            container.scrollTop = container.scrollHeight;
        }

        // Keep only last 1000 entries
        while (container.children.length > 1000) {
            container.removeChild(container.firstChild);
        }
    }

    // Navigation
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.style.display = 'none';
        });

        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        // Update navigation
        document.querySelectorAll('.sidebar .nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeLink = document.querySelector(`.sidebar .nav-link[href="#${sectionName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        this.currentSection = sectionName;

        // Load section-specific data
        switch (sectionName) {
            case 'claims':
                this.loadClaims();
                break;
            case 'twitter':
                this.loadTwitterStats();
                break;
            case 'schedule':
                this.loadScheduledTasks();
                break;
            case 'cookies':
                this.loadCookieStats();
                break;
            case 'logs':
                this.loadLogs();
                break;
        }
    }

    // Modal functions
    showClaimModal() {
        const modal = new bootstrap.Modal(document.getElementById('claimModal'));
        modal.show();
    }

    showScheduleModal() {
        const modal = new bootstrap.Modal(document.getElementById('scheduleModal'));
        modal.show();
    }

    showTwitterModal() {
        this.updateTwitterForm();
        const modal = new bootstrap.Modal(document.getElementById('twitterModal'));
        modal.show();
    }

    showSettings() {
        // TODO: Implement settings modal
        alert('Settings modal coming soon!');
    }

    // Form handlers
    async submitClaim() {
        const url = document.getElementById('claim-url').value;
        const method = document.getElementById('claim-method').value;

        if (!url) {
            alert('Please enter a URL');
            return;
        }

        try {
            const response = await fetch('/api/claims', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url, method })
            });

            const result = await response.json();
            
            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('claimModal')).hide();
                this.showAlert('Claim started successfully!', 'success');
                this.loadClaims();
            } else {
                this.showAlert(result.error || 'Failed to start claim', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    async submitSchedule() {
        const name = document.getElementById('task-name').value;
        const url = document.getElementById('task-url').value;
        const scheduleType = document.getElementById('schedule-type').value;
        const scheduleValue = document.getElementById('schedule-value').value;
        const method = document.getElementById('task-method').value;

        if (!name || !url || !scheduleValue) {
            alert('Please fill all required fields');
            return;
        }

        try {
            const response = await fetch('/api/schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    url,
                    schedule_type: scheduleType,
                    schedule_value: scheduleValue,
                    method
                })
            });

            const result = await response.json();
            
            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('scheduleModal')).hide();
                this.showAlert('Task scheduled successfully!', 'success');
                this.loadScheduledTasks();
            } else {
                this.showAlert(result.error || 'Failed to schedule task', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    async submitTwitterAction() {
        const action = document.getElementById('twitter-action').value;
        const formData = this.getTwitterFormData(action);

        try {
            const response = await fetch('/api/twitter/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action, ...formData })
            });

            const result = await response.json();
            
            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('twitterModal')).hide();
                this.showAlert('Twitter action completed successfully!', 'success');
                this.loadTwitterStats();
            } else {
                this.showAlert(result.error || 'Failed to execute Twitter action', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    getTwitterFormData(action) {
        const formData = {};
        const form = document.getElementById('twitter-form');
        
        form.querySelectorAll('input, textarea, select').forEach(input => {
            formData[input.id.replace('twitter-', '')] = input.value;
        });
        
        return formData;
    }

    updateScheduleInput() {
        const scheduleType = document.getElementById('schedule-type').value;
        const label = document.getElementById('schedule-value-label');
        const input = document.getElementById('schedule-value');

        switch (scheduleType) {
            case 'interval':
                label.textContent = 'Interval (seconds)';
                input.placeholder = '300';
                break;
            case 'daily':
                label.textContent = 'Time (HH:MM)';
                input.placeholder = '09:00';
                break;
            case 'cron':
                label.textContent = 'Cron Expression';
                input.placeholder = '0 9 * * *';
                break;
        }
    }

    updateTwitterForm() {
        const action = document.getElementById('twitter-action').value;
        const form = document.getElementById('twitter-form');

        let formHTML = '';
        
        switch (action) {
            case 'tweet':
                formHTML = `
                    <div class="mb-3">
                        <label class="form-label">Tweet Text</label>
                        <textarea class="form-control" id="twitter-text" rows="3" placeholder="What's happening?"></textarea>
                    </div>
                `;
                break;
            case 'follow':
                formHTML = `
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-control" id="twitter-username" placeholder="@username">
                    </div>
                `;
                break;
            case 'like':
            case 'retweet':
                formHTML = `
                    <div class="mb-3">
                        <label class="form-label">Tweet URL</label>
                        <input type="url" class="form-control" id="twitter-url" placeholder="https://twitter.com/user/status/123">
                    </div>
                `;
                break;
        }
        
        form.innerHTML = formHTML;
    }

    // Cookie management
    async importCookies() {
        const fileInput = document.getElementById('cookie-file');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Please select a file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/cookies/import', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.showAlert(`Imported ${result.count} cookies successfully!`, 'success');
                this.loadCookieStats();
            } else {
                this.showAlert(result.error || 'Failed to import cookies', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    async exportCookies() {
        try {
            const response = await fetch('/api/cookies/export');
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `cookies_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showAlert('Cookies exported successfully!', 'success');
        } catch (error) {
            this.showAlert('Failed to export cookies', 'danger');
        }
    }

    async refreshCookies() {
        try {
            const response = await fetch('/api/cookies/refresh', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Cookies refreshed successfully!', 'success');
                this.loadCookieStats();
            } else {
                this.showAlert(result.error || 'Failed to refresh cookies', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    async clearCookies() {
        if (!confirm('Are you sure you want to clear all cookies? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/api/cookies/clear', { method: 'DELETE' });
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('All cookies cleared successfully!', 'success');
                this.loadCookieStats();
            } else {
                this.showAlert(result.error || 'Failed to clear cookies', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    // Action handlers
    async retryClaim(claimId) {
        try {
            const response = await fetch(`/api/claims/${claimId}/retry`, { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Claim retry started!', 'success');
                this.loadClaims();
            } else {
                this.showAlert(result.error || 'Failed to retry claim', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    async deleteClaim(claimId) {
        if (!confirm('Are you sure you want to delete this claim?')) {
            return;
        }

        try {
            const response = await fetch(`/api/claims/${claimId}`, { method: 'DELETE' });
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Claim deleted successfully!', 'success');
                this.loadClaims();
            } else {
                this.showAlert(result.error || 'Failed to delete claim', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    async pauseTask(taskId) {
        try {
            const response = await fetch(`/api/schedule/${taskId}/pause`, { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Task paused successfully!', 'success');
                this.loadScheduledTasks();
            } else {
                this.showAlert(result.error || 'Failed to pause task', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }

        try {
            const response = await fetch(`/api/schedule/${taskId}`, { method: 'DELETE' });
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Task deleted successfully!', 'success');
                this.loadScheduledTasks();
            } else {
                this.showAlert(result.error || 'Failed to delete task', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    async postTweet() {
        const text = document.getElementById('tweet-text').value;
        
        if (!text) {
            alert('Please enter tweet text');
            return;
        }

        try {
            const response = await fetch('/api/twitter/tweet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Tweet posted successfully!', 'success');
                document.getElementById('tweet-text').value = '';
                this.loadTwitterStats();
            } else {
                this.showAlert(result.error || 'Failed to post tweet', 'danger');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'danger');
        }
    }

    // Utility functions
    refreshData() {
        switch (this.currentSection) {
            case 'dashboard':
                this.loadStats();
                break;
            case 'claims':
                this.loadClaims();
                break;
            case 'twitter':
                this.loadTwitterStats();
                break;
            case 'schedule':
                this.loadScheduledTasks();
                break;
            case 'cookies':
                this.loadCookieStats();
                break;
            case 'logs':
                this.loadLogs();
                break;
        }
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertContainer.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertContainer);
        
        setTimeout(() => {
            if (alertContainer.parentNode) {
                alertContainer.parentNode.removeChild(alertContainer);
            }
        }, 5000);
    }

    truncateUrl(url, maxLength = 50) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength - 3) + '...';
    }

    formatTime(timestamp) {
        if (!timestamp) return 'N/A';
        
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
}

// Global functions for HTML onclick handlers
let dashboard;

function showSection(section) {
    dashboard.showSection(section);
}

function showClaimModal() {
    dashboard.showClaimModal();
}

function showScheduleModal() {
    dashboard.showScheduleModal();
}

function showTwitterModal() {
    dashboard.showTwitterModal();
}

function showSettings() {
    dashboard.showSettings();
}

function submitClaim() {
    dashboard.submitClaim();
}

function submitSchedule() {
    dashboard.submitSchedule();
}

function submitTwitterAction() {
    dashboard.submitTwitterAction();
}

function updateScheduleInput() {
    dashboard.updateScheduleInput();
}

function updateTwitterForm() {
    dashboard.updateTwitterForm();
}

function importCookies() {
    dashboard.importCookies();
}

function exportCookies() {
    dashboard.exportCookies();
}

function refreshCookies() {
    dashboard.refreshCookies();
}

function clearCookies() {
    dashboard.clearCookies();
}

function refreshData() {
    dashboard.refreshData();
}

function loadLogs() {
    dashboard.loadLogs();
}

function postTweet() {
    dashboard.postTweet();
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new Dashboard();
});