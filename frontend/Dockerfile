# ========================================
# Builder Stage: Install deps and build
# ========================================
FROM node:20-alpine AS builder

ARG NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=${NODE_ENV}

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm ci

COPY . .

RUN if [ "$NODE_ENV" = "production" ]; then \
      npm run build; \
    else \
      true; \
    fi

# ========================================
# Installer Stage: Production deps only
# ========================================
FROM node:20-alpine AS installer

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm ci --omit=dev

# ========================================
# Runner Stage: Final production image
# ========================================
FROM node:20-alpine AS runner

ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV} \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

WORKDIR /app

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=installer --chown=nextjs:nodejs /app/node_modules ./node_modules

COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

EXPOSE 3000

USER nextjs

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["npm", "run", "start"]
