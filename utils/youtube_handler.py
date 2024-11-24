from typing import Dict, List
import google.api_core.exceptions
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import re

class YouTubeHandler:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError("Invalid YouTube URL")

    def get_video_details(self, video_id: str) -> Dict:
        """Get video title, description, and thumbnail."""
        try:
            response = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()

            if not response['items']:
                raise ValueError("Video not found")

            snippet = response['items'][0]['snippet']
            return {
                'title': snippet['title'],
                'description': snippet['description'],
                'channelId': snippet['channelId'],
                'thumbnail': snippet['thumbnails']['high']['url']  # 高解像度のサムネイルを取得
            }
        except google.api_core.exceptions.Error as e:
            raise Exception(f"YouTube API error: {str(e)}")

    def get_transcript(self, video_id: str) -> str:
        """Get video transcript."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ja', 'zh'])
            return " ".join([entry['text'] for entry in transcript_list])
        except Exception as e:
            raise Exception(f"Could not fetch transcript: {str(e)}")

    def get_channel_latest_videos(self, url: str, max_results: int = 5) -> List[Dict]:
        """Get latest videos from the same channel."""
        try:
            # まず動画のチャンネルIDを取得
            video_id = self.extract_video_id(url)
            video_details = self.get_video_details(video_id)
            channel_id = video_details['channelId']

            # チャンネルの最新動画を取得
            response = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                order='date',  # 日付順で並べ替え
                type='video',
                maxResults=max_results + 1  # 現在の動画も含まれる可能性があるため+1
            ).execute()

            latest_videos = []
            current_video_id = video_id.lower()  # 大文字小文字を区別しないように

            for item in response.get('items', []):
                if item['id']['kind'] == 'youtube#video':
                    # 現在の動画を除外
                    if item['id']['videoId'].lower() != current_video_id:
                        latest_videos.append({
                            'id': item['id']['videoId'],
                            'title': item['snippet']['title'],
                            'thumbnail': item['snippet']['thumbnails']['high']['url']  # 高解像度のサムネイルを使用
                        })
                        if len(latest_videos) >= max_results:
                            break

            if not latest_videos:
                raise Exception("No other videos found in this channel")

            return latest_videos

        except Exception as e:
            raise Exception(f"Error getting channel videos: {str(e)}")

    def process_videos(self, urls: List[str]) -> List[Dict]:
        """Process multiple YouTube videos."""
        results = []
        for url in urls:
            try:
                video_id = self.extract_video_id(url)
                details = self.get_video_details(video_id)
                transcript = self.get_transcript(video_id)

                results.append({
                    'url': url,
                    'video_id': video_id,
                    'title': details['title'],
                    'description': details['description'],
                    'thumbnail': details['thumbnail'],  # サムネイル情報を追加
                    'transcript': transcript
                })
            except Exception as e:
                results.append({
                    'url': url,
                    'error': str(e)
                })
        return results
