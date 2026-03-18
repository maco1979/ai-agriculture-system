FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm install --no-cache

COPY src/ ./src/

EXPOSE 8080

CMD ["node", "src/main.js"]