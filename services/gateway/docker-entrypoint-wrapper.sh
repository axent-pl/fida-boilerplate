#!/usr/bin/env bash
set -Eeo pipefail

axent_log() {
  CURRENT_TIME=$(date +"%Y/%m/%d %H:%M:%S")
  if [ -z "$2" ]; then
    M="info"
  else
    M=$2
  fi
  echo "$CURRENT_TIME [$M] axent-pl: $1"
}

echo "$(sed 's/${AS_HOST}/'$AS_HOST'/g' /opt/kong/kong.yaml)" > /opt/kong/kong.yaml
echo "$(sed 's/${AS_PORT}/'$AS_PORT'/g' /opt/kong/kong.yaml)" > /opt/kong/kong.yaml
echo "$(sed 's/${GW_ETL_HOST}/'$GW_ETL_HOST'/g' /opt/kong/kong.yaml)" > /opt/kong/kong.yaml
echo "$(sed 's/${GW_ETL_PORT}/'$GW_ETL_PORT'/g' /opt/kong/kong.yaml)" > /opt/kong/kong.yaml
echo "$(sed 's/${UPSTREAM_HOST}/'$UPSTREAM_HOST'/g' /opt/kong/kong.yaml)" > /opt/kong/kong.yaml
echo "$(sed 's/${UPSTREAM_PORT}/'$UPSTREAM_PORT'/g' /opt/kong/kong.yaml)" > /opt/kong/kong.yaml

AS_REALM_URL="${AS_ORIGIN}/auth/realms/${AS_REALM}"
while true; do
  AS_SIGN_KEY=$(curl -s -f $AS_REALM_URL 2>/dev/null | cut -d "," -f2 | cut -d ":" -f 2 | tr -d '"')
  if [ ! -z "$AS_SIGN_KEY" ]; then
    axent_log "public key fetched from AS"
    ESCAPED_AS_SIGN_KEY=$(echo "$AS_SIGN_KEY" | sed 's:/:\\/:g')
    echo "$(sed 's/${AS_SIGN_KEY}/'$ESCAPED_AS_SIGN_KEY'/g' /opt/kong/kong.yaml)" > /opt/kong/kong.yaml
    break
  fi
  axent_log "Could not fetch AS public key"
  sleep 5
done

load_config() {
  SECONDS=0
  axent_log "startup started"
  while true; do
    DURATION=$SECONDS
    if ! kong health 2>/dev/null; then
      axent_log "healthcheck failed, retrying..."
      sleep 1
    else
      axent_log "healthcheck successful"
      axent_log "startup done in $DURATION seconds"
      break
    fi
  done
  if [[ "$KONG_DATABASE" == "postgres" ]]; then
    axent_log "sync started"
    SECONDS=0
    deck gateway sync /opt/kong/kong.yaml
    DURATION=$SECONDS
    axent_log "sync done in $DURATION seconds"
  fi
}
load_config &

/docker-entrypoint.sh "kong" "docker-start"