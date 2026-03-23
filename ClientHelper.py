from collections import deque
import time


class ClientHelper:
    logout_deque = deque(maxlen=200)

    def __init__(self, client):
        self._client = client
        self.messages_queue = deque(maxlen=20)

    def last_seen(self):
        return self._client.last_seen

    def send(self, message):
        self.messages_queue.append(message)

    def dead(self):
        ClientHelper.logout_deque.append(self._client)

    def Update(self, dt):
        # remove the player if they haven't been heard from in a while
        if time.perf_counter() - self.last_seen() > 5:
            print("logging out ", self.parent.name, time.perf_counter() - self.last_seen())
            # use the client method in case extra cleanup is added later
            # needs to use despawned for clean up
            self._client.log_out()
