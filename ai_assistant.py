#!/usr/bin/env python3
"""
AI Assistant for Job Market Analysis
Uses OpenAI GPT to analyze job market data
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JobMarketAI:
    """AI Assistant that can query and analyze job market data"""
    
    def __init__(self, db_path='job_scraper.db', openai_api_key=None):
        self.db_path = db_path
        self.openai_api_key = openai_api_key
        
        # Initialize OpenAI client if key is provided
        if openai_api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=openai_api_key)
                self.enabled = True
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.warning("OpenAI library not installed. Run: pip install openai")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False
        else:
            logger.warning("No OpenAI API key provided")
            self.enabled = False
    
    def get_database_stats(self) -> Dict:
        """Get current database statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        stats = {}
        
        # Total jobs
        stats['total_jobs'] = cursor.execute(
            "SELECT COUNT(*) FROM jobs WHERE is_active = 1"
        ).fetchone()[0]
        
        # Jobs with descriptions
        stats['jobs_with_jd'] = cursor.execute(
            "SELECT COUNT(*) FROM jobs WHERE description != '' AND description IS NOT NULL AND is_active = 1"
        ).fetchone()[0]
        
        # Jobs by category
        category_data = cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM jobs 
            WHERE is_active = 1 
            GROUP BY category 
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()
        stats['categories'] = [dict(row) for row in category_data]
        
        # Jobs by source
        source_data = cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM jobs 
            WHERE is_active = 1 
            GROUP BY source
        """).fetchall()
        stats['sources'] = [dict(row) for row in source_data]
        
        # Recent jobs (last 7 days)
        stats['recent_jobs'] = cursor.execute("""
            SELECT COUNT(*) 
            FROM jobs 
            WHERE created_at >= datetime('now', '-7 days')
        """).fetchone()[0]
        
        # Top companies
        company_data = cursor.execute("""
            SELECT company, COUNT(*) as count 
            FROM jobs 
            WHERE is_active = 1 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 10
        """).fetchall()
        stats['top_companies'] = [dict(row) for row in company_data]
        
        conn.close()
        return stats
    
    def search_jobs(self, query: str, limit: int = 50) -> List[Dict]:
        """Search jobs in database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Search in title, company, description
        jobs = cursor.execute("""
            SELECT id, title, company, location, category, salary_range, 
                   description, source, created_at
            FROM jobs 
            WHERE is_active = 1 
              AND (title LIKE ? OR company LIKE ? OR description LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', limit)).fetchall()
        
        conn.close()
        return [dict(row) for row in jobs]
    
    def analyze_tech_trends(self) -> Dict:
        """Analyze technology trends in job descriptions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Common tech keywords to search
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C#', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
            'PostgreSQL', 'MongoDB', 'MySQL', 'Redis',
            'Machine Learning', 'AI', 'Data Science'
        ]
        
        tech_counts = {}
        for tech in tech_keywords:
            count = cursor.execute("""
                SELECT COUNT(*) 
                FROM jobs 
                WHERE description LIKE ? AND is_active = 1
            """, (f'%{tech}%',)).fetchone()[0]
            if count > 0:
                tech_counts[tech] = count
        
        conn.close()
        
        # Sort by count
        sorted_tech = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)
        return {
            'tech_counts': dict(sorted_tech[:20]),
            'total_jobs_analyzed': sum(tech_counts.values())
        }
    
    def get_context_for_query(self, user_query: str) -> str:
        """Get relevant database context for user query"""
        # Get general stats
        stats = self.get_database_stats()
        
        # Build context string
        context = f"""You are an AI assistant analyzing the New Zealand IT job market.

Current Database Statistics:
- Total Active Jobs: {stats['total_jobs']}
- Jobs with Full Descriptions: {stats['jobs_with_jd']}
- Recent Jobs (Last 7 Days): {stats['recent_jobs']}

Top Job Categories:
"""
        for cat in stats['categories'][:5]:
            context += f"- {cat['category']}: {cat['count']} jobs\n"
        
        context += "\nData Sources:\n"
        for src in stats['sources']:
            context += f"- {src['source']}: {src['count']} jobs\n"
        
        context += "\nTop Hiring Companies:\n"
        for comp in stats['top_companies'][:5]:
            context += f"- {comp['company']}: {comp['count']} jobs\n"
        
        # If query mentions specific keywords, search for relevant jobs
        search_keywords = ['python', 'java', 'react', 'aws', 'data', 'senior', 'junior']
        for keyword in search_keywords:
            if keyword.lower() in user_query.lower():
                jobs = self.search_jobs(keyword, limit=10)
                if jobs:
                    context += f"\nRecent {keyword.title()} Jobs:\n"
                    for job in jobs[:5]:
                        context += f"- {job['title']} at {job['company']} ({job['location']})\n"
                break
        
        # Add tech trends if query is about skills or technology
        if any(word in user_query.lower() for word in ['skill', 'tech', 'technology', 'trend', 'popular']):
            trends = self.analyze_tech_trends()
            context += "\nTop Technology Mentions:\n"
            for tech, count in list(trends['tech_counts'].items())[:10]:
                context += f"- {tech}: {count} jobs\n"
        
        return context
    
    def chat(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """
        Chat with AI assistant about job market data
        
        Args:
            user_message: User's question
            conversation_history: Previous messages in the conversation
            
        Returns:
            AI's response
        """
        if not self.enabled:
            return "❌ AI Assistant is not available. Please check OpenAI API key configuration."
        
        try:
            # Get relevant database context
            context = self.get_context_for_query(user_message)
            
            # Build messages for ChatGPT
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert AI assistant specializing in New Zealand IT job market analysis. 
You have access to real-time job market data and can provide insights on:
- Job trends and statistics
- Salary ranges and expectations
- Required skills and technologies
- Company hiring patterns
- Career advice for IT professionals

When answering:
1. Be specific and data-driven
2. Cite numbers from the database when available
3. Provide actionable insights
4. Be concise but thorough
5. Use emojis sparingly for better readability

Current database context will be provided with each query."""
                },
                {
                    "role": "user",
                    "content": f"Database Context:\n{context}\n\nUser Question: {user_message}"
                }
            ]
            
            # Add conversation history if provided
            if conversation_history:
                # Insert history before the current message
                messages = messages[:1] + conversation_history + messages[1:]
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4o-mini for cost efficiency
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            return answer
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return f"❌ Sorry, I encountered an error: {str(e)}"
    
    def generate_market_report(self) -> str:
        """Generate a comprehensive market analysis report"""
        if not self.enabled:
            return "AI Assistant is not available."
        
        stats = self.get_database_stats()
        trends = self.analyze_tech_trends()
        
        prompt = f"""Based on this New Zealand IT job market data, generate a comprehensive market analysis report:

Total Jobs: {stats['total_jobs']}
Recent Jobs (7 days): {stats['recent_jobs']}

Top Categories:
{json.dumps(stats['categories'][:5], indent=2)}

Top Technologies:
{json.dumps(list(trends['tech_counts'].items())[:10], indent=2)}

Top Companies:
{json.dumps(stats['top_companies'][:5], indent=2)}

Please provide:
1. Market Overview
2. Hot Job Categories
3. In-Demand Technologies
4. Hiring Trends
5. Recommendations for Job Seekers
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert IT job market analyst for New Zealand."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {str(e)}"


def main():
    """Test the AI assistant"""
    import os
    
    # Get API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY', '')
    
    ai = JobMarketAI(openai_api_key=api_key)
    
    if not ai.enabled:
        print("❌ AI Assistant not available")
        return
    
    print("🤖 NZ IT Job Market AI Assistant")
    print("=" * 60)
    
    # Test questions
    questions = [
        "How many Python jobs are currently available?",
        "What are the most in-demand technologies?",
        "Which companies are hiring the most?",
    ]
    
    for question in questions:
        print(f"\n❓ {question}")
        print("-" * 60)
        answer = ai.chat(question)
        print(answer)
        print()


if __name__ == '__main__':
    main()

