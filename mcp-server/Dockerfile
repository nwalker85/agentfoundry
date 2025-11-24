FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source and build
COPY tsconfig.json ./
COPY src ./src

# Build TypeScript
RUN npm install -D typescript
RUN npm run build

# Expose SSE port (optional, for web clients)
EXPOSE 3100

# Default to stdio (for MCP clients like Cursor)
CMD ["node", "dist/index.js"]

