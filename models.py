"""The scrapbook table: an image column plus media and scalar computed columns."""
import pixeltable as pxt
import pixeltable.functions as pxtf

from udfs import caption_blurb, orientation, trip_tag

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
