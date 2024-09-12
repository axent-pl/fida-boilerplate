FROM kong:3.5.0

USER root
RUN apt update && \
    apt install -y curl && \
    curl -sL https://github.com/kong/deck/releases/download/v1.30.0/deck_1.30.0_linux_amd64.tar.gz -o deck.tar.gz && \
    tar -xf deck.tar.gz -C /tmp && \
    mv /tmp/deck /usr/local/bin/

COPY --chown=kong:kong docker-entrypoint-wrapper.sh /docker-entrypoint-wrapper.sh
COPY --chown=kong:kong kong.yaml /opt/kong/kong.yaml

USER kong
ENTRYPOINT [ "/docker-entrypoint-wrapper.sh" ]