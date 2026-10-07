"""Seed the scrapbook with three sample photos from data/.

Usage:
    python seed.py            # seeds the local `scrapbook` catalog directory
    python seed.py my_dir     # or another directory you passed to `pxt schema update`
"""
import sys
from pathlib import Path

import pixeltable as pxt

target = sys.argv[1] if len(sys.argv) > 1 else 'scrapbook'
HERE = Path(__file__).resolve().parent

SEED = {
    'scrapbook': [
        {'city': 'Lisbon', 'country': 'Portugal', 'taken_on': '2026-05-02', 'caption': 'Tram 28 at golden hour', 'photo': 'data/lisbon.png'},
        {'city': 'Kyoto', 'country': 'Japan', 'taken_on': '2026-04-11', 'caption': 'Fushimi Inari, a thousand gates', 'photo': 'data/kyoto.png'},
        {'city': 'Reykjavik', 'country': 'Iceland', 'taken_on': '2026-02-20', 'caption': None, 'photo': 'data/reykjavik.png'},
    ],
}

for table_name, rows in SEED.items():
    t = pxt.get_table(f'{target}/{table_name}')
    if t.count() > 0:
        print(f'{target}/{table_name} already has {t.count()} rows; skipping')
        continue
    for row in rows:
        for k, v in row.items():
            if isinstance(v, str) and v.startswith('data/'):
                row[k] = str(HERE / v)   # local sample media file
    t.insert(rows)
    print(f'inserted {len(rows)} rows into {target}/{table_name}')
