FROM alpine:3.18

RUN apk add --no-cache \
    bash \
    postgresql-client \
    mc \
    curl \
    gzip \
    tar \
    openssl \
    dcron

WORKDIR /backup

COPY backup.sh /backup/
COPY restore.sh /backup/
COPY entrypoint.sh /backup/

RUN chmod +x /backup/*.sh

ENTRYPOINT ["/backup/entrypoint.sh"]