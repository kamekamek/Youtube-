import streamlit as st
import os
from utils import YouTubeHandler, GeminiProcessor
from utils.db_handler import DatabaseHandler
from datetime import datetime

# Translations dictionary
TRANSLATIONS = {
    'ja': {
        'page_title': '要約ジェネレーター',
        'app_description': '複数のYouTube動画をAIを使用して包括的な要約に変換します。\n以下にYouTube動画のURLを入力してください。',
        'url_input_label': 'YouTubeのURL（1行に1つ）',
        'url_input_help': 'YouTubeのURLを1行に1つずつ貼り付けてください',
        'generate_button': '要約を生成',
        'invalid_urls': '有効なYouTube URLを入力してください',
        'processing_videos': '動画を処理中...',
        'generating_article': '要約を生成中...',
        'error_occurred': 'エラーが発生しました：',
        'error_processing': '処理中にエラーが発生しました ',
        'generated_article': '生成された要約',
        'sources': 'ソース',
        'language_selector': '言語を選択',
        'recommendations': 'おすすめの動画',
        'recent_summaries': '最近の要約',
        'view_history': '履歴を表示'
    },
    'en': {
        'page_title': 'Summary Generator',
        'app_description': 'Transform multiple YouTube videos into a comprehensive summary using AI.\nEnter YouTube video URLs (one per line) below.',
        'url_input_label': 'Enter YouTube URLs (one per line)',
        'url_input_help': 'Paste YouTube URLs, one per line',
        'generate_button': 'Generate Summary',
        'invalid_urls': 'Please enter valid YouTube URLs',
        'processing_videos': 'Processing videos...',
        'generating_article': 'Generating summary...',
        'error_occurred': 'An error occurred: ',
        'error_processing': 'Error processing ',
        'generated_article': 'Generated Summary',
        'sources': 'Sources',
        'language_selector': 'Select Language',
        'recommendations': 'Recommended Videos',
        'recent_summaries': 'Recent Summaries',
        'view_history': 'View History'
    },
    'zh': {
        'page_title': '摘要生成器',
        'app_description': '使用AI将多个YouTube视频转换为综合摘要。\n在下方输入YouTube视频URL（每行一个）。',
        'url_input_label': '输入YouTube URL（每行一个）',
        'url_input_help': '粘贴YouTube URL，每行一个',
        'generate_button': '生成摘要',
        'invalid_urls': '请输入有效的YouTube URL',
        'processing_videos': '正在处理视频...',
        'generating_article': '正在生成摘要...',
        'error_occurred': '发生错误：',
        'error_processing': '处理出错 ',
        'generated_article': '生成的摘要',
        'sources': '来源',
        'language_selector': '选择语言',
        'recommendations': '推荐视频',
        'recent_summaries': '最近的摘要',
        'view_history': '查看历史'
    }
}

# Page configuration
st.set_page_config(
    page_title="Summary Generator",
    page_icon="📝",
    layout="wide"
)

# Load custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'generated_article' not in st.session_state:
        st.session_state.generated_article = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'language' not in st.session_state:
        st.session_state.language = 'ja'  # Default to Japanese
    if 'db_handler' not in st.session_state:
        st.session_state.db_handler = DatabaseHandler()

def validate_urls(urls: list) -> list:
    """Validate YouTube URLs."""
    valid_urls = []
    for url in urls:
        if url.strip() and ('youtube.com' in url or 'youtu.be' in url):
            valid_urls.append(url.strip())
    return valid_urls

def get_text(key: str) -> str:
    """Get translated text based on current language."""
    return TRANSLATIONS[st.session_state.language][key]

