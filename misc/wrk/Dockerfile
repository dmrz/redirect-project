FROM alpine:3
RUN apk update && apk add wrk
COPY scripts /scripts
ENTRYPOINT ["/usr/bin/wrk"]