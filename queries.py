"""Queries over the scrapbook."""
import pixeltable as pxt

from models import Scrapbook


@pxt.query
def photos_in(country: str):
    """Photos from one country, by date."""
    return Scrapbook.where(Scrapbook.country == country).select(
        Scrapbook.id, Scrapbook.place, Scrapbook.taken_on, Scrapbook.shape, Scrapbook.blurb
    ).order_by(Scrapbook.taken_on)


@pxt.query
def latest_thumb(city: str):
    """The most recent thumbnail for a city (served as an image file)."""
    return Scrapbook.where(Scrapbook.city == city).order_by(Scrapbook.id, asc=False).limit(1).select(Scrapbook.thumb)
