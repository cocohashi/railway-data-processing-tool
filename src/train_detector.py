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
        self.validity_percentage = config['train-detector']['validity-percentage']
        self.detection_threshold = config['train-detector']['detection-threshold']

        # Train Detection
        self.section_batches = self.compute_section_batches()
        self.section_status = self.compute_section_status()

    @staticmethod
    def get_rms(section, axis=0):
        return np.sqrt(np.mean(section ** 2, axis=axis))

    # Methods
    def compute_section_batches(self):
        return [{key: self.batch[:, value[0]:value[1]]} for key, value in self.section_map.items()]

    def train_detector_mode_0(self, section):
        buff_rms = self.get_rms(section)

        # Debug -------------------------------------------------------
        logger.debug(f"[RMS MEAN]: {round(np.mean(buff_rms), 5)}")
        # -------------------------------------------------------------

        detected_idx = np.where(buff_rms > self.detection_threshold)[0]
        _, counts = np.unique(np.diff(detected_idx), return_counts=True)

        if counts.size > 0:
            return counts[0] >= self.spatial_window
        return False

    def train_detector_mode_1(self, section):
        buff_rms = self.get_rms(section)
        number_of_valid_samples = int(self.validity_percentage * len(buff_rms))

        # Debug -------------------------------------------------------
        logger.debug(f"[RMS MEAN]: {round(np.mean(buff_rms), 5)}")
        logger.debug(f"[VALID SAMPLES]: {number_of_valid_samples}")
        # -------------------------------------------------------------

        if len(list(filter(lambda x: x >= self.detection_threshold, buff_rms))) > number_of_valid_samples:
            return True
        return False

    def compute_section_status(self):
        return [{"section-id": list(section.keys())[0],
                 "status": self.train_detector_mode_1(list(section.values())[0]),
                 "initial-timestamp": time.time(),
                 "batch-data": list(section.values())[0]}
                for section in self.section_batches]

    # Getters
    def get_section_status(self):
        return self.section_status

    def get_section_batches(self):
        return self.section_batches

    def get_temporal_length(self):
        return self.batch.shape[0]

    def get_spatial_length(self):
        return self.batch.shape[1]
