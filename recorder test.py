import time
from Movement import Recorder

def real_mouse_test():
    """Test real-time keyboard and mouse input recording."""
    rec = Recorder(keys=["w", "a", "s", "d"], enable_hooks=True)

    print("Click LEFT mouse quickly several times...")
    print("Recording for 5 seconds...\n")

    start = time.time()
    frames = []

    while time.time() - start < 5:
        data = rec.keyboard_recorder()
        frames.append(data)
        print(data)
        time.sleep(1/60)  # simulate game loop (60 FPS)

    # check if any click was detected
    detected = any(frame[4] for frame in frames)

    print("\nDetected click:", detected)


if __name__ == "__main__":
    real_mouse_test()