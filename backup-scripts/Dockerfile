FROM alpine:3.18

RUN apk add --no-cache \
    bash \
    postgresql-client \
    curl \
    gzip \
    tar \
    openssl \
    dcron \
    sudo \
    coreutils \
    util-linux \
    bc && \
    ARCH=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/') && \
    curl -fsSL "https://dl.min.io/client/mc/release/linux-${ARCH}/mc" -o /usr/local/bin/minio-mc && \
    chmod +x /usr/local/bin/minio-mc

# Create non-root user for backup operations
RUN addgroup -g 1001 backup && \
    adduser -D -u 1001 -G backup backup && \
    echo "backup ALL=(ALL) NOPASSWD: /usr/sbin/crond" >> /etc/sudoers

WORKDIR /backup

COPY backup.sh /backup/
COPY restore.sh /backup/
COPY entrypoint.sh /backup/

RUN chmod +x /backup/*.sh && \
    mkdir -p /backups /var/log && \
    chown -R backup:backup /backups /backup && \
    touch /var/log/backup.log && \
    chown backup:backup /var/log/backup.log

# Run as root for cron, but backups will execute as backup user
ENTRYPOINT ["/backup/entrypoint.sh"]