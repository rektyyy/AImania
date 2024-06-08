import socket
import struct
import numpy as np
from enum import Enum
from tminterface.structs import SimStateData, CheckpointData


class MessageType(Enum):
    SC_RUN_STEP_SYNC = 0
    C_SET_SPEED = 1
    C_REWIND_TO_STATE = 2
    C_SET_INPUT_STATE = 3
    C_SHUTDOWN = 4
    C_GIVE_UP = 5
    C_EXECUTE_COMMAND = 6
    C_REQUEST_FRAME = 7
    SC_REQUESTED_FRAME_SYNC = 8
    C_GET_SIMULATION_STATE = 9

class TMInterface:
    def __init__(self, host, port, width, height, heightMultUp, heightMultLow):
        self.host = host
        self.port = port
        self.sock = None
        self.requested_frames = 0
        self.width = np.int32(width)
        self.heigth = np.int32(height)
        self.newHeightUp = np.int32(height * heightMultUp)
        self.newHeightLow = np.int32(height * heightMultLow)
     
    def signal_handler(self, sig, frame):

        print('Shutting down...')
        self.sock.sendall(struct.pack('i', MessageType.C_SHUTDOWN.value))
        self.sock.close()

    #TODO: fix
    def rewind_to_state(self, state):
        self.sock.sendall(struct.pack('i', MessageType.C_REWIND_TO_STATE.value))
        self.sock.sendall(struct.pack('i', len(state.data)))
        self.sock.sendall(state.data)

    def set_input_state(self, up=-1, down=-1, steer=0x7FFFFFFF):
        self.sock.sendall(struct.pack('i', MessageType.C_SET_INPUT_STATE.value))
        self.sock.sendall(struct.pack('b', up))
        self.sock.sendall(struct.pack('b', down))
        self.sock.sendall(struct.pack('i', steer))

    def give_up(self):
        self.sock.sendall(struct.pack("i", MessageType.C_GIVE_UP.value))

    def execute_command(self, command):
        self.sock.sendall(struct.pack("ii", MessageType.C_EXECUTE_COMMAND.value, np.int32(len(command))))
        self.sock.sendall(command.encode())  # https://www.delftstack.com/howto/python/python-socket-send-string/

    def request_frame(self):
        self.requested_frames += 1
        self.sock.sendall(struct.pack("iiiii", MessageType.C_REQUEST_FRAME.value, self.width, self.heigth, self.newHeightLow, self.newHeightUp))

    def get_frame(self):
        if self.requested_frames == 0:
            raise Exception('Cannot download frame')
        self.requested_frames -= 1
        frame_data = self.sock.recv((self.newHeightUp - self.newHeightLow) * self.width * 1, socket.MSG_WAITALL)
        return np.frombuffer(frame_data, dtype=np.uint8).reshape(((self.newHeightUp - self.newHeightLow), self.width, 1))

    def read_int32(self):
        return struct.unpack("i", self.sock.recv(4, socket.MSG_WAITALL))[0]

    def get_simulation_state(self):
        # message_type = iface.read_int32()
        # state_length = struct.unpack('i', sock.recv(4))[0]
        # state = SimStateData(sock.recv(state_length))
        # state.cp_data.resize(CheckpointData.cp_states_field, state.cp_data.cp_states_length)
        # state.cp_data.resize(CheckpointData.cp_times_field, state.cp_data.cp_times_length)

        self.sock.sendall(struct.pack("i", MessageType.C_GET_SIMULATION_STATE.value))
        state_length = self.read_int32()
        state = SimStateData(self.sock.recv(state_length, socket.MSG_WAITALL))
        state.cp_data.resize(CheckpointData.cp_states_field, state.cp_data.cp_states_length)
        state.cp_data.resize(CheckpointData.cp_times_field, state.cp_data.cp_times_length)
        return state

    def respond(self, type):
        self.sock.sendall(struct.pack('i', type))
