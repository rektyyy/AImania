import socket
import struct
import time
import signal
import numpy as np
import random
import cv2
from tminterface.structs import SimStateData, CheckpointData
from PIL import Image
from tminterface2 import MessageType, TMInterface
from imageprocessing import Imageprocessing
import sys, os

HOST = "127.0.0.1"
PORT = 8478
WIDTH = 320
HEIGHT = 320
HEIGHT_MULT_UP = 0.9
HEIGHT_MULT_LOW = 0.3
NEW_HEIGHT = int(HEIGHT * HEIGHT_MULT_UP) - int(HEIGHT * HEIGHT_MULT_LOW)
N_RAYS = 32

def main():
    first_state = 0

    frame = 0

    ticks_per_second = 0
    now = time.time()

    iface = TMInterface(HOST, PORT, WIDTH, HEIGHT, HEIGHT_MULT_UP, HEIGHT_MULT_LOW)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    signal.signal(signal.SIGINT, iface.signal_handler)
    sock.connect((HOST, PORT))
    iface.sock = sock
    print('Connected')
    
    imageprocessor = Imageprocessing(N_RAYS, WIDTH, NEW_HEIGHT)
    # Add commands in reverse order
    beforeGameSetupCommands = ['map "My Challenges\mytrack.Challenge.Gbx"',
                               "set skip_map_load_screens true",
                               "set autologin 1"]
    
    for c in beforeGameSetupCommands:
        iface.execute_command(c)

    inGameSetupCommands = ["cam 3"]
    while True:
        message_type = struct.unpack('i', sock.recv(4))[0]
        if message_type == MessageType.SC_RUN_STEP_SYNC.value:

            state_length = struct.unpack('i', sock.recv(4))[0]
            state = SimStateData(sock.recv(state_length))
            state.cp_data.resize(CheckpointData.cp_states_field, state.cp_data.cp_states_length)
            state.cp_data.resize(CheckpointData.cp_times_field, state.cp_data.cp_times_length)

            race_time = state.player_info.race_time
            if race_time > 60000: #minuta
                #give_up(sock)
                iface.rewind_to_state(first_state)
            
            if race_time == 0:
                first_state = state
                for c in inGameSetupCommands:
                    iface.execute_command(c)

            upOrDown = random.randint(0, 1)
            #steer = random.randint(-65536, 65536)
            #set_input_state(sock, up=True, steer=steer)

    
            iface.respond(MessageType.SC_RUN_STEP_SYNC.value)

            if time.time() - now > 0.1:
                iface.request_frame()
                os.system('cls')
                print()
                print(imageprocessor.last_obs)
                print(f'Effective speed: {ticks_per_second / 10}x')
                # Pozycja gracza [przod/tyl, gora/dol, lewo/prawo]
                print(state.dyna.current_state.position)

                # Szybkosc gracza [przod/tyl, gora/dol, lewo/prawo]
                print(state.dyna.current_state.linear_speed)

                # Rotacja gracza (macierz 3x3 nie rozumiem wartosci)
                # print(state.dyna.current_state.rotation)

                # Czy kola maja kontakt z torem
                # Czy sie slizgaja kola
                ground_contact = []
                sliding = []
                for wheel in state.simulation_wheels:
                    ground_contact.append(wheel.real_time_state.has_ground_contact)
                    sliding.append(wheel.real_time_state.is_sliding)
                print(ground_contact)
                print(sliding)
                print()
                
                now = time.time()
                ticks_per_second = 0

            ticks_per_second += 1
        elif message_type == MessageType.SC_REQUESTED_FRAME_SYNC.value:
            iface.respond(MessageType.SC_REQUESTED_FRAME_SYNC.value)
            frame = iface.get_frame()
            frame = imageprocessor.create_blackwhite_frame(frame)
            image = imageprocessor.show_rays(frame)
            image.save('output_image_blackwhite.png')
            #image.show()

if __name__ == "__main__":
    main()