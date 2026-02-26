FROM python:3.13-slim

WORKDIR /app

# Install dependencies first (layer cached separately from code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "ui/streamlit_app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
