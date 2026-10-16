FROM python:3.12-slim
WORKDIR /app
COPY backend /app/backend
COPY ml /app/ml
RUN pip install --no-cache-dir -r backend/requirements.lock && pip install --no-cache-dir --no-deps ./backend
ENV TICKETOPS_DATABASE_URL=postgresql+psycopg://ticketops:ticketops@db:5432/ticketops
EXPOSE 8018
CMD ["sh","-c","alembic -c backend/alembic.ini upgrade head && uvicorn ticketops.main:app --host 0.0.0.0 --port 8018"]
