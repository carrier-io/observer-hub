class DockerClient(object):

    def __init__(self, client):
        self.client = client

    def get_container(self, container_id):
        try:
            return DockerContainer(self.client.containers.get(container_id))
        except:
            return DockerContainer()

    def run(self, image, **kwargs):
        return self.client.containers.run(image, **kwargs)

    def port(self, container_id, port):
        return self.client.api.port(container_id, port)[0]["HostPort"]


class DockerContainer(object):

    def __init__(self, container=None):
        self.container = container

    def remove(self, force=False):
        if self.container:
            self.container.remove(force=force)
