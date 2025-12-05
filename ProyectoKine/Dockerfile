# Dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# --- PASOS PARA USAR UN ENTORNO VIRTUAL ---
# 1. Crear entorno virtual (venv)
RUN python -m venv /opt/venv
# 2. Activar el entorno virtual agregándolo al PATH
ENV PATH="/opt/venv/bin:$PATH"
# ------------------------------------------

# 3. Copiar requirements e instalar DENTRO del venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto del código
COPY . .
ENV PYTHONPATH=/app:$PYTHONPATH
# Crear carpetas para archivos estáticos y media
RUN mkdir -p /vol/staticfiles /vol/media
EXPOSE 8000

# Comando de inicio: El venv/bin ya está en el PATH, y usamos la ruta explícita de Python
CMD ["python", "-m", "gunicorn", "ProyectoKine.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]