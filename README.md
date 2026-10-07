<!-- pixeltable-example-app: 20260926-travel-scrapbook -->
# Travel Scrapbook API built with Pixeltable

[![Built with Pixeltable](https://img.shields.io/badge/built%20with-Pixeltable-5b4bff)](https://pixeltable.com)
[![PyPI - pixeltable](https://img.shields.io/pypi/v/pixeltable?label=pixeltable)](https://pypi.org/project/pixeltable/)
[![GitHub stars](https://img.shields.io/github/stars/pixeltable/pixeltable?style=social)](https://github.com/pixeltable/pixeltable)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Upload a travel photo with its city, country, date and caption, and Pixeltable stores the image as a first-class **`pxt.Image` column**, generates a 64x48 thumbnail with `photo.resize(...)`, tags the place and works out the photo's orientation with a PIL-based UDF, all as **computed columns**. The API accepts multipart uploads, lists photos by country, and streams the latest thumbnail for a city straight from the table.

[Pixeltable](https://pixeltable.com) is open-source, Python-native **multimodal AI data infrastructure**: tables, incremental computed columns, UDFs, indexes and serving in one library, running locally or on Pixeltable Cloud.

> ⭐ **Like this example?** Star [pixeltable/pixeltable](https://github.com/pixeltable/pixeltable) on GitHub. It helps other developers find it.

## What this example shows

- **Multimodal media columns** with configurable media destinations
- **Reads and writes**: Json columns, primary-key updates and deletes, and quick inspection with the `pxt` CLI (`pxt rows`, `pxt get`, `pxt count`)
- **Incremental computed columns** powered by plain Python UDFs (`@pxt.udf`)
- **FastAPI serving**: one `FastAPIRouter` turns tables and `@pxt.query` functions into typed REST routes (insert, update, delete, compute and query) with OpenAPI docs
- **Importable UDF module**: UDFs in `udfs.py`, tables in `models.py`, queries in `queries.py`, routes in `app.py` (Pixeltable resolves UDFs by module path)
- **`pixeltable.toml`** declares a local database and a **Pixeltable Cloud** database, so the same code deploys with `pxt db update`

## Media in Pixeltable, briefly

- `photo: pxt.Image` stores the uploaded file in Pixeltable's media store. You get a PIL image in UDFs and a file or URL when you read it back.
- `thumb = photo.resize((64, 48))` is a **media computed column**: the thumbnail is generated once on insert and stored, not on every request.
- **Where media goes is configuration, not code.** By default it lives in the local media store (or your database's home bucket on Pixeltable Cloud). To put generated files somewhere else, set per-database destinations in `pixeltable.toml`, e.g. `settings = { output_media_dest = 's3://<your-bucket>/scrapbook/' }`, or pass `destination=` on a single column.
- `GET /photos/thumb?city=...` is a one-row query route with `return_fileresponse=True`, so the API returns the image bytes directly.

## What's inside

| File | What it is |
|------|------------|
| `app.py` | The API: one `FastAPIRouter` wiring the tables and queries into REST routes |
| `client_demo.py` | Upload a photo, caption it, browse by country and download a thumbnail through the API |
| `data/kyoto.png` | Sample data |
| `data/lisbon.png` | Sample data |
| `data/reykjavik.png` | Sample data |
| `models.py` | Tables declared as Python classes: columns, computed columns, indexes |
| `pixeltable.toml` | Project config: the local database plus a Pixeltable Cloud database (sizing, deploy excludes) |
| `queries.py` | `@pxt.query` functions served as query routes |
| `seed.py` | Seed the scrapbook with three sample photos from data/ |
| `udfs.py` | Pixeltable UDFs (`@pxt.udf`) in their own importable module |
| `requirements.txt` / `pyproject.toml` | Dependencies (`pixeltable[serve]>=0.7.14`) |

**Tables**

| Table | Stored columns | Computed columns |
|-------|---------|------------------|
| `scrapbook` | `city`, `country`, `taken_on`, `caption`, `photo` | `id`, `thumb`, `place`, `shape`, `blurb` |

**API routes** (service `scrapbook_api`)

| Method | Path | Kind | Backed by | Notes |
|--------|------|------|-----------|-------|
| `POST` | `/photos` | insert | `Scrapbook` |  |
| `POST` | `/photos/caption` | update | `Scrapbook` |  |
| `GET` | `/photos/by-country` | query | `photos_in` |  |
| `GET` | `/photos/thumb` | query | `latest_thumb` | one row (404 if none) |

## Quickstart

Requires Python 3.11+ and `pixeltable[serve]>=0.7.14`.

```bash
git clone https://github.com/pierrebrunelle/pixeltable-travel-scrapbook.git
cd pixeltable-travel-scrapbook
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create the tables in a local catalog directory named `scrapbook`
pxt schema update app.py scrapbook

python seed.py scrapbook
pxt service run app.py scrapbook --port 8000   # open http://localhost:8000/docs
python client_demo.py                         # in another terminal
```

Try it:

```bash
curl -s -X POST localhost:8000/photos -F city=Porto -F country=Portugal -F caption='Riverside' -F photo=@data/lisbon.png
curl -s 'localhost:8000/photos/by-country?country=Portugal'
curl -s -o thumb.png 'localhost:8000/photos/thumb?city=Porto'
```

## Deploy to Pixeltable Cloud

The same `app.py` runs on [Pixeltable Cloud](https://pixeltable.com). Sign in (or get a free trial database with `pxt new`), point the second database entry in `pixeltable.toml` at your own database, then deploy:

```bash
pxt login                       # or: export PIXELTABLE_API_KEY=<your-api-key>
# edit pixeltable.toml: name = 'pxt://<your-org>:<your-db>'
pxt db update pxt://<your-org>:<your-db>                 # build the image and upload the project
pxt schema update app.py pxt://<your-org>:<your-db>/scrapbook   # create the tables in the hosted database
pxt service update app.py pxt://<your-org>:<your-db>/scrapbook  # start the API there
pxt service list pxt://<your-org>:<your-db>              # list hosted services
```

Hosted routes require an API key: send it in the `X-api-key` header (for example `-H "X-api-key: $PIXELTABLE_API_KEY"`). Keep keys in environment variables or `pxt secret set`, never in code.

## Code walkthrough

**1. Business logic is plain Python, in `udfs.py`.** A `@pxt.udf` function can be used as a column expression. Pixeltable records UDFs by module path (`udfs.trip_tag`), so they live in their own importable module rather than inline in the app: the daemon, serving workers and Pixeltable Cloud import it again by that path.

```python
# udfs.py
@pxt.udf
def trip_tag(city: str, country: str) -> str:
    """'Lisbon, Portugal' -> 'lisbon-portugal'."""
    return f'{city}-{country}'.lower().replace(' ', '-')
```

**2. Tables are Python classes (`models.py`).** Annotated attributes are stored columns; attributes assigned an expression are **computed columns** (`id`, `thumb`, `place`, `shape`, `blurb`), evaluated incrementally on every insert or update and recomputed when their inputs change.

```python
# models.py
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
```

**3. Queries are functions (`queries.py`).** `@pxt.query` wraps a Pixeltable query so it can be called from Python or exposed as a route:

```python
# queries.py
@pxt.query
def photos_in(country: str):
    """Photos from one country, by date."""
    return Scrapbook.where(Scrapbook.country == country).select(
        Scrapbook.id, Scrapbook.place, Scrapbook.taken_on, Scrapbook.shape, Scrapbook.blurb
    ).order_by(Scrapbook.taken_on)
```

**4. One router, a full REST API.** `FastAPIRouter` generates request/response models from the column types, validates input, and publishes OpenAPI docs at `/docs`:

```python
# app.py
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
```

## Learn more

- 🌐 Website: https://pixeltable.com
- 📚 Docs: https://docs.pixeltable.com
- 💻 Source: https://github.com/pixeltable/pixeltable (⭐ star it if Pixeltable is useful to you)
- 📦 PyPI: https://pypi.org/project/pixeltable/

---

<sub>Built as part of a daily series of Pixeltable example apps · Pixeltable 0.7.14 · Python, FastAPI, incremental computed columns · Licensed under Apache-2.0.</sub>
