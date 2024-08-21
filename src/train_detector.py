import numpy as np
import time
from uuid import uuid4
from dotenv import load_dotenv

from src.logger import load_logger

load_dotenv()
logger = load_logger(__name__)


class TrainDetector:
    def __init__(self, batch, **config):
        self.batch = batch
        self.section_map = config['section-map']

        # Detection Parameters
        self.spatial_window = config['train-detector']['spatial-window']
        self.detection_threshold = config['train-detector']['detection-threshold']

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
        batch_id = uuid4()
        return [{"section-id": list(section.keys())[0],
                 "batch-id": batch_id,
                 "status": self.train_detector(list(section.values())[0]),
                 "initial-timestamp": time.time(),
                 "batch-data": list(section.values())[0]}
                for section in self.section_batches]

    # Getters
    def get_section_status(self):
        return self.section_status

    def get_section_batches(self):
        return self.section_batches
