import os
import numpy as np

import logging

from src.train_detector import TrainDetector

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


# class BufferManager:
class BufferManager:
    def __init__(self, batch, **config):
        self.batch = batch
        self.config = config

        # Signal Config
        self.N = config['signal']['N']
        self.fs = config['signal']['fs']  # Frequency [Hz]

        # Section Map Config
        self.section_map = config['section-map']

        # Batch Manager Config
        self.batch_time = config['buffer-manager']['batch-time']  # Time [s]
        self.spatial_resolution = config['buffer-manager']['spatial-resolution']  # Space [m]
        self.section_train_speed_mean = config['buffer-manager']['section-train-speed-mean']  # Speed [Km / h]
        self.start_margin_time = config['buffer-manager']['start-margin-time']  # Time [s]
        self.end_margin_time = config['buffer-manager']['end-margin-time']  # Time [s]

        # Local variables (inputs)
        self.dt = self.N * (1 / self.fs)  # Time [s]
        self.train_time_width = 1.25  # Time [s]
        self.section_number = len(self.section_map.keys())

        # Local variables (outputs)
        self.section_train_speed_mean_ms = [speed / 3.6 for speed in self.section_train_speed_mean]  # Speed [m / s]
        self.section_map_index_ranges = [np.diff(ranges)[0] for ranges in self.section_map.values()]  # Index
        self.section_map_space_ranges = list(
            np.multiply(self.spatial_resolution, self.section_map_index_ranges))  # Space [m]
        self.section_map_time_ranges = [self.section_map_space_ranges[i] / self.section_train_speed_mean_ms[i] for i in
                                        range(self.section_number)]  # Time [s]
        self.section_map_train_time_ranges = [time + self.train_time_width for time in
                                              self.section_map_time_ranges]  # Time [s]

        self.start_margin_batch_number = int(np.round(self.start_margin_time / self.batch_time))
        self.buffer_time = self.batch_time * self.start_margin_batch_number
        self.output_block_time = [self.start_margin_time + section_time + self.end_margin_time for section_time in
                                  self.section_map_train_time_ranges]
        self.num_batches_to_save = [int(np.round(time / self.batch_time)) for time in self.output_block_time]
        self.buffer_batch_num = max(self.num_batches_to_save)
        self.batch_index_ref = [(self.buffer_batch_num - batch + self.start_margin_batch_number) for batch in
                                self.num_batches_to_save]

        # self._info()
        self.train_detector()

    def print_info(self):
        logger.info("\n ===========================\n     Buffer Manager Info    \n ===========================")
        print("\n INPUT VALUES:\n")
        print("  Signal: ")
        print(f" --> Down-sampling Factor:              {self.N} ")
        print(f" --> Sampling Rate [Hz]:                {self.fs}")
        print(f" --> Sampling Time [s]:                 {self.dt}\n")
        print("  Section Map: ")
        print(f"  --> Number of Sections:               {self.section_number}")
        print(f"  --> Section ID's:                     {list(self.section_map.keys())}")
        print(f"  --> Train Time Width [s]:             {self.train_time_width}")
        print(f"  --> Section Map:                      {self.section_map}\n")
        print("  Batch Manager: ")
        print(f"  --> Batch Time [s]:                   {self.batch_time}")
        print(f"  --> Spatial Resolution [m]:           {self.spatial_resolution}")
        print(f"  --> Train Speed Mean's [Km/h]:        {self.section_train_speed_mean}")
        print(f"  --> Start Margin Time [s]:            {self.start_margin_time}")
        print(f"  --> End Margin Time [s]:              {self.end_margin_time}")
        print("\n OUTPUT VALUES:\n")
        print("  Section Map: ")
        print(f"  --> Index Ranges:                     {self.section_map_index_ranges}")
        print(f"  --> Time Ranges [s]:                  {self.section_map_time_ranges}")
        print(f"  --> Time Range + Train Width [s]:     {self.section_map_train_time_ranges}")
        print(f"  --> Space Ranges [m]:                 {self.section_map_space_ranges}")
        print(f"  --> Numb. of Batches at Start Margin: {self.start_margin_batch_number}")
        print(f"  --> Buffer Time:                      {self.buffer_time}")
        print(f"  --> Numb. of Batches in Buffer:       {self.buffer_batch_num}")
        print(f"  --> Numb. of Batches to Save per Sec: {self.num_batches_to_save}")
        print(f"  --> Buffer's Batch index reference:   {self.batch_index_ref}")
        print(f"  ----------------------------------------------------------------------------------------------------")

    def train_detector(self):
        section_status = TrainDetector(self.batch, **self.config).get_section_status()
        section_status_info = [{"section-id": ss.get("section-id"),
                                "status": ss.get("status")}
                               for ss in section_status]
        logger.info(f"section_status_info: {section_status_info}")
