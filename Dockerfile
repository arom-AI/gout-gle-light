# Utiliser une image Python officielle
FROM python:3.12-slim

# Installer tesseract et les langues française + anglaise
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    && apt-get clean

# Définir le répertoire de travail
WORKDIR /app

# Copier ton projet dans l'image
COPY . .

# Installer les dépendances Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Exposer le port pour Streamlit
EXPOSE 8000

# Commande de démarrage
CMD ["streamlit", "run", "app_goutgle.py", "--server.port=8000", "--server.address=0.0.0.0"]
