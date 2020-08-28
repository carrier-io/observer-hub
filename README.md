### Observer hub

```
docker run --network host \
-v /tmp/hub:/tmp/hub \
-v /var/run/docker.sock:/var/run/docker.sock \
-e TOKEN=${CARRIER_AUTH_TOKEN} \
getcarrier/observer-hub:latest
```

#### Config

Create config.json file

```
{
    "chrome": {
        "default": "83.0",
        "versions":{
            "83.0":{
                "image": "getcarrier/observer-chrome:latest",
                "env": {
                    "VNC_NO_PASSWORD": 1
                }
            }
        }
    }
}
```
