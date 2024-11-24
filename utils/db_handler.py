from datetime import datetime
import os
from supabase.client import create_client, Client
from typing import List, Optional, Tuple
import traceback
import streamlit as st

class VideoSummary:
    def __init__(self, id: int, video_id: str, title: str, summary: str, 
                 language: str, timestamp: datetime, source_urls: str,
                 thumbnail_url: str = None):
        self.id = id
        self.video_id = video_id
        self.title = title
        self.summary = summary
        self.language = language
        self.timestamp = timestamp
        self.source_urls = source_urls
        self.thumbnail_url = thumbnail_url

class DatabaseHandler:
    def __init__(self):
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')

            if not supabase_url or not supabase_key:
                st.error("Supabase credentials not found in environment variables")
                raise ValueError("Supabase credentials not found in environment variables")

            st.info("Initializing Supabase client...")
            self.client = create_client(supabase_url, supabase_key)

            # Test connection
            if not self.verify_connection():
                st.error("Failed to verify database connection")
                raise Exception("Database connection verification failed")

            st.success("Database connected successfully")

        except Exception as e:
            st.error(f"Database initialization error: {str(e)}")
            st.error(f"Stack trace: {traceback.format_exc()}")
            raise Exception(f"Failed to initialize database connection: {str(e)}")

    def verify_connection(self) -> bool:
        """Verify database connection is active."""
        try:
            # Use from_ instead of table for Supabase client
            response = self.client.from_('video_summaries').select('id').limit(1).execute()
            return True
        except Exception as e:
            st.error(f"Connection verification failed: {str(e)}")
            st.error(f"Stack trace: {traceback.format_exc()}")
            return False

    def save_summary(self, video_id: str, title: str, summary: str, 
                    language: str, source_urls: str, thumbnail_url: str = None) -> bool:
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
                "thumbnail_url": thumbnail_url,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Use from_ instead of table for Supabase client
            response = self.client.from_('video_summaries').insert(data).execute()
            return True

        except Exception as e:
            st.error(f"Error saving summary: {str(e)}")
            st.error(f"Stack trace: {traceback.format_exc()}")
            raise Exception(f"Database error: {str(e)}")

    def get_recent_summaries(self, limit: int = 10) -> List[VideoSummary]:
        """Get recent summaries from the database."""
        try:
            if not self.verify_connection():
                st.error("Database connection is not active")
                return []

            # Use from_ instead of table for Supabase client
            response = self.client.from_('video_summaries')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()

            return [
                VideoSummary(
                    id=item['id'],
                    video_id=item['video_id'],
                    title=item['title'],
                    summary=item['summary'],
                    language=item['language'],
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    source_urls=item['source_urls'],
                    thumbnail_url=item.get('thumbnail_url')
                )
                for item in response.data
            ] if response.data else []

        except Exception as e:
            st.error(f"Error in get_recent_summaries: {str(e)}")
            return []

    def get_summaries_by_language(self, language: str, 
                                limit: int = 10) -> List[VideoSummary]:
        """Get summaries filtered by language."""
        try:
            if not self.verify_connection():
                st.error("Database connection is not active")
                return []

            # Use from_ instead of table for Supabase client
            response = self.client.from_('video_summaries')\
                .select('*')\
                .eq('language', language)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()

            return [
                VideoSummary(
                    id=item['id'],
                    video_id=item['video_id'],
                    title=item['title'],
                    summary=item['summary'],
                    language=item['language'],
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    source_urls=item['source_urls'],
                    thumbnail_url=item.get('thumbnail_url')
                )
                for item in response.data
            ] if response.data else []

        except Exception as e:
            st.error(f"Error in get_summaries_by_language: {str(e)}")
            return []

    def delete_summary(self, summary_id: int) -> Tuple[bool, str]:
        """Delete a summary from the database.

        Args:
            summary_id: The ID of the summary to delete

        Returns:
            Tuple[bool, str]: (Success status, Message)
        """
        try:
            if not self.verify_connection():
                return False, "Database connection is not active"

            # First verify the summary exists
            response = self.client.from_('video_summaries')\
                .select('id')\
                .eq('id', summary_id)\
                .execute()

            if not response.data:
                return False, "Summary not found"

            # Delete the summary
            response = self.client.from_('video_summaries')\
                .delete()\
                .eq('id', summary_id)\
                .execute()

            return True, "Summary deleted successfully"

        except Exception as e:
            error_msg = f"Error deleting summary: {str(e)}"
            st.error(error_msg)
            st.error(f"Stack trace: {traceback.format_exc()}")
            return False, error_msg

    def __del__(self):
        """Cleanup."""
        pass
