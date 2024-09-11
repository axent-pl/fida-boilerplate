FROM kong:3.5.0

USER root
RUN apt update && \
    apt install -y curl && \
    curl -sL https://github.com/kong/deck/releases/download/v1.30.0/deck_1.30.0_linux_amd64.tar.gz -o deck.tar.gz && \
    tar -xf deck.tar.gz -C /tmp && \
    mv /tmp/deck /usr/local/bin/

COPY docker-entrypoint.sh /docker-entrypoint.sh

USER kong
COPY --chown=kong:kong kong.yaml /opt/kong/kong.yaml