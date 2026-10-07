"""Travel Scrapbook API built with Pixeltable.

    pxt schema update app.py scrapbook
    pxt service run app.py scrapbook
"""
from pixeltable.serving import FastAPIRouter

from models import Scrapbook, TableModel  # noqa: F401  (TableModel lets `pxt schema` find the models)
from queries import latest_thumb, photos_in

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
