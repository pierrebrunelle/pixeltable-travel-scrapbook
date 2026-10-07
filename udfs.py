"""Pixeltable UDFs for the travel scrapbook (recorded by module path, e.g. `udfs.orientation`)."""
import PIL.Image

import pixeltable as pxt


@pxt.udf
def trip_tag(city: str, country: str) -> str:
    """'Lisbon, Portugal' -> 'lisbon-portugal'."""
    return f'{city}-{country}'.lower().replace(' ', '-')


@pxt.udf
def orientation(photo: PIL.Image.Image) -> str:
    """landscape / portrait / square from the image size."""
    w, h = photo.size
    return 'square' if abs(w - h) <= 2 else ('landscape' if w > h else 'portrait')


@pxt.udf
def caption_blurb(caption: str | None) -> str:
    c = (caption or '').strip()
    return c if len(c) <= 40 else c[:39].rstrip() + '…'
