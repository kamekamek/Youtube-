import streamlit as st
import os
from utils.db_handler import DatabaseHandler
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Translations dictionary
TRANSLATIONS = {
    'ja': {
        'page_title': '要約履歴',
        'language_selector': '言語を選択',
        'no_summaries': '保存された要約はまだありません',
        'delete_button': '削除',
        'delete_confirm': 'この要約を削除してもよろしいですか？',
        'delete_success': '要約を削除しました',
        'delete_error': '削除中にエラーが発生しました：',
        'cancel_button': 'キャンセル',
        'summary_date_format': '%Y年%m月%d日 %H:%M',
        'db_error': 'データベースエラーが発生しました：',
        'loading': '読み込み中...',
        'view_video': '動画を見る',
        'summary_label': '要約：'
    },
    'en': {
        'page_title': 'Summary History',
        'language_selector': 'Select Language',
        'no_summaries': 'No saved summaries yet',
        'delete_button': 'Delete',
        'delete_confirm': 'Are you sure you want to delete this summary?',
        'delete_success': 'Summary deleted successfully',
        'delete_error': 'Error deleting summary: ',
        'cancel_button': 'Cancel',
        'summary_date_format': '%Y-%m-%d %H:%M',
        'db_error': 'Database error occurred: ',
        'loading': 'Loading...',
        'view_video': 'Watch Video',
        'summary_label': 'Summary:'
    },
    'zh': {
        'page_title': '摘要历史',
        'language_selector': '选择语言',
        'no_summaries': '暂无保存的摘要',
        'delete_button': '删除',
        'delete_confirm': '确定要删除这个摘要吗？',
        'delete_success': '摘要删除成功',
        'delete_error': '删除摘要时出错：',
        'cancel_button': '取消',
        'summary_date_format': '%Y年%m月%d日 %H:%M',
        'db_error': '数据库错误：',
        'loading': '加载中...',
        'view_video': '观看视频',
        'summary_label': '摘要：'
    }
}

def get_text(key: str) -> str:
    """Get translated text based on current language."""
    return TRANSLATIONS[st.session_state.language].get(key, key)

def delete_summary(summary_id: int):
    """Delete a summary and handle the confirmation dialog."""
    if summary_id not in st.session_state.delete_confirmation:
        st.session_state.delete_confirmation[summary_id] = False

    if st.button(get_text('delete_button'), key=f"delete_{summary_id}"):
        st.session_state.delete_confirmation[summary_id] = True

    if st.session_state.delete_confirmation[summary_id]:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(get_text('delete_confirm'), key=f"confirm_{summary_id}"):
                success, message = st.session_state.db_handler.delete_summary(summary_id)
                if success:
                    st.success(get_text('delete_success'))
                    st.session_state.delete_confirmation[summary_id] = False
                    st.experimental_rerun()
                else:
                    st.error(f"{get_text('delete_error')}{message}")
        with col2:
            if st.button(get_text('cancel_button'), key=f"cancel_{summary_id}"):
                st.session_state.delete_confirmation[summary_id] = False
                st.experimental_rerun()

def initialize_session_state():
    """Initialize session state variables."""
    if 'language' not in st.session_state:
        st.session_state.language = 'ja'
    if 'delete_confirmation' not in st.session_state:
        st.session_state.delete_confirmation = {}

    # Initialize database connection
    if 'db_handler' not in st.session_state:
        try:
            st.session_state.db_handler = DatabaseHandler()
        except Exception as e:
            st.error(f"{get_text('db_error')} {str(e)}")
            st.session_state.db_handler = None

def main():
    st.set_page_config(page_title="Summary History", page_icon="📚", layout="wide")

    # Load custom CSS
    try:
        with open('assets/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading CSS: {str(e)}")

    initialize_session_state()

    st.title(f"📚 {get_text('page_title')}")

    # Language selector
    st.selectbox(
        get_text('language_selector'),
        options=['ja', 'en', 'zh'],
        index=['ja', 'en', 'zh'].index(st.session_state.language),
        format_func=lambda x: '日本語' if x == 'ja' else 'English' if x == 'en' else '中文',
        key='language'
    )

    if st.session_state.db_handler is None:
        st.error(get_text('db_error'))
        return

    with st.spinner(get_text('loading')):
        summaries = st.session_state.db_handler.get_summaries_by_language(
            st.session_state.language
        )

        if not summaries:
            st.info(get_text('no_summaries'))
            return

        # Display summaries in a grid layout
        cols = st.columns(2)  # 2列のグリッドレイアウト
        for idx, summary in enumerate(summaries):
            with cols[idx % 2]:
                with st.container():
                    # サムネイル画像とタイトルを表示
                    if summary.thumbnail_url:
                        st.image(summary.thumbnail_url, use_column_width=True)

                    # タイトルと日時
                    date_format = get_text('summary_date_format')
                    formatted_date = summary.timestamp.strftime(date_format)
                    st.markdown(f"### {summary.title}")
                    st.markdown(f"*{formatted_date}*")

                    # 要約内容
                    st.markdown(f"**{get_text('summary_label')}**")
                    st.markdown(summary.summary)

                    # 動画リンクと削除ボタン
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        video_url = f"https://youtube.com/watch?v={summary.video_id}"
                        st.markdown(f'<a href="{video_url}" target="_blank" class="video-link">'
                                  f'{get_text("view_video")}</a>', unsafe_allow_html=True)
                    with col2:
                        delete_summary(summary.id)

                    # 区切り線
                    st.markdown("---")

if __name__ == "__main__":
    main()
