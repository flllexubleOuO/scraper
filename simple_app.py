#!/usr/bin/env python3
"""
Simplified Flask app without SQLAlchemy dependencies for testing.
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import logging
from datetime import datetime
from ai_assistant import JobMarketAI

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI Assistant
import os
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # 从环境变量读取
ai_assistant = JobMarketAI(db_path='job_scraper.db', openai_api_key=OPENAI_API_KEY)
logger.info(f"AI Assistant enabled: {ai_assistant.enabled}")

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('job_scraper.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables."""
    conn = get_db_connection()
    
    # Create jobs table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary_range TEXT,
            job_type TEXT,
            description TEXT,
            url TEXT,
            category TEXT,
            skills TEXT,
            first_seen_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create job_snapshots table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS job_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            field_changes TEXT,
            snapshot_data TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')
    
    # Create scrape_logs table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS scrape_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            jobs_found INTEGER DEFAULT 0,
            jobs_new INTEGER DEFAULT 0,
            jobs_updated INTEGER DEFAULT 0,
            jobs_removed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'success',
            error_message TEXT,
            duration_seconds REAL
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/jobs')
def get_jobs():
    """Get jobs with filtering and pagination."""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        category = request.args.get('category', '')
        location = request.args.get('location', '')
        search = request.args.get('search', '')
        source = request.args.get('source', '')  # Add source filter
        
        conn = get_db_connection()
        
        # Build query
        where_conditions = ["is_active = 1"]
        params = []
        
        if category:
            where_conditions.append("category = ?")
            params.append(category)
        
        if location:
            where_conditions.append("location LIKE ?")
            params.append(f'%{location}%')
        
        if source:
            where_conditions.append("source = ?")
            params.append(source)
        
        if search:
            where_conditions.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        where_clause = " AND ".join(where_conditions)
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM jobs WHERE {where_clause}"
        total = conn.execute(count_query, params).fetchone()[0]
        
        # Get jobs with pagination (新工作排在前面)
        offset = (page - 1) * per_page
        jobs_query = f"""
            SELECT * FROM jobs 
            WHERE {where_clause}
            ORDER BY is_new_today DESC, created_at DESC 
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        
        jobs = conn.execute(jobs_query, params).fetchall()
        
        # Convert to list of dictionaries
        job_list = []
        for job in jobs:
            job_dict = {
                'id': job['id'],
                'title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'salary_range': job['salary_range'],
                'job_type': job['job_type'],
                'category': job['category'],
                'skills': json.loads(job['skills']) if job['skills'] else [],
                'url': job['url'],
                'source': job['source'] if 'source' in job.keys() else 'seek',
                'is_new_today': job['is_new_today'] if 'is_new_today' in job.keys() else 0,  # 新增字段
                'created_at': job['created_at'],
                'description': job['description'][:500] + '...' if job['description'] and len(job['description']) > 500 else job['description']
            }
            job_list.append(job_dict)
        
        conn.close()
        
        return jsonify({
            'jobs': job_list,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<int:job_id>')
def get_job_detail(job_id):
    """Get full details of a specific job including complete description."""
    try:
        conn = get_db_connection()
        
        job = conn.execute("""
            SELECT * FROM jobs WHERE id = ?
        """, (job_id,)).fetchone()
        
        if not job:
            conn.close()
            return jsonify({'error': 'Job not found'}), 404
        
        job_dict = {
            'id': job['id'],
            'external_id': job['external_id'],
            'title': job['title'],
            'company': job['company'],
            'location': job['location'],
            'salary_range': job['salary_range'],
            'job_type': job['job_type'],
            'category': job['category'],
            'skills': json.loads(job['skills']) if job['skills'] else [],
            'url': job['url'],
            'source': job['source'] if 'source' in job.keys() else 'seek',
            'description': job['description'],  # Full description, not truncated
            'first_seen_date': job['first_seen_date'],
            'last_seen_date': job['last_seen_date'],
            'is_active': job['is_active'],
            'created_at': job['created_at'],
            'updated_at': job['updated_at']
        }
        
        conn.close()
        
        return jsonify(job_dict)
        
    except Exception as e:
        logger.error(f"Error getting job detail: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories')
def get_categories():
    """Get list of job categories."""
    try:
        conn = get_db_connection()
        categories = conn.execute("""
            SELECT DISTINCT category 
            FROM jobs 
            WHERE category IS NOT NULL AND is_active = 1
        """).fetchall()
        
        category_list = [cat['category'] for cat in categories if cat['category']]
        conn.close()
        
        return jsonify({'categories': category_list})
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/locations')
def get_locations():
    """Get list of job locations."""
    try:
        conn = get_db_connection()
        locations = conn.execute("""
            SELECT DISTINCT location 
            FROM jobs 
            WHERE location IS NOT NULL AND is_active = 1
        """).fetchall()
        
        location_list = [loc['location'] for loc in locations if loc['location']]
        conn.close()
        
        return jsonify({'locations': location_list})
        
    except Exception as e:
        logger.error(f"Error getting locations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    try:
        conn = get_db_connection()
        
        # Total active jobs
        total_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE is_active = 1").fetchone()[0]
        
        # Jobs by category
        category_stats = conn.execute("""
            SELECT category, COUNT(*) as count 
            FROM jobs 
            WHERE is_active = 1 
            GROUP BY category 
            ORDER BY count DESC
        """).fetchall()
        
        # Recent activity
        recent_jobs = conn.execute("""
            SELECT COUNT(*) 
            FROM jobs 
            WHERE created_at >= datetime('now', '-7 days')
        """).fetchone()[0]
        
        # Top companies
        top_companies = conn.execute("""
            SELECT company, COUNT(*) as count 
            FROM jobs 
            WHERE is_active = 1 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 10
        """).fetchall()
        
        # Jobs by source
        source_stats = conn.execute("""
            SELECT source, COUNT(*) as count 
            FROM jobs 
            WHERE is_active = 1 
            GROUP BY source 
            ORDER BY count DESC
        """).fetchall()
        
        conn.close()
        
        return jsonify({
            "total_jobs": total_jobs,
            "category_stats": [{"category": cat['category'], "count": cat['count']} for cat in category_stats],
            "source_stats": [{"source": src['source'], "count": src['count']} for src in source_stats],
            "recent_jobs": recent_jobs,
            "top_companies": [{"company": comp['company'], "count": comp['count']} for comp in top_companies]
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_query():
    """AI-powered analysis endpoint using ChatGPT."""
    try:
        data = request.get_json()
        question = data.get('question', '')
        conversation_history = data.get('history', [])
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Check if AI is enabled
        if not ai_assistant.enabled:
            # Fallback to simple responses if AI not available
            return jsonify({
                "question": question,
                "response": "⚠️ AI Assistant is not available. Please ensure OpenAI library is installed (pip install openai) and API key is valid.",
                "ai_enabled": False
            })
        
        # Use AI to answer the question
        logger.info(f"AI Query: {question}")
        answer = ai_assistant.chat(question, conversation_history)
        
        return jsonify({
            "question": question,
            "response": answer,
            "ai_enabled": True
        })
        
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        return jsonify({
            'error': str(e),
            'response': f"❌ Error: {str(e)}"
        }), 500

@app.route('/api/market-report')
def generate_market_report():
    """Generate AI-powered market analysis report."""
    try:
        if not ai_assistant.enabled:
            return jsonify({
                'error': 'AI Assistant not available',
                'report': 'Please configure OpenAI API key'
            }), 503
        
        logger.info("Generating AI market report...")
        report = ai_assistant.generate_market_report()
        
        return jsonify({
            'report': report,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
def manual_scrape():
    """Trigger manual scraping."""
    return jsonify({
        'status': 'info',
        'message': 'Manual scraping is not available in this simplified version. Use the test_scraper.py script instead.'
    })

@app.route('/api/scheduler/status')
def scheduler_status():
    """Get scheduler status."""
    return jsonify({
        'is_running': False,
        'next_run': None,
        'scheduled_jobs': 0
    })

@app.route('/api/scrape-history')
def get_scrape_history():
    """Get scraping history."""
    try:
        conn = get_db_connection()
        logs = conn.execute("""
            SELECT * FROM scrape_logs 
            ORDER BY timestamp DESC 
            LIMIT 50
        """).fetchall()
        
        history = []
        for log in logs:
            history.append({
                'id': log['id'],
                'source': log['source'],
                'timestamp': log['timestamp'],
                'status': log['status'],
                'jobs_found': log['jobs_found'],
                'jobs_new': log['jobs_new'],
                'jobs_updated': log['jobs_updated'],
                'duration_seconds': log['duration_seconds'],
                'error_message': log['error_message']
            })
        
        conn.close()
        return jsonify({'history': history})
        
    except Exception as e:
        logger.error(f"Error getting scrape history: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run the Flask app
    logger.info("Starting simplified Flask app...")
    app.run(debug=True, host='0.0.0.0', port=8080)
