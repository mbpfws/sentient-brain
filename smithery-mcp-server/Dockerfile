FROM node:18-alpine

# Install system dependencies needed for Crawlee
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    wget \
    xvfb

# Set environment variables for Puppeteer
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    DISPLAY=:99

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port the dev server runs on
EXPOSE 8182

# Start the server
# Build the server first, then run the output directly
CMD ["sh", "-c", "npx @smithery/cli build && node ./.smithery/index.cjs"]