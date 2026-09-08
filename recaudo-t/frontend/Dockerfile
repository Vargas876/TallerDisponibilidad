# RECAUDO-T — frontend Next.js (standalone)
# npm install (no npm ci): el lock generado en win32 omite optional deps de
# plataformas (alpine/musl -> @emnapi/*) y npm ci los rechaza con EUSAGE.
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --no-audit --no-fund
COPY . .
ARG NEXT_PUBLIC_DISPATCHER_URL=http://localhost:8000
ENV NEXT_PUBLIC_DISPATCHER_URL=$NEXT_PUBLIC_DISPATCHER_URL
RUN npm run build

FROM node:24-alpine
ENV NODE_ENV=production
WORKDIR /app
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]