from datetime import datetime
import os
from supabase.client import create_client, Client
from typing import List, Optional
import traceback
import streamlit as st

class VideoSummary:
    def __init__(self, id: int, video_id: str, title: str, summary: str, 
                 language: str, timestamp: datetime, source_urls: str):
        self.id = id
        self.video_id = video_id
        self.title = title
        self.summary = summary
        self.language = language
        self.timestamp = timestamp
        self.source_urls = source_urls

class DatabaseHandler:
    def __init__(self):
        try:
            # Try getting credentials from environment variables first, then Streamlit secrets
            supabase_url = os.environ.get('SUPABASE_URL') or st.secrets.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY') or st.secrets.get('SUPABASE_KEY')
            
            if not supabase_url:
                st.error("Supabase URL not found in environment variables or secrets")
                raise ValueError("Missing SUPABASE_URL")
            
            if not supabase_key:
                st.error("Supabase API key not found in environment variables or secrets")
                raise ValueError("Missing SUPABASE_KEY")

            st.info("Initializing Supabase client...")
            st.info(f"Attempting to connect to Supabase URL: {supabase_url.split('@')[-1]}")  # Only show host part
            
            self.client = create_client(supabase_url, supabase_key)
            
            # Test connection with detailed error handling
            if not self.verify_connection():
                st.error("Failed to verify database connection")
                st.error("Please check your Supabase credentials and network connection")
                raise Exception("Database connection verification failed")
            
            st.success("Database connected successfully to Supabase")
            
        except ValueError as ve:
            st.error(f"Configuration error: {str(ve)}")
            st.error("Please ensure all required environment variables are set")
            raise
        except Exception as e:
            st.error(f"Database initialization error: {str(e)}")
            st.error(f"Stack trace:\n{traceback.format_exc()}")
            raise Exception(f"Failed to initialize Supabase connection: {str(e)}")

    def verify_connection(self) -> bool:
        """Verify database connection is active."""
        try:
            response = self.client.from_('video_summaries').select('id').limit(1).execute()
            if hasattr(response, 'data'):
                return True
            return False
        except Exception as e:
            st.error(f"Connection verification failed: {str(e)}")
            st.error(f"Stack trace:\n{traceback.format_exc()}")
            return False

    def save_summary(self, video_id: str, title: str, summary: str, 
                    language: str, source_urls: str) -> bool:
        """Save a video summary to the database."""
        try:
            if not self.verify_connection():
                st.error("Database connection is not active")
                raise Exception("Database connection is not active")
            
            data = {
                "video_id": video_id,
                "title": title,
                "summary": summary,
                "language": language,
                "source_urls": source_urls,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.client.from_('video_summaries').insert(data).execute()
            
            if hasattr(response, 'data') and response.data:
                st.success("Summary saved successfully to Supabase")
                return True
            else:
                st.error("Failed to save summary: No data returned from Supabase")
                return False
            
        except Exception as e:
            st.error(f"Error saving summary: {str(e)}")
            st.error(f"Stack trace:\n{traceback.format_exc()}")
            raise Exception(f"Database error: {str(e)}")

    def get_recent_summaries(self, limit: int = 5) -> List[VideoSummary]:
        """Get recent summaries from the database."""
        try:
            if not self.verify_connection():
                st.error("Database connection is not active")
                return []
            
            response = self.client.from_('video_summaries')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            if not hasattr(response, 'data'):
                st.error("No data attribute in Supabase response")
                return []
            
            return [
                VideoSummary(
                    id=item.get('id'),
                    video_id=item.get('video_id'),
                    title=item.get('title'),
                    summary=item.get('summary'),
                    language=item.get('language'),
                    timestamp=datetime.fromisoformat(item.get('timestamp')),
                    source_urls=item.get('source_urls')
                )
                for item in response.data
                if all(key in item for key in ['id', 'video_id', 'title', 'summary', 'language', 'timestamp', 'source_urls'])
            ]
            
        except Exception as e:
            st.error(f"Error in get_recent_summaries: {str(e)}")
            st.error(f"Stack trace:\n{traceback.format_exc()}")
            return []

    def get_summaries_by_language(self, language: str, 
                                limit: int = 5) -> List[VideoSummary]:
        """Get summaries filtered by language."""
        try:
            if not self.verify_connection():
                st.error("Database connection is not active")
                return []
            
            response = self.client.from_('video_summaries')\
                .select('*')\
                .eq('language', language)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            if not hasattr(response, 'data'):
                st.error("No data attribute in Supabase response")
                return []
            
            return [
                VideoSummary(
                    id=item.get('id'),
                    video_id=item.get('video_id'),
                    title=item.get('title'),
                    summary=item.get('summary'),
                    language=item.get('language'),
                    timestamp=datetime.fromisoformat(item.get('timestamp')),
                    source_urls=item.get('source_urls')
                )
                for item in response.data
                if all(key in item for key in ['id', 'video_id', 'title', 'summary', 'language', 'timestamp', 'source_urls'])
            ]
            
        except Exception as e:
            st.error(f"Error in get_summaries_by_language: {str(e)}")
            st.error(f"Stack trace:\n{traceback.format_exc()}")
            return []

    def __del__(self):
        """Cleanup."""
        self.client = None
