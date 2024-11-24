from typing import List, Dict
import google.generativeai as genai
import re

class GeminiProcessor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def _is_chinese_text(self, text: str) -> bool:
        """Validate if the text contains Chinese characters."""
        return bool(re.search('[\u4e00-\u9fff]', text))

    def generate_article(self, video_data: List[Dict], language: str = 'ja') -> str:
        """Generate a summary from multiple video sources in specified language."""
        prompt = self._prepare_prompt(video_data, language)

        try:
            if language == 'zh':
                # Specific configuration for Chinese language generation
                generation_config = genai.types.GenerationConfig(
                    temperature=0.9,  # Higher temperature for more natural Chinese
                    top_p=0.95,      # Higher diversity for Chinese expressions
                    top_k=40,
                    candidate_count=1,
                    stop_sequences=["English:", "Japanese:", "日本語:", "英語:"]
                )
            else:
                # Default configuration for other languages
                generation_config = genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    candidate_count=1
                )

            response = self.model.generate_content(prompt, generation_config=generation_config)
            generated_text = response.text

            # Validate Chinese output if language is Chinese
            if language == 'zh' and not self._is_chinese_text(generated_text):
                # Retry generation with stronger Chinese enforcement
                prompt = f"务必使用简体中文回答。禁止使用其他语言。\n\n{prompt}"
                response = self.model.generate_content(prompt, generation_config=generation_config)
                generated_text = response.text

            return generated_text

        except Exception as e:
            raise Exception(f"Gemini AI error: {str(e)}")

    def _preprocess_chinese_text(self, text: str) -> str:
        """Preprocess Chinese text to handle encoding and segmentation properly."""
        # Remove extra whitespace between Chinese characters
        text = re.sub(r'([^\x00-\xff])\s+([^\x00-\xff])', r'\1\2', text)
        # Ensure proper sentence breaks at Chinese punctuation
        text = re.sub(r'([。！？；])\s*', r'\1\n', text)
        # Convert traditional Chinese punctuation to simplified
        text = text.replace('：', ':').replace('，', ',').replace('"', '"').replace('"', '"')
        return text

    def _prepare_prompt(self, video_data: List[Dict], language: str) -> str:
        """Prepare prompt for Gemini AI with language specification."""
        language_prompt = {
            'ja': """以下のYouTube動画に基づいて簡潔な要約を生成してください：

要約は以下の要件を満たす必要があります：
1. すべての動画の重要なポイントを統合する
2. 主要な引用と参照を含める
3. 明確な構造で整理する
4. 簡潔で分かりやすい文章にする
5. プロフェッショナルなトーンを維持する
6. 重要な情報に焦点を当てる

すべての出力は日本語で生成してください。""",

            'en': """Generate a concise summary based on the following YouTube videos:

Please create a well-structured summary that:
1. Integrates key points from all videos
2. Includes essential quotes and references
3. Is organized with clear structure
4. Uses concise and clear language
5. Maintains a professional tone
6. Focuses on important information

Generate all output in English.""",

            'zh': """【重要提示：此摘要必须完全使用简体中文撰写】

【摘要生成指引】
本系统将为您生成一份结构完整、内容精炼的视频内容摘要。

【具体要求】
1. 内容要求
   • 提炼视频核心观点
   • 突出重要信息
   • 保持逻辑连贯性
   • 紧扣主题展开

2. 语言规范
   • 严格使用规范简体中文
   • 确保表达地道自然
   • 避免生硬翻译
   • 保持专业性

3. 格式规范
   • 合理分段
   • 重点突出
   • 层次分明
   • 结构清晰

【特别说明】
• 禁止使用英语或其他语言
• 确保所有内容均为中文表达
• 专业术语需使用标准中文译名"""
        }

        # Prepare language-specific prompt
        if language == 'zh':
            prompt = "【语言要求】\n必须使用标准简体中文输出全部内容。严禁使用其他语言。\n\n"
            prompt += language_prompt[language] + "\n\n"
            prompt += "【视频内容】\n"
        else:
            prompt = f"Output Language: {language}\n\n"
            prompt += language_prompt[language] + "\n\n"

        # Process video data
        for video in video_data:
            if 'error' not in video:
                if language == 'zh':
                    title_label = "【视频标题】"
                    content_label = "【内容记录】"
                else:
                    title_label = "Title: "
                    content_label = "Content: "

                prompt += f"{title_label}{video['title']}\n"

                # Preprocess transcript
                transcript = video['transcript']
                if language == 'zh':
                    if len(transcript) > 2000:
                        # Find last complete Chinese sentence
                        transcript = transcript[:2000]
                        last_period = max(
                            transcript.rfind('。'), 
                            transcript.rfind('！'), 
                            transcript.rfind('？'),
                            transcript.rfind('；')
                        )
                        if last_period > 0:
                            transcript = transcript[:last_period + 1]
                    transcript = self._preprocess_chinese_text(transcript)
                else:
                    transcript = transcript[:2000].rsplit('.', 1)[0] + '...'

                prompt += f"{content_label}{transcript}\n\n"

        if language == 'zh':
            prompt += "\n【注意事项】\n请确保生成的摘要完全使用简体中文，并保持专业性和可读性的平衡。"

        return prompt
