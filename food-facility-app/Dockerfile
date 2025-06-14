# Build stage
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

# Production stage (serve with nginx)
FROM nginx:alpine

# Copy build files to nginx html folder
COPY --from=build /app/dist /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf
# Expose nginx port
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
