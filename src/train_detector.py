import os
import numpy as np
from uuid import uuid4

import logging

# -------------------------------------------------------------------------------------------------------------------
# Set Logger
# -------------------------------------------------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler() if os.environ['ENVIRONMENT'] == 'develop' else logging.FileHandler('main.log')
logger.setLevel(logging.INFO)
formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)


# -----------------------------------------------------------------------------------------------------------------


class TrainDetector:
    def __init__(self, batch, **config):
        self.batch = batch
        self.section_map = config['section-map']

        # Detection Parameters
        self.spatial_window = 2
        self.detection_threshold = 3

        # Train Detection
        self.section_batches = self.compute_section_batches()
        self.section_status = self.compute_section_status()

    # Methods
    def compute_section_batches(self):
        return [{key: self.batch[:, value[0]:value[1]]} for key, value in self.section_map.items()]

    @staticmethod
    def get_rms(section, axis=0):
        return np.sqrt(np.mean(section ** 2, axis=axis))

    def train_detector(self, section):
        buff_rms = self.get_rms(section)
        detected_idx = np.where(buff_rms > self.detection_threshold)[0]
        _, counts = np.unique(np.diff(detected_idx), return_counts=True)

        if counts.size > 0:
            return counts[0] >= self.spatial_window
        return False

    def compute_section_status(self):
        return [{"section-id": list(section.keys())[0],
                 "batch-id": uuid4(),
                 "status": self.train_detector(list(section.values())[0]),
                 "batch": self.batch}
                for section in self.section_batches]

    # Getters
    def get_section_status(self):
        return self.section_status

    def get_section_batches(self):
        return self.section_batches
