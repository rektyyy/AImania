import gym
import numpy as np

class TMEnv(gym.Env):
    def __init__(self, threads=1, n_rays = 16):
        self.threads = threads

        # TODO: normalizacja do [0, 1]
        # Przestrzen akcji: [gaz, hamulec, skret]
        # Alternatywnie: [gaz, hamulec, lewo, prawo] 
        # Nie wiem tylko czy nie bedzie probowal model dwoch na raz lewo prawo
        self.action_space = gym.spaces.Box(low=np.array([0, 0, -65536]), high=np.array([1, 1, 65536]), dtype=np.int32)

        # TODO: normalizacja do [0, 1]
        # Przestrzeń stanów: [pozycja_x, pozycja_z, pozycja_y, prędkość_x, prędkość_z, prędkość_y, 
        #                     kontakt1, kontakt2, kontakt3, kontakt4, slizg1, slizg2, slizg3, slizg4
        #                     promien1, ... , promien n]
        self.observation_space = gym.spaces.Box(low=np.array([0, 0, 0, -130, -130, -130, 
                                                          0, 0, 0, 0, 0, 0, 0, 0] +
                                                          ([0] * n_rays)), 
                                            high=np.array([1500, 1500, 1500, 130, 130, 130,
                                                            1, 1, 1, 1, 1, 1, 1, 1] +
                                                            ([1] * n_rays)), 
                                            dtype=np.float32)
        
    
    def step(self, action):
        pass
    
    def reset(self):
        pass

    def render(self):
        pass