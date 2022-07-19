#!/bin/sh
# (c) Studio73 - Pablo Fuentes <pablo@studio73.es>
set -e
if [ -z $TARGET ]; then
    echo "Missing TARGET enviroment variable"
    exit 75
else
    sed -i 's/TARGET/'"$TARGET"'/g' /etc/nginx/conf.d/default.conf
fi

if [ $PORT ] && [ ! -f /etc/nginx/conf.d/port.conf ]; then
    echo -e "
server {
    listen $PORT;
    proxy_pass $TARGET:$PORT;
}
" >> /etc/nginx/conf.d/port.conf
fi

# Override dns nameserver to avoid Docker to resolve itself
echo "nameserver 1.1.1.1" > /etc/resolv.conf
exec "$@"