def display_recent_summaries():
    """Display recent summaries from the database."""
    summaries = st.session_state.db_handler.get_summaries_by_language(
        st.session_state.language
    )
    if summaries:
        st.markdown(f"### {get_text('recent_summaries')}")
        for summary in summaries:
            with st.expander(f"{summary.title} - {summary.timestamp.strftime('%Y-%m-%d %H:%M')}"):
                st.markdown(summary.summary)
                st.markdown("**Sources:**")
                for url in summary.source_urls.split(','):
                    st.markdown(f'<a href="{url.strip()}" target="_blank">{url.strip()}</a>', 
                              unsafe_allow_html=True)

def main():
    initialize_session_state()
    
    # Language selector
    st.selectbox(
        get_text('language_selector'),
        options=['ja', 'en', 'zh'],
        index=['ja', 'en', 'zh'].index(st.session_state.language),
        format_func=lambda x: '日本語' if x == 'ja' else 'English' if x == 'en' else '中文',
        key='language'
    )
    
    st.title(f"📝 {get_text('page_title')}")
    st.markdown(get_text('app_description'))

    # Input area for YouTube URLs
    urls_input = st.text_area(
        get_text('url_input_label'),
        height=150,
        help=get_text('url_input_help')
    )

    col1, col2 = st.columns([2, 1])

    # Process button
    if col1.button(get_text('generate_button'), disabled=st.session_state.processing):
        urls = urls_input.split('\n')
        valid_urls = validate_urls(urls)

        if not valid_urls:
            st.error(get_text('invalid_urls'))
            return

        try:
            st.session_state.processing = True

            # Initialize handlers with environment variables
            youtube_handler = YouTubeHandler(api_key=os.environ['YOUTUBE_API_KEY'])
            gemini_processor = GeminiProcessor(api_key=os.environ['GEMINI_API_KEY'])

            # Process videos
            with st.spinner(get_text('processing_videos')):
                video_data = youtube_handler.process_videos(valid_urls)

            # Check for errors
            errors = [data for data in video_data if 'error' in data]
            if errors:
                for error in errors:
                    st.error(f"{get_text('error_processing')}{error['url']}: {error['error']}")
                if len(errors) == len(video_data):
                    return

            # Generate article
            with st.spinner(get_text('generating_article')):
                article = gemini_processor.generate_article(
                    video_data, 
                    language=st.session_state.language
                )
                st.session_state.generated_article = article

                # Save to database
                if len(video_data) > 0 and 'error' not in video_data[0]:
                    st.session_state.db_handler.save_summary(
                        video_id=youtube_handler.extract_video_id(valid_urls[0]),
                        title=video_data[0]['title'],
                        summary=article,
                        language=st.session_state.language,
                        source_urls=','.join(valid_urls)
                    )

                # Get video recommendations
                recommendations = youtube_handler.get_recommendations(valid_urls[0])
                st.session_state.recommendations = recommendations

        except Exception as e:
            st.error(f"{get_text('error_occurred')}{str(e)}")
        finally:
            st.session_state.processing = False

    # Display recent summaries in sidebar
    with st.sidebar:
        display_recent_summaries()

    # Display generated article
    if st.session_state.generated_article:
        st.markdown(f"### {get_text('generated_article')}")
        st.markdown('<div class="article-container">', unsafe_allow_html=True)
        st.markdown(st.session_state.generated_article)
        st.markdown('</div>', unsafe_allow_html=True)

        # Source attribution
        st.markdown(f"### {get_text('sources')}")
        for url in validate_urls(urls_input.split('\n')):
            st.markdown(f'<a href="{url}" class="source-link" target="_blank">{url}</a>', 
                       unsafe_allow_html=True)
        
        # Display recommendations
        if hasattr(st.session_state, 'recommendations'):
            st.markdown(f"### {get_text('recommendations')}")
            for video in st.session_state.recommendations:
                st.markdown(
                    f'<a href="https://youtube.com/watch?v={video["id"]}" class="video-recommendation" target="_blank">'
                    f'<img src="{video["thumbnail"]}" style="width:120px;margin-right:10px;">'
                    f'{video["title"]}</a>',
                    unsafe_allow_html=True
                )

if __name__ == "__main__":
    main()
