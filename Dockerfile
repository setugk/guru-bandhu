FROM python:3.12-alpine
WORKDIR /app
RUN pip install --no-cache-dir flask
COPY app.py db.py create_account.py ./
COPY templates/ templates/
COPY static/ static/
EXPOSE 5000
CMD ["python", "app.py"]
