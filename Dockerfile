# KiroCrew gateway for Railway: the official image, pinned by version and digest,
# behind a small Caddy front that adds a password-protected /login link minter.
FROM caddy:2.11.9@sha256:4851e54a46b206517c574821bb5cc67f170d2156041e9fbc4c9193b45e84a75b AS caddy

FROM ghcr.io/kirodotdev/kirocrew:0.13.1@sha256:080c81417fd67d03ca28fdd983cb309efbcea8ee618adaeeb75a2ed96bcf58d1

USER root
COPY --from=caddy /usr/bin/caddy /usr/local/bin/caddy
COPY rootfs/ /
RUN chmod 755 /usr/local/bin/railway-start /usr/local/bin/crew /usr/local/bin/kiro-login \
 && chmod 644 /etc/railway/Caddyfile /usr/local/lib/railway/login_helper.py \
 && caddy version \
 && H="$(caddy hash-password --plaintext build-time-check)" \
 && PORT=8080 KIROCREW_INTERNAL_PORT=5476 KIROCREW_LOGIN_PORT=5477 KIROCREW_LOGIN_USER=admin KIROCREW_LOGIN_HASH="$H" caddy validate --config /etc/railway/Caddyfile --adapter caddyfile

# Starts as root only to fix the Railway volume's ownership; every process then
# runs as the image's non-root "kirocrew" user.
ENV PORT=8080
EXPOSE 8080
ENTRYPOINT ["tini", "-g", "--", "/usr/local/bin/railway-start"]
