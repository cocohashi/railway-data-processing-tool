import os
import numpy as np
import time
from dotenv import load_dotenv

from src.data_loader import DataLoader
from src.signal_processor import SignalProcessor
from src.logger import load_logger

load_dotenv()
logger = load_logger(__name__)


class BatchDataGenerator:
    def __init__(self, data_path, **config):
        self.data_path = data_path
        self.config = config
        self.max_files = config['batch-data-generator']['max-files']
        self.batch_waiting_time = config['batch-data-generator']['waiting-time']

        self.filenames = [filename for filename in os.listdir(data_path)]
        self.temporal_len = 0
        self.spatial_len = 0

        self.N = config['signal']['N']
        self.fs = config['signal']['fs']  # Frequency [Hz]
        self.dt = self.N * (1 / self.fs)  # Time [s]

        self.batch_temporal_length = config['params']['temporal-resolution']  # Time [s]

    def __iter__(self):
        for sample in range(min(self.max_files, len(self.filenames))):
            data = DataLoader(fullpath=os.path.join(self.data_path, self.filenames[sample])).get_data()
            filtered_data = SignalProcessor(data=data, **self.config).get_filtered_data()
            self.temporal_len = filtered_data.shape[0]
            self.spatial_len = filtered_data.shape[1]
            batch_idx = int(self.batch_temporal_length / self.dt)
            new_batch_idx = self.get_closest_divisor(self.temporal_len, batch_idx)

            for x in range(0, self.temporal_len, new_batch_idx):
                batch = filtered_data[x: x + new_batch_idx, :]
                time.sleep(self.batch_waiting_time)
                yield batch

    @staticmethod
    def get_closest_divisor(n, m):
        """Find the divisor of n closest to m
        """
        divisors = np.array([i for i in range(1, int(np.sqrt(n) + 1)) if n % i == 0])
        divisions = n / divisors
        return int(divisions[np.argmin(np.abs(m - divisions))])
