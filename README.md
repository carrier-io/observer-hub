### Observer hub

```
docker run  --network host -v /var/run/docker.sock:/var/run/docker.sock -e TZ=UTC getcarrier/observer_hub:latest
```