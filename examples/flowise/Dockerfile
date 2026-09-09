FROM node:24-alpine AS build
RUN apk add --no-cache git python3 py3-pip py3-setuptools make g++ build-base cairo-dev pango-dev
ENV PUPPETEER_SKIP_DOWNLOAD=true
RUN npm install -g flowise@3.1.4 --legacy-peer-deps

FROM node:24-alpine
RUN apk add --no-cache chromium git python3 py3-pip py3-setuptools make g++ build-base cairo-dev pango-dev curl
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
COPY --from=build /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=build /usr/local/bin /usr/local/bin
RUN chown -R node:node /usr/local/lib/node_modules /usr/local/bin
USER node
EXPOSE 3000
ENTRYPOINT ["flowise", "start"]
