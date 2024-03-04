FROM docker.io/python:3.12-alpine as builder

WORKDIR /build
COPY ./ /build
RUN python -m pip install poetry && \
    poetry build && \
    mkdir /pubobot && \
    python -m venv /pubobot && \
    /pubobot/bin/python -m pip install /build/dist/*.whl

FROM docker.io/python:3.12-alpine
COPY --from=builder /pubobot /pubobot

VOLUME /pubobot/config
VOLUME /pubobot/data
VOLUME /pubobot/logs

ENTRYPOINT ["/pubobot/bin/pubobot"]
CMD ["-c", "/pubobot/config/config.cfg", "-d", "/pubobot/data/database.sqlite3", "-l", "/pubobot/logs"]
