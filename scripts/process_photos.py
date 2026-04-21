"""Resize the source campaign PNGs to web-friendly JPEGs.

Source: website/pics/*.png  (4–5 MB each, very high resolution)
Output: website/static/uploads/photos/<slug>.jpg  (max 900px wide, 85 quality)

Slug mapping is keyed off the source filename so re-running overwrites in place.
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC_DIR = os.path.join(ROOT, 'pics')
DST_DIR = os.path.join(ROOT, 'static', 'uploads', 'photos')

# source filename (without .png)  ->  output slug (without extension)
SLUG_MAP = {
    'Raed':           'raed-atrash',
    'Kareem Sheebat': 'kareem-sheebat',
    'Rita Shomaly':   'rita-shomaly',
    'Lina Qazaha':    'lina-qazaha',
    'Jamal Shayeb':   'jamal-shayeb',
    'Bashar Hawash':  'bashar-hawash',
    'Munjed Hawash':  'munjed-hawash',
    'Elias Awwad':    'elias-awwad',
    'Ramiz Awad':     'ramiz-awad',
    'Jacob Yatim':    'jacob-yatim',
    'Majdi Atrash':   'majdi-atrash',
    'Jiana Atrash':   'jiana-atrash',
    'Jwan Atrash':    'jwan-atrash',
}

MAX_WIDTH = 900


def process():
    os.makedirs(DST_DIR, exist_ok=True)
    results = []
    for src_stem, out_slug in SLUG_MAP.items():
        src = os.path.join(SRC_DIR, f'{src_stem}.png')
        if not os.path.exists(src):
            results.append((src_stem, 'MISSING'))
            continue
        dst = os.path.join(DST_DIR, f'{out_slug}.jpg')
        with Image.open(src) as im:
            if im.mode in ('RGBA', 'LA', 'P'):
                im = im.convert('RGB')
            w, h = im.size
            if w > MAX_WIDTH:
                new_h = int(h * MAX_WIDTH / w)
                im = im.resize((MAX_WIDTH, new_h), Image.LANCZOS)
            im.save(dst, 'JPEG', quality=85, optimize=True)
        size_kb = os.path.getsize(dst) // 1024
        results.append((src_stem, f'{out_slug}.jpg ({size_kb} KB)'))
    return results


if __name__ == '__main__':
    for name, result in process():
        print(f'{name:20} -> {result}')
