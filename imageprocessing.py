import numpy as np
import cv2
from PIL import Image

class Imageprocessing():
    def __init__(self, n_rays, width, height):
        self.n_rays = n_rays
        self.width = width
        self.height = height
        self.last_frame = None
        self.last_obs = None
        self.last_rays = None

    # Function to process frames
    def create_blackwhite_frame(self, blackwhite_data):
        blackwhite_data = np.array(blackwhite_data, dtype=np.uint8).reshape((self.height, self.width))
        edges = cv2.Canny(blackwhite_data, threshold1=80, threshold2=300)
        dilation = cv2.dilate(edges, np.ones((7, 7)), iterations=1)
        softedges = cv2.GaussianBlur(dilation, (9, 9), 1)
        binary_image_array = (softedges > 128).astype(np.uint8) * 255
        return binary_image_array

    def is_in_frame(self, frame, x, y):
        return 0 <= x < len(frame[0]) and 0 <= y < len(frame)

    def find_end(self, frame, angle):
        x = len(frame[0]) // 2
        y = len(frame) - 1

        dx = np.cos(angle)
        dy = np.sin(angle)

        while self.is_in_frame(frame, x, y,) and frame[int(y)][int(x)] == 0:
            x += dx
            y -= dy
        return [int(x), int(y)]

    # Uzywamy skalowania aby zachowac odpowiednie odleglosci
    def scaling_func(self, angle):
            return (1 + 3 * np.sin(angle)) / 4

    def get_distance(self, point, ref_size, ref_point, angle=0):
        return (
            self.scaling_func(angle)
            * np.linalg.norm(np.array(point) - np.array(ref_point), 2)
            / ref_size
        )

    def get_rays(self, frame):
        rays = []
        angles = []
        for i in range(self.n_rays):
            angle = i * np.pi / (self.n_rays - 1)
            rays.append(self.find_end(frame, angle))
            angles.append(angle)
        self.last_rays = rays
        return rays, angles

    def get_obs(self, frame):
        frame = self.create_blackwhite_frame(frame)
        ref_size = np.hypot(frame.shape[0], frame.shape[1]) / 2
        rays, angles = self.get_rays(frame)
        ref_point = (len(frame[0]) // 2, len(frame) - 1)
        distances = [self.get_distance(ray, ref_size, ref_point, angle) for ray, angle in zip(rays, angles)]
        self.last_obs = np.array(distances).astype(np.float32)
        return self.last_obs

    def show_rays(self, frame):
        _ = self.get_obs(frame)
        ref_point = (len(frame[0]) // 2, len(frame) - 1)
        for ray in self.last_rays:
            cv2.line(frame, ref_point, tuple(ray), (128, 0, 0), 1)
        self.last_frame = Image.fromarray(frame, 'L')
        return self.last_frame