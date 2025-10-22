// Global variables
let currentPage = 1;
let currentFilters = {};
let categoryChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Load initial data
        await loadDashboardStats();
        await loadFilters();
        await loadJobs();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize chat
        initializeChat();
        
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showError('Failed to load application data');
    }
}

function setupEventListeners() {
    // Search and filter events
    document.getElementById('search-btn').addEventListener('click', handleSearch);
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    
    // Manual scrape button
    document.getElementById('manual-scrape-btn').addEventListener('click', handleManualScrape);
    
    // Chat events
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Example question buttons
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            document.getElementById('chat-input').value = question;
            sendMessage();
        });
    });
}

async function loadDashboardStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        if (stats.error) {
            throw new Error(stats.error);
        }
        
        // Update stat cards
        document.getElementById('total-jobs').textContent = stats.total_jobs || 0;
        document.getElementById('recent-jobs').textContent = stats.recent_jobs || 0;
        
        // Top category
        if (stats.category_stats && stats.category_stats.length > 0) {
            const topCategory = stats.category_stats[0];
            document.getElementById('top-category').textContent = topCategory.category;
        }
        
        // Create category chart
        createCategoryChart(stats.category_stats || []);
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

function createCategoryChart(categoryStats) {
    const ctx = document.getElementById('category-chart').getContext('2d');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    const labels = categoryStats.map(stat => stat.category);
    const data = categoryStats.map(stat => stat.count);
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#667eea',
                    '#764ba2',
                    '#f093fb',
                    '#f5576c',
                    '#4facfe',
                    '#00f2fe',
                    '#43e97b',
                    '#38f9d7'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                title: {
                    display: true,
                    text: 'Jobs by Category',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        }
    });
}

