import json
import logging
from typing import Dict, List, Optional
from config import Config
import openai

logger = logging.getLogger(__name__)

class JobClassifier:
    """LLM-based job classifier for categorizing IT positions."""
    
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            logger.warning("No OpenAI API key found. Job classification will be disabled.")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def classify_job(self, job_data: Dict) -> Dict:
        """Classify a job into categories and extract skills."""
        if not self.client:
            return self._fallback_classification(job_data)
        
        try:
            # Prepare job information for classification
            job_text = self._prepare_job_text(job_data)
            
            # Create classification prompt
            prompt = self._create_classification_prompt(job_text)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert job classifier for IT positions. Analyze job postings and categorize them accurately."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=0.1
            )
            
            # Parse response
            result = self._parse_classification_response(response.choices[0].message.content)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in job classification: {e}")
            return self._fallback_classification(job_data)
    
    def _prepare_job_text(self, job_data: Dict) -> str:
        """Prepare job data for classification."""
        parts = []
        
        if job_data.get('title'):
            parts.append(f"Title: {job_data['title']}")
        
        if job_data.get('company'):
            parts.append(f"Company: {job_data['company']}")
        
        if job_data.get('description'):
            # Truncate description if too long
            description = job_data['description']
            if len(description) > 2000:
                description = description[:2000] + "..."
            parts.append(f"Description: {description}")
        
        return "\n\n".join(parts)
    
    def _create_classification_prompt(self, job_text: str) -> str:
        """Create prompt for job classification."""
        categories = ", ".join(Config.JOB_CATEGORIES)
        
        prompt = f"""
Please analyze the following job posting and provide a JSON response with:

1. **category**: The most appropriate category from this list: {categories}
2. **confidence**: A number between 0-100 indicating confidence in the classification
3. **skills**: An array of key technical skills mentioned (programming languages, frameworks, tools, etc.)
4. **technologies**: An array of specific technologies mentioned
5. **experience_level**: "entry", "mid", "senior", or "lead" based on requirements
6. **salary_indicator**: "low", "medium", "high", or "not_specified" based on salary range if available

Job posting:
{job_text}

Respond with valid JSON only, no additional text.
"""
        return prompt
    
    def _parse_classification_response(self, response: str) -> Dict:
        """Parse LLM response into structured data."""
        try:
            # Clean response and extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            result = json.loads(response)
            
            # Validate and set defaults
            return {
                'category': result.get('category', 'Other IT roles'),
                'confidence': min(max(result.get('confidence', 50), 0), 100),
                'skills': result.get('skills', []),
                'technologies': result.get('technologies', []),
                'experience_level': result.get('experience_level', 'mid'),
                'salary_indicator': result.get('salary_indicator', 'not_specified')
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse classification response: {e}")
            return self._fallback_classification({})
    
    def _fallback_classification(self, job_data: Dict) -> Dict:
        """Fallback classification using keyword matching."""
        title = (job_data.get('title', '') + ' ' + job_data.get('description', '')).lower()
        
        # Simple keyword-based classification
        category = 'Other IT roles'
        confidence = 30
        
        if any(word in title for word in ['developer', 'programmer', 'engineer', 'coder']):
            if any(word in title for word in ['frontend', 'front-end', 'react', 'angular', 'vue']):
                category = 'Software Developer (Frontend)'
                confidence = 60
            elif any(word in title for word in ['backend', 'back-end', 'api', 'server']):
                category = 'Software Developer (Backend)'
                confidence = 60
            else:
                category = 'Software Developer (Full-stack)'
                confidence = 50
        
        elif any(word in title for word in ['data analyst', 'data scientist', 'analytics']):
            if any(word in title for word in ['data engineer', 'etl', 'pipeline']):
                category = 'Data Engineer'
            else:
                category = 'Data Analyst'
            confidence = 70
        
        elif any(word in title for word in ['devops', 'cloud', 'aws', 'azure', 'docker', 'kubernetes']):
            category = 'DevOps Engineer'
            confidence = 70
        
        elif any(word in title for word in ['qa', 'test', 'testing', 'quality']):
            category = 'QA Engineer'
            confidence = 70
        
        elif any(word in title for word in ['security', 'cyber', 'pentest']):
            category = 'Security Engineer'
            confidence = 70
        
        elif any(word in title for word in ['support', 'admin', 'system administrator']):
            category = 'IT Support'
            confidence = 60
        
        elif any(word in title for word in ['product manager', 'project manager']):
            category = 'Product Manager'
            confidence = 60
        
        # Extract skills using simple keyword matching
        skills = []
        skill_keywords = {
            'Python': ['python', 'django', 'flask', 'pandas', 'numpy'],
            'JavaScript': ['javascript', 'js', 'node', 'react', 'angular', 'vue'],
            'Java': ['java', 'spring', 'hibernate'],
            'C#': ['c#', 'csharp', '.net', 'dotnet'],
            'SQL': ['sql', 'mysql', 'postgresql', 'oracle'],
            'AWS': ['aws', 'amazon web services'],
            'Docker': ['docker', 'container'],
            'Kubernetes': ['kubernetes', 'k8s'],
            'Git': ['git', 'github', 'gitlab']
        }
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in title for keyword in keywords):
                skills.append(skill)
        
        return {
            'category': category,
            'confidence': confidence,
            'skills': skills,
            'technologies': [],
            'experience_level': 'mid',
            'salary_indicator': 'not_specified'
        }
    
    def batch_classify(self, jobs: List[Dict]) -> List[Dict]:
        """Classify multiple jobs efficiently."""
        results = []
        
        for job in jobs:
            classification = self.classify_job(job)
            
            # Merge classification results with job data
            enhanced_job = {**job, **classification}
            results.append(enhanced_job)
        
        return results
