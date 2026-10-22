"""Check global visual uniqueness, responsive variants and complete sections."""
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import json
from lxml import html
from PIL import Image

ROOT = Path(__file__).resolve().parent
PAGES = {'index.html': 14, 'sistema-personalizado.html': 18,
         'pagina-web-personalizada.html': 20}
POSTERS = {'soluciones', 'inventarios', 'stock', 'prestamos', 'web',
           'negocios', 'automatizar'}


def difference_hash(image):
    gray = image.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
    pixels = [gray.getpixel((x, y)) for y in range(8) for x in range(9)]
    return sum((pixels[y * 9 + x] > pixels[y * 9 + x + 1]) << (y * 8 + x)
               for y in range(8) for x in range(8))


def verify():
    assets = json.loads((ROOT / 'visual-assets.json').read_text())
    placements, errors, sections = [], [], 0
    for page, expected in PAGES.items():
        doc = html.parse(str(ROOT / page))
        images = doc.xpath('//main//img[not(contains(@class,"whatsapp-icon"))]')
        if len(images) != expected:
            errors.append(f'{page}: expected {expected} images, got {len(images)}')
        for image in images:
            key = image.get('data-asset')
            placements.append({'page': page, 'asset': key})
            if key not in assets or image.get('src') != f'/{key}-900.webp':
                errors.append(f'{page}: missing asset identity or wrong source: {key}')
            if not image.get('alt') and 'v-poster-back' not in image.getparent().get('class', ''):
                errors.append(f'{page}: missing descriptive alt: {key}')
        for section in doc.xpath('//main/section'):
            sections += 1
            if not section.xpath('.//img[@data-asset]'):
                errors.append(f'{page}: section without an image')
    counts = Counter(p['asset'] for p in placements)
    duplicates = {k: n for k, n in counts.items() if n > 1}
    if duplicates:
        errors.append(f'Images repeated across pages: {duplicates}')
    if set(counts) != set(assets) or not POSTERS <= set(counts):
        errors.append('Published images do not match the complete asset catalog')

    hashes, decoded, fingerprints, total_bytes = {}, {}, {}, 0
    for key in assets:
        for width in (480, 900, 1200):
            path = ROOT / f'{key}-{width}.webp'
            try:
                raw = path.read_bytes()
                total_bytes += len(raw)
                with Image.open(path) as image:
                    image.load()
                    if image.width != width or not raw:
                        errors.append(f'Invalid dimensions or empty image: {path.name}')
                    if width == 900:
                        hashes[key] = sha256(raw).hexdigest()
                        decoded[key] = sha256(image.convert('RGB').tobytes()).hexdigest()
                        fingerprints[key] = difference_hash(image)
                        if image.height != assets[key]['height900']:
                            errors.append(f'Wrong HTML image dimensions: {key}')
            except (OSError, ValueError) as exc:
                errors.append(f'{path.name}: {exc}')
    similar = []
    for a, b in combinations(fingerprints, 2):
        distance = (fingerprints[a] ^ fingerprints[b]).bit_count()
        if hashes[a] == hashes[b] or decoded[a] == decoded[b]:
            errors.append(f'Duplicate image contents: {a}, {b}')
        if distance <= 6:
            similar.append({'assets': [a, b], 'difference_hash_distance': distance})
    return {'pages': len(PAGES), 'sections_with_images': sections,
            'placements': len(placements), 'unique_content_images': len(counts),
            'original_posters_used_once': sorted(POSTERS),
            'responsive_variants': len(assets) * 3, 'total_variant_bytes': total_bytes,
            'duplicate_placements': duplicates, 'similarity_review_candidates': similar,
            'asset_placements': placements, 'errors': errors}


if __name__ == '__main__':
    result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['errors']))
