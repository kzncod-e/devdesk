FROM node:22-alpine AS build
WORKDIR /srv
COPY package.json package-lock.json ./
# --ignore-scripts: postinstall runs `nuxt prepare`, which needs the full source
RUN npm ci --ignore-scripts
COPY . .
ARG API_PROXY_TARGET=http://api:8000
ENV API_PROXY_TARGET=$API_PROXY_TARGET
RUN npm run build

FROM node:22-alpine
WORKDIR /srv
ENV NODE_ENV=production
COPY --from=build /srv/.output ./.output
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
