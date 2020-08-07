### Observer hub

```
docker run --network host \
-v ${PWD}/config:/tmp/browser_hub \
-v /var/run/docker.sock:/var/run/docker.sock \
-e TZ=UTC getcarrier/observer_hub:latest
```

#### Config

Create config.json file

```
{
    "chrome": {
        "default": "83.0",
        "versions":{
            "83.0":{
                "image": "getcarrier/observer-chrome:latest"
            }
        }
    }
}
```
