# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install -g npm@10.9.0
RUN npm install
COPY . ./
RUN npm run build
