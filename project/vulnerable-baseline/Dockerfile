FROM python:3.7
WORKDIR /app
COPY . .
RUN pip install -r needs-vulnerable.txt
USER root
CMD ["python","app.py"]
