
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/
COPY outputs/ ./outputs/

EXPOSE 8501

CMD ["streamlit", "run", "scripts/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
