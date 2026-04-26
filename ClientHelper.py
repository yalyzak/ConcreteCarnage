from collections import deque
import time


class ClientHelper:
    logout_deque = deque(maxlen=200)

    def __init__(self, client):
        """Initialize helper with client reference and message queues."""
        self._client = client
        self.messages_queue = deque(maxlen=20)
        self.chat_queue = deque(maxlen=10)

    def last_seen(self):
        """Get timestamp of last client activity."""
        return self._client.last_seen

    def send_udp(self, message):
        """Queue message for UDP transmission."""
        self.messages_queue.append(message)

    def broadcast_tcp(self, message):
        """Queue message for TCP broadcast."""
        self.chat_queue.append(message)

    def dead(self):
        """Mark client for logout due to inactivity."""
        ClientHelper.logout_deque.append(self._client)

    def Update(self, dt):
        """Check for client timeout and remove inactive players."""
        # remove the player if they haven't been heard from in a while
        if time.perf_counter() - self.last_seen() > 5:
            print("logging out ", self.parent.name, time.perf_counter() - self.last_seen())
            # use the client method in case extra cleanup is added later
            # needs to use despawned for clean up
            self._client.log_out()
