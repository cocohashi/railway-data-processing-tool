import os
import numpy as np

import logging

from src.train_detector import TrainDetector
from src.data_plotter import DataPlotter

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
    def __init__(self, **config):
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
        self.section_ids = list(self.section_map.keys())

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
        self.output_chunk_time = [self.start_margin_time + section_time + self.end_margin_time for section_time in
                                  self.section_map_train_time_ranges]
        self.num_batches_to_save = [int(np.round(time / self.batch_time)) for time in self.output_chunk_time]
        self.buffer_batch_num = max(self.num_batches_to_save)
        self.train_event_index_ref = [(self.buffer_batch_num - batch + self.start_margin_batch_number) for batch in
                                      self.num_batches_to_save]

        # Batch Buffer Config
        self.batch_buffer = {key: [] for key, _ in self.section_map.items()}
        self.batch_buffer_rebase_flags = {key: False for key, _ in self.section_map.items()}

        # Chunk Buffer Config
        self.chunk_buffer_num = 12
        self.chunk_buffer = {key: [] for key, _ in self.section_map.items()}

        # Debug
        # self.print_info()

    def print_info(self):
        logger.info("\n ===========================\n     Buffer Manager Info    \n ===========================")
        print("\n INPUT VALUES:\n")
        print("  Signal: ")
        print(f" --> Down-sampling Factor:              {self.N} ")
        print(f" --> Sampling Rate [Hz]:                {self.fs}")
        print(f" --> Sampling Time [s]:                 {self.dt}\n")
        print("  Section Map: ")
        print(f"  --> Number of Sections:               {self.section_number}")
        print(f"  --> Section ID's:                     {self.section_ids}")
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
        print(f"  --> Output Chunk Time [s]:            {self.output_chunk_time}")
        print(f"  --> Numb. of Batches in Buffer:       {self.buffer_batch_num}")
        print(f"  --> Numb. of Batches to Save per Sec: {self.num_batches_to_save}")
        print(f"  --> Train event index reference:      {self.train_event_index_ref}")
        print(f"  ----------------------------------------------------------------------------------------------------")

    def generate_train_capture(self, batch):
        processed_batch = TrainDetector(batch, **self.config).get_section_status()

        # Debugging
        # processed_batch_info = [{"section-id": ss.get("section-id"),
        #                          "batch-id": ss.get("batch-id"),
        #                          "status": ss.get("status")}
        #                         for ss in processed_batch]
        # logger.info(f"PROCESSED BATCH: {processed_batch_info}")

        for section_id in self.section_ids:
            # Get processed batch of a particular section
            processed_batch_section_id = \
                [section_batch for section_batch in processed_batch if section_batch['section-id'] == section_id][0]

            if len(self.batch_buffer[section_id]) < self.buffer_batch_num:
                # Fill Buffer if not rebased
                self.batch_buffer[section_id].append(processed_batch_section_id)

                # Debug
                logger.info(
                    f"BATCH BUFFER STATE  (FILLING)         :: section-id:"
                    f" {section_id}, buffer-length: {len(self.batch_buffer[section_id])}/{self.buffer_batch_num}")

            else:
                self.batch_buffer_rebase_flags[section_id] = True
                logger.info(f"REBASE FLAG TRUE ({section_id}):      :: {self.batch_buffer_rebase_flags}")

            if self.batch_buffer_rebase_flags[section_id]:
                for chunk in self.generate_chunks():
                    section_id = chunk['section-id']

                    # Debug
                    logger.info(f"BATCH BUFFER STATE: [REBASED]         :: section-id: {section_id}")

                    if not chunk['complete']:
                        self.chunk_buffer[section_id].append(chunk['train-data'])

                        # Debug
                        logger.info(f"CHUNK BUFFER STATE: [NOT COMPLETED]   :: section-id: {section_id}: "
                                    f"buffer-length: {len(self.chunk_buffer[section_id])}")

                    else:
                        # Debug
                        logger.info(f"CHUNK BUFFER STATE: [COMPLETED]       :: section-id: {section_id}: "
                                    f"buffer-length: {len(self.chunk_buffer[section_id])}")

                        if not self.chunk_buffer[section_id]:
                            yield chunk
                        else:
                            # Append chunk to section's chunk-buffer
                            self.chunk_buffer[section_id].append(chunk['train-data'])
                            section_train_data = self.concat_matrix_list(self.chunk_buffer[section_id])

                            # Debug
                            logger.info(f"CONCAT CHUNKS: section-id: {section_id}: "
                                        f"Capture-shape: {section_train_data.shape}")

                            # Delete chunk buffer of a section
                            self.chunk_buffer.update({section_id: []})

                            # Yield new concatenated chunk
                            yield {"section-id": section_id, "complete": True, "train-data": section_train_data}

                # Roll Buffer when rebased
                if self.batch_buffer[section_id]:
                    self.batch_buffer[section_id].pop(0)
                    self.batch_buffer[section_id].append(processed_batch_section_id)

                    # Debug
                    section_status = [batch['status'] for batch in self.batch_buffer[section_id]]
                    logger.info(f"BATCH BUFFER STATE  (ROLLING)         :: section-id: {section_id},"
                                f" section_status: {section_status}")

    def generate_chunks(self):
        for index, section_id in enumerate(self.section_ids):
            # Get a list of the train-event status batches stored in the buffer for a particular section
            section_status = [batch['status'] for batch in self.batch_buffer[section_id]]

            # Debug
            logger.info(f"BATCH BUFFER STATE  (CHUNK-GENERATOR) :: section-id: {section_id},"
                        f" section_status: {section_status}")

            if any(section_status) and self.batch_buffer_rebase_flags[section_id]:
                # Get the buffer index where the oldest train-event chunk is located
                train_event_min_index = min([s for s, r in enumerate(section_status) if r])
                if train_event_min_index == self.train_event_index_ref[index]:
                    # Select batches from buffer to generate a chunk
                    batch_data = [batch['batch-data'] for i, batch in enumerate(self.batch_buffer[section_id])
                                  if i >= (self.buffer_batch_num - self.num_batches_to_save[index])]

                    # Concat batch data to get a chunk
                    train_data = self.concat_matrix_list(batch_data)

                    # If there isn't train in the last batch mark chunk as complete
                    complete = not section_status[-1]

                    # Delete section-id buffer
                    self.batch_buffer.update({section_id: []})

                    # Update Rebased flag
                    self.batch_buffer_rebase_flags[section_id] = False
                    logger.info(
                        f"REBASE FLAG FALSE !! ({section_id}):  :: {self.batch_buffer_rebase_flags}")

                    # Debug
                    logger.info(
                        f"NEW CHUNK GENERATED                   :: section-id: {section_id}, complete: {complete},"
                        f" train_data (shape): {train_data.shape}")

                    yield {
                        "section-id": section_id,
                        "train-data": train_data,
                        "complete": complete
                    }

    @staticmethod
    def concat_matrix_list(matrix_list):
        new_matrix = np.ndarray((0, matrix_list[0].shape[1]))
        for matrix in matrix_list:
            new_matrix = np.concatenate([new_matrix, matrix])
        return new_matrix
