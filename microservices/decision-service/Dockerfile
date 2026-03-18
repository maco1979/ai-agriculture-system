FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci --only=production

COPY . .

EXPOSE 8002

ENV NODE_ENV=production

CMD ["node", "src/main.js"]
