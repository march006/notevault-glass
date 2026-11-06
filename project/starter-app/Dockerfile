FROM python:3.12.8-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN useradd --system --uid 10001 --create-home appuser
WORKDIR /app
COPY needs.txt .
RUN pip install --no-cache-dir -r needs.txt
COPY --chown=appuser:appuser app.py ./
COPY --chown=appuser:appuser templates ./templates
COPY --chown=appuser:appuser static ./static
RUN mkdir -p /data && chown appuser:appuser /data
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')" || exit 1
CMD ["gunicorn","--bind=0.0.0.0:8080","--workers=2","--threads=4","--timeout=30","app:app"]
