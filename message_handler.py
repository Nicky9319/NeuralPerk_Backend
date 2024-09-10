from enum import Enum
import time
import render_handler

class MessageTypes(Enum):
    MISC = 0
    RESPONSE = 1
    USER_MESSAGE = 2
    MODEL = 3
    MESSAGE = 4
    RENDER_REQUEST = 5
    RENDER_FULFIL = 6

def add_frames_to_queue(new_frames):
    render_handler.queue_new_frames(new_frames)


if __name__ == "__main__":
    for i in range(1, 5):
        add_frames_to_queue([i])
        time.sleep(1)


def save_rendered_image():
    pass

class Message:
    def __init__(self, type: MessageTypes, data, elapsed_time: float = time.time()) -> None:
        self.type = type
        self.data = data
        self.elapsed_time = elapsed_time

    def process_receiver_side(self):
        if self.type == MessageTypes.MESSAGE:
            print(self.data)
        
        if self.type == MessageTypes.RESPONSE:
            print("response", self.data)
        
        if self.type == MessageTypes.MODEL:
            t1 = time.time()
            print("Received Model")
            t2 = self.elapsed_time
            print("Time Taken to Send Model : " , t1-t2)
        
        if self.type == MessageTypes.RENDER_REQUEST:
            assert type(self.data) is list
            add_frames_to_queue()

        if self.type == MessageTypes.RENDER_FULFIL:
            save_rendered_image()
        
        