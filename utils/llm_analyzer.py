import json
import logging
from typing import Dict, List, Optional, Any
from config import Config
import openai
from sqlalchemy import text
from database.connection import get_session
from database.models import Job, ScrapeLog

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """LLM-powered analyzer for natural language database queries."""
    
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            logger.warning("No OpenAI API key found. LLM analysis will be disabled.")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def analyze_query(self, user_question: str) -> Dict[str, Any]:
        """Process a natural language query and return analysis results."""
        if not self.client:
            return {"error": "LLM service not available"}
        
        try:
            # Generate SQL query from natural language
            sql_query = self._generate_sql_query(user_question)
            if not sql_query:
                return {"error": "Could not generate valid query"}
            
            # Execute query safely
            results = self._execute_safe_query(sql_query)
            
            # Generate natural language response
            response = self._generate_response(user_question, results)
            
            return {
                "question": user_question,
                "sql_query": sql_query,
                "data": results,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _generate_sql_query(self, question: str) -> Optional[str]:
        """Generate SQL query from natural language question."""
        try:
            # Get database schema information
            schema_info = self._get_schema_info()
            
            prompt = f"""
You are a SQL expert. Based on the following database schema and user question, generate a safe SQL query.

Database Schema:
{schema_info}

User Question: {question}

Rules:
1. Only use SELECT queries (no INSERT, UPDATE, DELETE)
2. Use parameterized queries where possible
3. Limit results to reasonable numbers (max 100 rows)
4. Include proper date filtering when relevant
5. Return valid SQL only, no explanations

Common patterns:
- "How many jobs" → COUNT queries
- "What are the trending" → GROUP BY with date ranges
- "Compare" → Multiple queries or complex aggregations
- "Show me" → SELECT with filters

Generate the SQL query:
"""
            
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate safe SELECT queries only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Basic validation
            if not sql_query.upper().startswith('SELECT'):
                logger.warning(f"Generated query doesn't start with SELECT: {sql_query}")
                return None
            
            # Check for dangerous keywords
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
            if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
                logger.warning(f"Generated query contains dangerous keywords: {sql_query}")
                return None
            
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return None
    
    def _get_schema_info(self) -> str:
        """Get database schema information for LLM."""
        return """
Tables:
1. jobs (id, external_id, title, company, location, salary_range, job_type, description, url, category, skills, first_seen_date, last_seen_date, is_active, created_at, updated_at)
2. job_snapshots (id, job_id, snapshot_date, field_changes, snapshot_data)
3. scrape_logs (id, source, timestamp, jobs_found, jobs_new, jobs_updated, jobs_removed, status, error_message, duration_seconds)

Common query patterns:
- Count jobs by category: SELECT category, COUNT(*) FROM jobs WHERE is_active = true GROUP BY category
- Jobs by date range: SELECT * FROM jobs WHERE created_at >= '2024-01-01' AND created_at <= '2024-12-31'
- Trending skills: SELECT skills, COUNT(*) FROM jobs WHERE skills IS NOT NULL GROUP BY skills ORDER BY COUNT(*) DESC
- Company analysis: SELECT company, COUNT(*) FROM jobs WHERE is_active = true GROUP BY company ORDER BY COUNT(*) DESC
"""
    
    def _execute_safe_query(self, sql_query: str) -> List[Dict]:
        """Execute SQL query safely and return results."""
        try:
            session = get_session()
            
            # Execute query
            result = session.execute(text(sql_query))
            
            # Convert to list of dictionaries
            columns = result.keys()
            rows = []
            
            for row in result:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # Handle datetime objects
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    # Handle JSON objects
                    elif isinstance(value, dict):
                        value = json.dumps(value)
                    row_dict[column] = value
                rows.append(row_dict)
            
            session.close()
            return rows
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def _generate_response(self, question: str, data: List[Dict]) -> str:
        """Generate natural language response from query results."""
        if not data:
            return "No data found matching your query."
        
        try:
            prompt = f"""
User asked: {question}

Query results (first 10 rows):
{json.dumps(data[:10], indent=2)}

Generate a natural language response that:
1. Directly answers the user's question
2. Includes key insights from the data
3. Mentions specific numbers and trends
4. Is conversational and helpful
5. Keeps response under 300 words

Response:
"""
            
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst. Provide clear, insightful responses about job market data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Found {len(data)} results. Here's a summary: {json.dumps(data[:3], indent=2)}"
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get key statistics for dashboard display."""
        try:
            session = get_session()
            
            # Total active jobs
            total_jobs = session.query(Job).filter(Job.is_active == True).count()
            
            # Jobs by category
            category_stats = session.query(Job.category, session.query(Job).filter(Job.category == Job.category, Job.is_active == True).count().label('count')).filter(Job.is_active == True).group_by(Job.category).all()
            
            # Recent activity
            recent_jobs = session.query(Job).filter(Job.created_at >= text("NOW() - INTERVAL '7 days'")).count()
            
            # Top companies
            top_companies = session.query(Job.company, session.query(Job).filter(Job.company == Job.company, Job.is_active == True).count().label('count')).filter(Job.is_active == True).group_by(Job.company).order_by(text('count DESC')).limit(10).all()
            
            session.close()
            
            return {
                "total_jobs": total_jobs,
                "category_stats": [{"category": cat, "count": count} for cat, count in category_stats],
                "recent_jobs": recent_jobs,
                "top_companies": [{"company": comp, "count": count} for comp, count in top_companies]
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {"error": "Failed to get statistics"}
