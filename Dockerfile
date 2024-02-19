# Usa la imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requerimientos
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos de la aplicación
COPY . .

# Expone el puerto 5000 (puerto predeterminado de Flask)
EXPOSE 0000

# Define la variable de entorno FLASK_APP con el nombre del archivo principal de tu aplicación Flask
ENV FLASK_APP=app.py
ARG DATABASE_URL
ENV DATABASE_URL=$DATABASE_URL
ENV PORT=0000

# Ejecuta la aplicación Flask
CMD ["python", "app.py"]
