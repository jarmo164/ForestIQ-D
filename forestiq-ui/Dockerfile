FROM node:22-alpine AS build

WORKDIR /app
RUN corepack enable

COPY forestiq-ui/package.json forestiq-ui/pnpm-lock.yaml ./
COPY forestiq-ui/patches ./patches
RUN corepack prepare pnpm@10.15.1 --activate && pnpm install --frozen-lockfile

COPY forestiq-ui/ ./
RUN pnpm build

FROM nginx:1.27-alpine

COPY forestiq-ui/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist/public /usr/share/nginx/html

EXPOSE 80
