FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Usuario sin privilegios (la guia original corre como root)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

CMD ["waitress-serve", "--listen=0.0.0.0:5000", "app:app"]
