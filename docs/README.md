# Documentation for `qctss_client`

How to build the documentation:

## By Docker

Use the `docker-compose.yml` at the root of the repository to build the documentation. The following command will build the documentation and place it in the `docs/_dist`.

```bash
docker compose up --build -d qctss-client-docs-sphinx
```

## By Local Build

```bash
sphinx-build -W -E -b html docs docs/_dist
# at project root
```

## Preview

```bash
python -m http.server -d docs/_dist 3500
# then open your browser and go to http://localhost:3500
```
