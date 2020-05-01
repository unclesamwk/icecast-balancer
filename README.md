# icecast-balancer

The prerequisite for using the icecast balancer productively is an icecast master-relay setup or all relays have the same mounts.

https://www.icecast.org/docs/icecast-trunk/relaying/

## start container
```
docker run -itd \
  -p 8080:8080 \
  -e ICECAST_SERVERS='server1.example.com,server2.example.com' \
  unclesamwk/icecast-balancer:latest
```
## use icecastbalancer

When the icecast balancer is started you can see the number of listeners for each specified server under the url http://0.0.0.0:8080/status.

```
curl "http://0.0.0.0:8080/status"
{"message":"No iceastrelay is reachable!"}
```
or valid status with count of listeners for every icecast server
```
curl "http://0.0.0.0:8080/status"
{
    "server1.example.com":"55"
    "server2.example.com":"15"
}
```
If you want to call up a stream, just enter the url of the icecast-balancer and the path.

Example: http://0.0.0.0:8080/stream

### contributing

Pull requests are welcome