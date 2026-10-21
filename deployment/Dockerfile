# Linux/amd64 manifest inspected October 21, 2026; hosted acceptance is separate.
FROM python:3.14.8-slim-bookworm@sha256:ddec44f5ab04dd68aaee83d7dc9831c964a4bb9e950c89960e60760373fbf54f AS build
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY deployment/build-tools.lock.txt ./build-tools.lock.txt
RUN python -m pip install --only-binary=:all: --require-hashes -r build-tools.lock.txt
COPY backend/requirements.lock.txt ./requirements.lock.txt
RUN python -m pip install --only-binary=:all: -r requirements.lock.txt
COPY pyproject.toml ./
COPY backend/ ./backend/
COPY data-build/ ./data-build/
COPY deployment/ ./deployment/
RUN python -m pip install --no-deps --no-build-isolation .
ARG FDA_RELEASE_URL=""
RUN if [ -n "$FDA_RELEASE_URL" ]; then \
      python -m deployment.release fetch --url "$FDA_RELEASE_URL" --lock deployment/release.lock.json --destination /opt/fda/release; \
    else \
      python -m deployment.release extract --archive deployment/input/release.tar.gz --lock deployment/release.lock.json --destination /opt/fda/release; \
    fi
RUN python -m pip uninstall --yes setuptools pip

FROM python:3.14.8-slim-bookworm@sha256:ddec44f5ab04dd68aaee83d7dc9831c964a4bb9e950c89960e60760373fbf54f
RUN python -m pip uninstall --yes pip
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    FDA_RELEASE_DIRECTORY=/opt/fda/release \
    FDA_ALLOWED_ORIGINS=https://abdul-rahmansayed.github.io PORT=10000
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --from=build /opt/fda/release /opt/fda/release
COPY deployment/release.lock.json /opt/fda/release.lock.json
USER 10001:10001
EXPOSE 10000
CMD ["python", "-m", "deployment.serve", "--lock", "/opt/fda/release.lock.json"]
