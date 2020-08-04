class DockerClient(object):

    def __init__(self, client):
        self.client = client

    def get_container(self, container_id):
        return self.client.containers.get(container_id)

    def run(self, image, **kwargs):
        return self.client.containers.run(image, **kwargs)

    def port(self, container_id, port):
        return self.client.api.port(container_id, port)[0]["HostPort"]
