FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application files
COPY app/ ./app/
COPY public/ ./public/
COPY next.config.js ./
COPY tsconfig.json ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Build Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Run Next.js
CMD ["npm", "run", "dev"]
