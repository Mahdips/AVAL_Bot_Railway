FROM python:3.11-slim

# Railway allocates ONE public port and ONE process per service.
# The app runs Telegram polling + the FastAPI web panel in a single
# event loop (WEB_WITH_BOT=1), so no supervisor or systemd is needed.
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY bot.py admin_control.py ./
COPY tests ./tests

# Railway injects PORT at runtime; bot.py reads WEB_PORT.
# The entrypoint maps Railway's PORT to WEB_PORT so a redeploy never
# picks a mismatched port. Default 8090 for local docker runs.
#
# The persistent volume must be mounted at /app/data in the Railway
# dashboard (Settings > Volumes). DATABASE_FILE points at it so
# SQLite survives every redeploy.
ENV WEB_HOST=0.0.0.0
ENV DATABASE_FILE=/app/data/bot.db

# Make sure the data dir exists even before the volume is mounted,
# so the first boot can create the database there.
RUN mkdir -p /app/data

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/' % os.getenv('WEB_PORT','8090'), timeout=4)" || exit 1

EXPOSE 8090

CMD ["sh", "-c", "WEB_PORT=${PORT:-8090} python bot.py"]
