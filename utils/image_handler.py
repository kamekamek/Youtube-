from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

class ImageHandler:
    def __init__(self):
        self.assets_dir = Path('assets')
        self.character_path = self.assets_dir / 'character.png'
        
        # フォントの設定（日本語対応フォントが必要）
        font_path = self.assets_dir / 'fonts' / 'NotoSansJP-Regular.ttf'
        self.font = ImageFont.truetype(str(font_path), size=24) if font_path.exists() else ImageFont.load_default()

    def create_character_bubble(self, text: str) -> Image.Image:
        """キャラクターと吹き出しを含む画像を生成"""
        # キャラクター画像を開く
        try:
            base_img = Image.open(self.character_path)
        except FileNotFoundError:
            # キャラクター画像がない場合は白い画像を作成
            base_img = Image.new('RGB', (400, 300), 'white')

        # 描画オブジェクトを作成
        draw = ImageDraw.Draw(base_img)

        # 吹き出しの位置とサイズ
        bubble_x = 150
        bubble_y = 50
        bubble_width = 200
        bubble_height = 100

        # 吹き出しを描画
        draw.rectangle(
            [(bubble_x, bubble_y), (bubble_x + bubble_width, bubble_y + bubble_height)],
            fill='white',
            outline='black',
            width=2
        )

        # テキストを描画（中央揃え）
        text_bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        text_x = bubble_x + (bubble_width - text_width) // 2
        text_y = bubble_y + (bubble_height - text_height) // 2
        
        draw.text((text_x, text_y), text, fill='black', font=self.font)

        return base_img 