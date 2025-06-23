# Dockerfile para Backend de Automação Hidrológica - Censipam Porto Velho
# Imagem base: Python 3.11 slim (otimizada)
FROM python:3.11-slim

# Metadados
LABEL maintainer="Censipam Porto Velho"
LABEL description="Backend de automação para dados hidrológicos - Projeto CONSULTAHIDRO"
LABEL version="1.0"

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV DEBIAN_FRONTEND=noninteractive

# Criar usuário não-root para segurança
RUN groupadd -r hidro && useradd -r -g hidro hidro

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    git \
    libpq-dev \
    gcc \
    python3-dev \
    build-essential \
    tk \
    tcl \
    python3-tk \
    tk-dev \
    tcl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    libxss1 \
    libatspi2.0-0 \
    libxrandr2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxinerama1 \
    libxkbcommon0 \
    fontconfig \
    fonts-liberation \
    libatlas-base-dev \
    liblapack-dev \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivo de requirements da pasta docker
COPY Scripts/docker/requirements.txt .

# Atualizar pip e instalar dependências Python + Playwright
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir playwright

# Instala os navegadores do Playwright
RUN playwright install chromium

# Criar estrutura de diretórios
RUN mkdir -p /app/Scripts/logica \
             /app/Scripts/Interfaces \
             /app/Scripts/Addons \
             /app/Scripts/dados \
             /app/data/input \
             /app/data/output \
             /app/data/logs

# Copiar código fonte do projeto (da estrutura Estações_Hidroweb/Scripts/)
COPY Scripts/logica/ /app/Scripts/logica/
COPY Scripts/Interfaces/ /app/Scripts/Interfaces/
COPY Scripts/Addons/ /app/Scripts/Addons/
COPY Scripts/dados/ /app/Scripts/dados/

# Criar script de entrada principal da pasta docker
COPY Scripts/docker/docker-entrypoint.py /app/
COPY Scripts/docker/verify_dependencies.py /app/

# Ajustar permissões
RUN chown -R hidro:hidro /app && \
    chmod +x /app/docker-entrypoint.py

# Criar volumes para dados externos
VOLUME ["/data", "/estacoes_hidroweb"]

# Mudar para usuário não-root
USER hidro

# Verificar instalações (debug) - CORREÇÃO: usar python -c
RUN python -c "import pandas, numpy, playwright, psycopg2, customtkinter; print('✅ Todas as bibliotecas principais carregadas com sucesso!')"

# Exposer porta (opcional, para futuras funcionalidades)
EXPOSE 8080

# Comando padrão
CMD ["python", "/app/docker-entrypoint.py"]