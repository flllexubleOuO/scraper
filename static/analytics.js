// Analytics页面的JavaScript逻辑

// 视图切换
document.addEventListener('DOMContentLoaded', function() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const views = {
        'dashboard': document.getElementById('dashboard-view'),
        'analytics': document.getElementById('analytics-view'),
        'ai': document.getElementById('ai-view')
    };
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const targetView = this.getAttribute('data-view');
            
            // 更新按钮状态
            navButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 切换视图
            Object.keys(views).forEach(key => {
                views[key].style.display = key === targetView ? 'block' : 'none';
            });
            
            // 如果切换到Analytics视图，加载数据
            if (targetView === 'analytics') {
                loadAnalytics();
            }
        });
    });
    
    // 刷新按钮
    const refreshBtn = document.getElementById('refresh-analytics-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadAnalytics);
    }
});

// 加载Analytics数据
async function loadAnalytics() {
    try {
        // 并行加载所有数据
        const [techStack, trends, experienceLevels, workTypes] = await Promise.all([
            fetch('/api/analytics/tech-stack').then(r => r.json()),
            fetch('/api/analytics/trends').then(r => r.json()),
            fetch('/api/analytics/experience-levels').then(r => r.json()),
            fetch('/api/analytics/work-types').then(r => r.json())
        ]);
        
        // 渲染图表
        renderTechStackCharts(techStack);
        renderTrendsChart(trends);
        renderExperienceChart(experienceLevels);
        renderWorkTypeChart(workTypes);
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        alert('Failed to load analytics data. Please run: python3 enrich_job_data.py');
    }
}

// 渲染技术栈图表
function renderTechStackCharts(data) {
    const categories = [
        { key: 'programming_languages', id: 'languages-chart', color: '#3b82f6' },
        { key: 'frontend', id: 'frontend-chart', color: '#10b981' },
        { key: 'backend', id: 'backend-chart', color: '#f59e0b' },
        { key: 'cloud', id: 'cloud-chart', color: '#8b5cf6' },
        { key: 'database', id: 'database-chart', color: '#ef4444' },
        { key: 'devops', id: 'devops-chart', color: '#06b6d4' }
    ];
    
    categories.forEach(cat => {
        const canvas = document.getElementById(cat.id);
        if (!canvas) return;
        
        const skills = data[cat.key] || [];
        if (skills.length === 0) {
            canvas.parentElement.innerHTML += '<p class="no-data">No data available. Run enrich_job_data.py first.</p>';
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // 销毁旧图表
        if (canvas.chart) {
            canvas.chart.destroy();
        }
        
        canvas.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: skills.map(s => s.name),
                datasets: [{
                    label: 'Job Count',
                    data: skills.map(s => s.count),
                    backgroundColor: cat.color,
                    borderColor: cat.color,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    });
}

// 渲染趋势图
function renderTrendsChart(data) {
    const canvas = document.getElementById('trends-chart');
    if (!canvas) return;
    
    const trends = data.trends || [];
    if (trends.length === 0) return;
    
    // 提取所有来源
    const sources = new Set();
    trends.forEach(t => {
        Object.keys(t.counts).forEach(source => sources.add(source));
    });
    
    // 准备数据集
    const datasets = Array.from(sources).map((source, idx) => {
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
        return {
            label: source.charAt(0).toUpperCase() + source.slice(1),
            data: trends.map(t => t.counts[source] || 0),
            borderColor: colors[idx % colors.length],
            backgroundColor: colors[idx % colors.length] + '20',
            borderWidth: 2,
            fill: true
        };
    });
    
    const ctx = canvas.getContext('2d');
    
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    canvas.chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trends.map(t => t.date),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// 渲染经验等级图表
function renderExperienceChart(data) {
    const canvas = document.getElementById('experience-chart');
    if (!canvas) return;
    
    const levels = data.levels || [];
    if (levels.length === 0) return;
    
    const ctx = canvas.getContext('2d');
    
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    canvas.chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: levels.map(l => l.level.charAt(0).toUpperCase() + l.level.slice(1)),
            datasets: [{
                data: levels.map(l => l.count),
                backgroundColor: [
                    '#3b82f6',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// 渲染工作类型图表
function renderWorkTypeChart(data) {
    const canvas = document.getElementById('worktype-chart');
    if (!canvas) return;
    
    const types = data.work_types || [];
    if (types.length === 0) return;
    
    const ctx = canvas.getContext('2d');
    
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    canvas.chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: types.map(t => t.type.charAt(0).toUpperCase() + t.type.slice(1)),
            datasets: [{
                data: types.map(t => t.count),
                backgroundColor: [
                    '#3b82f6',
                    '#10b981',
                    '#f59e0b'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

