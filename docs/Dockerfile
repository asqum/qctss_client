FROM ghcr.io/astral-sh/uv:debian-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build tools
RUN apt-get update && apt-get install -y \
    git pandoc make curl zip unzip fontconfig \
    fonts-noto-cjk \
    fonts-noto-mono \
    fonts-roboto && \
    rm -rf /var/lib/apt/lists/*

# Install Roboto Flex font
RUN mkdir -p /usr/share/fonts/truetype/roboto-flex && \
    curl -L https://github.com/google/fonts/raw/main/ofl/robotoflex/RobotoFlex%5BGRAD%2CXOPQ%2CXTRA%2CYOPQ%2CYTAS%2CYTDE%2CYTFI%2CYTLC%2CYTUC%2Copsz%2Cslnt%2Cwdth%2Cwght%5D.ttf -o /usr/share/fonts/truetype/roboto-flex/RobotoFlex.ttf

# Update font cache
RUN fc-cache -fv

# Prepare Python environment
RUN uv python install 3.12
RUN uv venv /.venv --python python3.12
ENV PATH="/.venv/bin:${PATH}"

RUN uv pip install --upgrade pip setuptools wheel

WORKDIR /app