async function loadFilters() {
    try {
        // Load categories
        const categoriesResponse = await fetch('/api/categories');
        const categoriesData = await categoriesResponse.json();
        
        const categorySelect = document.getElementById('category-filter');
        categorySelect.innerHTML = '<option value="">All Categories</option>';
        
        if (categoriesData.categories) {
            categoriesData.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categorySelect.appendChild(option);
            });
        }
        
        // Load locations
        const locationsResponse = await fetch('/api/locations');
        const locationsData = await locationsResponse.json();
        
        const locationSelect = document.getElementById('location-filter');
        locationSelect.innerHTML = '<option value="">All Locations</option>';
        
        if (locationsData.locations) {
            locationsData.locations.forEach(location => {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                locationSelect.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

async function loadJobs(page = 1) {
    try {
        const params = new URLSearchParams({
            page: page,
            per_page: 20,
            ...currentFilters
        });
        
        const response = await fetch(`/api/jobs?${params}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayJobs(data.jobs);
        updatePagination(data);
        
    } catch (error) {
        console.error('Error loading jobs:', error);
        showError('Failed to load jobs');
    }
}

function displayJobs(jobs) {
    const jobList = document.getElementById('job-list');
    
    if (jobs.length === 0) {
        jobList.innerHTML = '<div class="text-center text-muted mt-20">No jobs found matching your criteria.</div>';
        return;
    }
    
    jobList.innerHTML = jobs.map(job => {
        const hasDescription = job.description && job.description.trim() !== '';
        const descriptionPreview = hasDescription ? job.description.substring(0, 200) : '';
        const isNewToday = job.is_new_today === 1;
        
        return `
        <div class="job-card ${isNewToday ? 'job-card-new' : ''}">
            <div class="job-header">
                <div>
                    <h3 class="job-title">
                        ${isNewToday ? '<span class="new-tag">🆕 NEW</span>' : ''}
                        ${escapeHtml(job.title)}
                    </h3>
                    <div class="job-company">${escapeHtml(job.company)}</div>
                </div>
                <div class="job-actions">
                    ${hasDescription ? `<button onclick="viewJobDetail(${job.id})" class="btn-view-jd">📄 View JD</button>` : ''}
                    <a href="${job.url}" target="_blank" class="job-link">🔗 Original</a>
                </div>
            </div>
            
            <div class="job-meta">
                ${job.source ? `<span class="job-source">🌐 ${escapeHtml(job.source)}</span>` : ''}
                ${job.location ? `<span>📍 ${escapeHtml(job.location)}</span>` : ''}
                ${job.category ? `<span class="job-category">${escapeHtml(job.category)}</span>` : ''}
                ${job.salary_range ? `<span>💰 ${escapeHtml(job.salary_range)}</span>` : ''}
                ${job.job_type ? `<span>⏰ ${escapeHtml(job.job_type)}</span>` : ''}
            </div>
            
            ${hasDescription ? `
                <div class="job-description-preview">
                    ${escapeHtml(descriptionPreview)}${descriptionPreview.length >= 200 ? '...' : ''}
                </div>
            ` : ''}
            
            ${job.skills && job.skills.length > 0 ? `
                <div class="job-skills">
                    ${job.skills.map(skill => `<span class="skill-tag">${escapeHtml(skill)}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `;
    }).join('');
}

// View job detail in modal
async function viewJobDetail(jobId) {
    try {
        const response = await fetch(`/api/jobs/${jobId}`);
        const job = await response.json();
        
        if (job.error) {
            throw new Error(job.error);
        }
        
        showJobModal(job);
    } catch (error) {
        console.error('Error loading job detail:', error);
        alert('Failed to load job details');
    }
}

function showJobModal(job) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = function(e) {
        if (e.target === modal) {
            closeJobModal();
        }
    };
    
    const descriptionHtml = job.description 
        ? job.description.split('\n').map(line => `<p>${escapeHtml(line)}</p>`).join('')
        : '<p class="text-muted">No description available.</p>';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <h2>${escapeHtml(job.title)}</h2>
                    <p class="modal-company">${escapeHtml(job.company)}</p>
                </div>
                <button class="modal-close" onclick="closeJobModal()">✕</button>
            </div>
            
            <div class="modal-meta">
                ${job.source ? `<span class="job-source">🌐 ${escapeHtml(job.source)}</span>` : ''}
                ${job.location ? `<span>📍 ${escapeHtml(job.location)}</span>` : ''}
                ${job.category ? `<span class="job-category">${escapeHtml(job.category)}</span>` : ''}
                ${job.salary_range ? `<span>💰 ${escapeHtml(job.salary_range)}</span>` : ''}
                ${job.job_type ? `<span>⏰ ${escapeHtml(job.job_type)}</span>` : ''}
            </div>
            
            <div class="modal-body">
                <h3>Job Description</h3>
                <div class="job-description-full">
                    ${descriptionHtml}
                </div>
                
                ${job.skills && job.skills.length > 0 ? `
                    <div class="modal-skills">
                        <h3>Required Skills</h3>
                        <div class="job-skills">
                            ${job.skills.map(skill => `<span class="skill-tag">${escapeHtml(skill)}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div class="modal-footer">
                <a href="${job.url}" target="_blank" class="btn btn-primary">View Original Post</a>
                <button onclick="closeJobModal()" class="btn btn-secondary">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
}

function closeJobModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.remove();
        document.body.style.overflow = 'auto';
    }
}

function updatePagination(data) {
    const pagination = document.getElementById('pagination');
    const totalPages = data.total_pages;
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    paginationHTML += `
        <button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">
            Previous
        </button>
    `;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="changePage(1)">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="page-btn">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">
                ${i}
            </button>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="page-btn">...</span>`;
        }
        paginationHTML += `<button class="page-btn" onclick="changePage(${totalPages})">${totalPages}</button>`;
    }
    
    // Next button
    paginationHTML += `
        <button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">
            Next
        </button>
    `;
    
    pagination.innerHTML = paginationHTML;
}

function changePage(page) {
    currentPage = page;
    loadJobs(page);
}

function handleSearch() {
    currentFilters = {
        search: document.getElementById('search-input').value,
        category: document.getElementById('category-filter').value,
        location: document.getElementById('location-filter').value
    };
    
    currentPage = 1;
    loadJobs();
}

async function handleManualScrape() {
    const button = document.getElementById('manual-scrape-btn');
    const originalText = button.textContent;
    
    button.disabled = true;
    button.innerHTML = '<span class="loading"></span> Scraping...';
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showSuccess(`Scraping completed! Found ${result.jobs_found} jobs, ${result.jobs_new} new.`);
            
            // Reload data
            await loadDashboardStats();
            await loadJobs();
        } else {
            showError(`Scraping failed: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Manual scrape error:', error);
        showError('Failed to start scraping');
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

// Chat functionality
function initializeChat() {
    addChatMessage('assistant', 'Hi! I\'m your AI job market analyst. Ask me anything about job trends, salary analysis, or market insights!');
}

function addChatMessage(sender, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    if (sender === 'assistant') {
        // Format AI responses with better styling
        messageDiv.innerHTML = formatAIResponse(message);
    } else {
        messageDiv.textContent = message;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
}

function formatAIResponse(text) {
    // Convert markdown-like formatting to HTML
    let html = escapeHtml(text);
    
    // Convert ### headers to h3
    html = html.replace(/### (.+?)(\n|$)/g, '<h3 class="ai-heading">$1</h3>');
    
    // Convert ** bold ** to strong
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert numbered lists (1. 2. 3.)
    html = html.replace(/(\n|^)(\d+)\.\s+\*\*(.+?)\*\*:/g, '$1<div class="ai-list-item"><span class="ai-number">$2.</span> <strong>$3:</strong>');
    html = html.replace(/(\n|^)(\d+)\.\s+(.+?)(\n|$)/g, '$1<div class="ai-list-item"><span class="ai-number">$2.</span> $3</div>$4');
    
    // Convert bullet points (- item)
    html = html.replace(/(\n|^)-\s+\*\*(.+?)\*\*:/g, '$1<div class="ai-bullet-item"><span class="ai-bullet">•</span> <strong>$2:</strong>');
    html = html.replace(/(\n|^)-\s+(.+?)(\n|$)/g, '$1<div class="ai-bullet-item"><span class="ai-bullet">•</span> $2</div>$3');
    
    // Convert line breaks to <br> but preserve divs
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n(?!<)/g, '<br>');
    
    // Wrap in container
    return `<div class="ai-response-content">${html}</div>`;
}

async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Add user message
    addChatMessage('user', message);
    chatInput.value = '';
    
    // Show loading
    const loadingMessage = addChatMessage('assistant', 'Analyzing your question...');
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: message })
        });
        
        const result = await response.json();
        
        // Remove loading message
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.removeChild(chatMessages.lastChild);
        
        if (result.error) {
            addChatMessage('assistant', `Sorry, I encountered an error: ${result.error}`);
        } else {
            addChatMessage('assistant', result.response);
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        
        // Remove loading message
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.removeChild(chatMessages.lastChild);
        
        addChatMessage('assistant', 'Sorry, I\'m having trouble connecting to the analysis service.');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    // Simple error display - could be enhanced with a proper notification system
    alert('Error: ' + message);
}

function showSuccess(message) {
    // Simple success display - could be enhanced with a proper notification system
    alert('Success: ' + message);
}
