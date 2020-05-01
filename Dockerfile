FROM alpine:3.11
RUN apk add --update py3-flask py3-requests
ADD icecast-balancer.py .
CMD [ "python3", "/icecast-balancer.py" ]