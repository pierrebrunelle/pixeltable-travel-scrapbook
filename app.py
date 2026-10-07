"""Travel Scrapbook API built with Pixeltable.

    pxt schema update app.py scrapbook
    pxt service run app.py scrapbook
"""
import pixeltable as pxt
import pixeltable.functions as pxtf
from pixeltable.serving import FastAPIRouter

from udfs import caption_blurb, orientation, trip_tag

# ---- tables ----
TableModel = pxt.model_base()


class Scrapbook(TableModel, name='scrapbook'):
    id = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)
    city: pxt.String
    country: pxt.String
    taken_on: pxt.String | None
    caption: pxt.String | None
    photo: pxt.Image

    thumb = photo.resize((64, 48))          # stored media, generated once per photo
    place = trip_tag(city, country)
    shape = orientation(photo)
    blurb = caption_blurb(caption)


# ---- queries ----
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


# ---- routes ----
scrapbook_api = FastAPIRouter(name='scrapbook_api')
scrapbook_api.add_insert_route(
    Scrapbook, path='/photos',
    inputs=[Scrapbook.city, Scrapbook.country, Scrapbook.taken_on, Scrapbook.caption],
    uploadfile_inputs=[Scrapbook.photo],
    outputs=[Scrapbook.id, Scrapbook.place, Scrapbook.shape, Scrapbook.blurb],
)
scrapbook_api.add_update_route(Scrapbook, path='/photos/caption', inputs=[Scrapbook.caption],
                               outputs=[Scrapbook.id, Scrapbook.blurb])
scrapbook_api.add_query_route(path='/photos/by-country', query=photos_in, method='get')
scrapbook_api.add_query_route(path='/photos/thumb', query=latest_thumb, method='get', one_row=True,
                              return_fileresponse=True)
