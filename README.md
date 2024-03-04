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

## Deploying Container

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
