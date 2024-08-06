import os
import logging
import numpy as np
import time

from src.data_loader import DataLoader
from src.signal_processor import SignalProcessor

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


class BatchDataGenerator:
    def __init__(self, data_path, **config):
        self.data_path = data_path
        self.config = config
        self.filenames = [filename for filename in os.listdir(data_path)]
        self.max_files = 3
        self.temporal_len = 0
        self.spatial_len = 0
        self.batch_temporal_length = 5  # seconds
        self.fs = 1000
        self.N = 1
        self.dt = (1 / self.fs) * self.N

    def __iter__(self):
        for sample in range(self.max_files):
            t0 = time.time()
            data = DataLoader(fullpath=os.path.join(self.data_path, self.filenames[sample])).get_data()
            filtered_data = SignalProcessor(data=data, **self.config).get_filtered_data()
            self.temporal_len = filtered_data.shape[0]
            self.spatial_len = filtered_data.shape[1]
            batch_idx = int(self.batch_temporal_length / self.dt)
            new_batch_idx = self.get_closest_divisor(self.temporal_len, batch_idx)

            for x in range(0, self.temporal_len, new_batch_idx):
                batch = filtered_data[x: x + new_batch_idx, :]
                t1 = time.time()
                time.sleep(max(0.0, self.batch_temporal_length - (t1 - t0)))
                yield batch

    @staticmethod
    def get_closest_divisor(n, m):
        """Find the divisor of n closest to m
        """
        divisors = np.array([i for i in range(1, int(np.sqrt(n) + 1)) if n % i == 0])
        divisions = n / divisors
        return int(divisions[np.argmin(np.abs(m - divisions))])
