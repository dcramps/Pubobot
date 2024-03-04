# Pubobot

## Development Setup

[Install poetry for your system](https://python-poetry.org/docs/#installation).

Create a `config.cfg` file and add the following:
```python
DISCORD_TOKEN = "your_discord_token"
```

For more options, see [config.cfg.example](config.cfg.example).

Install dependencies and execute with poetry:

```console
$ poetry install
$ poetry run pubobot
```

## Deploying

### Build

```console
$ docker build -t pubobot .
```

### Docker

For persistence, mount volumes `/pubobot/data` and `/pubobot/logs`.

```console
$ docker run -d \
    -e PUBOBOT_DISCORD_TOKEN="...your bot token.." \
    -v pubobot-data:/pubobot/data \
    -v pubobot-logs:/pubobot/logs \
    pubobot
```

Alternatively, you can a config file matching `config.cfg.example` and mount to
`/pubobot/config/config.cfg`.

```console
$ docker run -d \
    -v path/to/config.cfg:/pubobot/config/config.cfg \
    -v pubobot-data:/pubobot/data \
    -v pubobot-logs:/pubobot/logs \
    pubobot
```

### Docker Compose

A `compose.yaml` file is provided for your convenience. You will need to create
a `.env` file and set your discord token:

**.env**
```
PUBOBOT_DISCORD_TOKEN=..bot token..
```
Bring up
```console
$ docker-compose up
```
