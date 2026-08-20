FROM debian:trixie-slim AS document-tools

ARG TARGETARCH
ARG PANDOC_VERSION=3.10.2
ARG TECTONIC_VERSION=0.17.0

RUN apt-get update \
    && apt-get install --yes --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
        amd64) \
            pandoc_arch="amd64"; \
            pandoc_sha256="c7edd535941c48be6a362081a748272837de81ae11777202d9c341d3d8261c9a"; \
            tectonic_arch="x86_64"; \
            tectonic_sha256="8533d07f9ccbd7a65824b9e0459041bca34af1eb33daba48f59215593753a3b7" \
            ;; \
        arm64) \
            pandoc_arch="arm64"; \
            pandoc_sha256="1c4d69f2a092bd47cb180e58a4aab7b9637101ced928252458c7d41a7f7fa71d"; \
            tectonic_arch="aarch64"; \
            tectonic_sha256="b10954a95404f3ab2328d2fa59a5ebab8e657f893fab096f98be8db7c0c979b8" \
            ;; \
        *) exit 1 ;; \
    esac; \
    curl --fail --location --silent --show-error \
        "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-linux-${pandoc_arch}.tar.gz" \
        --output /tmp/pandoc.tar.gz; \
    echo "${pandoc_sha256}  /tmp/pandoc.tar.gz" | sha256sum --check -; \
    mkdir /tmp/pandoc; \
    tar --extract --gzip --file /tmp/pandoc.tar.gz --directory /tmp/pandoc --strip-components=1; \
    install /tmp/pandoc/bin/pandoc /usr/local/bin/pandoc; \
    curl --fail --location --silent --show-error \
        "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${TECTONIC_VERSION}/tectonic-${TECTONIC_VERSION}-${tectonic_arch}-unknown-linux-musl.tar.gz" \
        --output /tmp/tectonic.tar.gz; \
    echo "${tectonic_sha256}  /tmp/tectonic.tar.gz" | sha256sum --check -; \
    tar --extract --gzip --file /tmp/tectonic.tar.gz --directory /usr/local/bin tectonic

FROM python:3.14-slim AS builder

ENV POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true

RUN python -m pip install --no-cache-dir poetry==2.2.1

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction

FROM python:3.14-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    HOME=/home/app \
    XDG_CACHE_HOME=/home/app/.cache \
    IDE_TECTONIC_ONLY_CACHED=true \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        fontconfig=2.15.0-2.3 \
        fonts-noto-cjk=1:20240730+repack1-1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=document-tools /usr/local/bin/pandoc /usr/local/bin/pandoc
COPY --from=document-tools /usr/local/bin/tectonic /usr/local/bin/tectonic

USER app
RUN printf '%s\n' \
        '\documentclass{article}' \
        '\usepackage{xcolor,amsmath,amssymb,unicode-math,lmodern}' \
        '\usepackage{longtable,booktabs,array,caption,multirow}' \
        '\usepackage{calc,etoolbox,footnotehyper,graphicx}' \
        '\usepackage{bookmark,xurl,hyperref}' \
        '\setmainfont{Noto Sans CJK KR}' \
        '\begin{document}한국어 cache\end{document}' \
        > /tmp/tectonic-cache-warmup.tex \
    && success=0 \
    && for attempt in 1 2 3 4 5; do \
        if tectonic --untrusted --outdir /tmp /tmp/tectonic-cache-warmup.tex; then \
            success=1; \
            break; \
        fi; \
        sleep "$((attempt * 15))"; \
    done \
    && test "$success" -eq 1 \
    && rm -f /tmp/tectonic-cache-warmup.*

COPY --chown=app:app src ./src

EXPOSE 8000

CMD ["uvicorn", "ide_api.cmd.api:app", "--host", "0.0.0.0", "--port", "8000"]
