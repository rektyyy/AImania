import socket
import struct
import time
import signal
import numpy as np
from tminterface.structs import SimStateData, CheckpointData
from PIL import Image

HOST = "127.0.0.1"
PORT = 8477

SC_RUN_STEP_SYNC = 0
C_SET_SPEED = 1
C_REWIND_TO_STATE = 2
C_SET_INPUT_STATE = 3
C_SHUTDOWN = 4
C_GIVE_UP = 5
C_EXECUTE_COMMAND = 6
C_REQUEST_FRAME = 7
SC_REQUESTED_FRAME_SYNC = 8

sock = None
width = 160
height = 90
requested_frames = 0

def signal_handler(sig, frame):
    global sock

    print('Shutting down...')
    sock.sendall(struct.pack('i', C_SHUTDOWN))
    sock.close()


def rewind_to_state(sock, state):
    sock.sendall(struct.pack('i', C_REWIND_TO_STATE))
    sock.sendall(struct.pack('i', len(state.data)))
    sock.sendall(state.data)

def set_input_state(sock, up=-1, down=-1, steer=0x7FFFFFFF):
    sock.sendall(struct.pack('i', C_SET_INPUT_STATE))
    sock.sendall(struct.pack('b', up))
    sock.sendall(struct.pack('b', down))
    sock.sendall(struct.pack('i', steer))

def give_up(sock):
    sock.sendall(struct.pack("i", C_GIVE_UP))

def execute_command(sock, command):
    sock.sendall(struct.pack("ii", C_EXECUTE_COMMAND, np.int32(len(command))))
    sock.sendall(command.encode())  # https://www.delftstack.com/howto/python/python-socket-send-string/

def request_frame(sock, W, H):
    global requested_frames
    requested_frames += 1
    sock.sendall(struct.pack("iii", C_REQUEST_FRAME, np.int32(W), np.int32(H)))

def get_frame(sock, width, height):
    global requested_frames
    if requested_frames == 0:
        raise Exception('cannot download frame')
    requested_frames -= 1
    frame_data = sock.recv(width * height * 1, socket.MSG_WAITALL)
    return np.frombuffer(frame_data, dtype=np.uint8).reshape((height, width, 1))

def respond(sock, type):
    sock.sendall(struct.pack('i', type))

# Function to test frames
def create_grayscale_image(grayscale_data, width, height):
    # Ensure grayscale_data is a numpy array with the correct dtype
    grayscale_data = np.array(grayscale_data, dtype=np.uint8).reshape((height, width))

    # Create a grayscale (L mode) image from the numpy array
    image = Image.fromarray(grayscale_data, 'L')

    return image

def main():
    global sock, width, height

    first_state = 0

    frame = 0

    ticks_per_second = 0
    now = time.time()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    signal.signal(signal.SIGINT, signal_handler)

    sock.connect((HOST, PORT))
    print('Connected')
    
    # Add commands in reverse order
    execute_command(sock, 'map "My Challenges\A01-Race.Challenge.Gbx"')
    execute_command(sock, "set skip_map_load_screens true")
    execute_command(sock, "set autologin 1")
    while True:
        message_type = struct.unpack('i', sock.recv(4))[0]
        if message_type == SC_RUN_STEP_SYNC:
            state_length = struct.unpack('i', sock.recv(4))[0]
            state = SimStateData(sock.recv(state_length))
            state.cp_data.resize(CheckpointData.cp_states_field, state.cp_data.cp_states_length)
            state.cp_data.resize(CheckpointData.cp_times_field, state.cp_data.cp_times_length)

            race_time = state.player_info.race_time
            # if race_time == 0:
            #     first_state = state
            #     set_input_state(sock, up=True)

            # if race_time == 3000:
            #     width = 1600
            #     height = 900
            #     request_frame(sock, width, height)
                #give_up(sock)
                #execute_command(sock, "vars")

            # if race_time > 0 and race_time % 5000 == 0 and first_state:
            #     rewind_to_state(sock, first_state)
            #     set_input_state(sock, up=True, steer=65536)

    
            respond(sock, SC_RUN_STEP_SYNC)

            if time.time() - now > 1:
                request_frame(sock, width, height)
                #print(f'Effective speed: {ticks_per_second / 100}x')

                # Pozycja gracza [przod/tyl, gora/dol, lewo/prawo]
                # print(state.dyna.current_state.position)

                # Szybkosc gracza [przod/tyl, gora/dol, lewo/prawo]
                # print(state.dyna.current_state.linear_speed)

                # Rotacja gracza (macierz 3x3 nie rozumiem wartosci)
                # print(state.dyna.current_state.rotation)

                # Czy kola maja kontakt z torem
                # Czy sie slizgaja kola
                # ground_contact = []
                # sliding = []
                # for wheel in state.simulation_wheels:
                #     ground_contact.append(wheel.real_time_state.has_ground_contact)
                #     sliding.append(wheel.real_time_state.is_sliding)
                # print(ground_contact)
                # print(sliding)
                now = time.time()
                ticks_per_second = 0

            ticks_per_second += 1
        elif message_type == int(SC_REQUESTED_FRAME_SYNC):
            respond(sock, SC_REQUESTED_FRAME_SYNC)
            frame = get_frame(sock, width, height)
            image = create_grayscale_image(frame, width, height)
            image.show()

if __name__ == "__main__":
    main()