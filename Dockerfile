FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the dependencies declared in pyproject.toml before copying application
# source. This preserves Docker's dependency-installation cache when only source
# files change.
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install $(python -c "import tomllib; print(' '.join(tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']))")

RUN addgroup --system appuser \
    && adduser --system --ingroup appuser --home /app --no-create-home appuser

COPY --chown=appuser:appuser app ./app
RUN pip install --no-deps .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
