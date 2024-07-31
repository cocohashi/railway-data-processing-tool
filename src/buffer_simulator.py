import os
import logging
import numpy as np

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
# -----------------------------------------------------------------------------------------------------------------

class BufferSimulator:
    def __init__(self, data_path, **config):
        self.data_path = data_path
        self.config = config
        self.filenames = [filename for filename in os.listdir(data_path)]
        self.max_files = 4
        self.slots = 2
        self.spatial_len = 2478
        self.start = True
        self.buffer = np.ndarray(shape=(0, self.spatial_len))

    def __iter__(self):
        for sample in range(self.max_files):
            data = DataLoader(fullpath=os.path.join(self.data_path, self.filenames[sample])).get_data()
            filtered_data = SignalProcessor(data=data, **self.config).get_filtered_data()
            temporal_len = filtered_data.shape[0]

            if self.buffer.shape[0] >= temporal_len * self.slots:
                if self.start:
                    self.start = False
                    yield self.buffer

                self.buffer = np.concatenate((self.buffer, filtered_data))
                new_buffer = self.buffer[temporal_len:, :]
                self.buffer = new_buffer
                yield self.buffer

            else:
                self.buffer = np.concatenate((self.buffer, filtered_data))
