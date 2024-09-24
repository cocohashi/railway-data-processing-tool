import os
from uuid import uuid4

import numpy as np
from dotenv import load_dotenv

from src.logger import load_logger
from src.train_detector import TrainDetector

load_dotenv()
logger = load_logger(__name__)


class BufferManagerRT:
    def __init__(self, **config):
        self.config = config

        # Signal Config
        self.N = config['signal']['N']
        self.fs = config['signal']['fs']  # Frequency [Hz]
        self.dt = self.N * (1 / self.fs)

        # Section Map Config
        self.section_map = config['section-map']
        self.section_ids = list(self.section_map.keys())

        # JSON File Manager Config
        self.max_file_size_mb = config["client"]["max-file-size-mb"]

        # Client's Side Buffer Manager Config
        self.start_margin_time = config['client']['start-margin-time']  # Time [s]
        self.end_margin_time = config['client']['end-margin-time']  # Time [s]

        # Params
        self.bytes_pixel_ratio = config['params']['bytes-pixel-ratio']
        self.batch_shape = config['params']['dev-batch-shape'] if os.environ['ENVIRONMENT'] == 'dev' \
            else config['params']['prod-batch-shape']

        # Batch Buffer Config
        self.batch_buffer = {key: [] for key, _ in self.section_map.items()}
        self.batch_buffer_rebase_flags = {key: False for key, _ in self.section_map.items()}
        self.batch_buffer_status_flags = {key: False for key, _ in self.section_map.items()}
        self.section_uuid_chunk = {key: None for key, _ in self.section_map.items()}
        self.section_file_chunk = {key: 0 for key, _ in self.section_map.items()}
        self.batch_buffer_sizes = {key: None for key, _ in self.section_map.items()}
        self.section_map_sizes = {key: (self.batch_shape[0], value[1] - value[0]) for key, value in
                                  self.section_map.items()}
        self.initial_timestamp = None

        self.buffer_sizes = self.get_buffer_sizes()
        self.to_active_state_index_ref = {key: int(self.start_margin_time / (self.batch_shape[0] * self.dt)) for key, _
                                          in self.section_map.items()}

        self.to_inactive_state_index_ref = {key: value - int(self.end_margin_time / (self.batch_shape[0] * self.dt)) for
                                            key, value in self.buffer_sizes.items()}

        self.debug_info()

    def debug_info(self):
        logger.debug(f"BUFFER MANAGER INFO ---------------------------------------------------------------------------")
        logger.debug(f"self.max_file_size_mb: {self.max_file_size_mb}")
        logger.debug(f"self.batch_shape: {self.batch_shape}")
        logger.debug(f"self.buffer_sizes: {self.buffer_sizes}")
        logger.debug(f"self.section_map_sizes: {self.section_map_sizes}")
        logger.debug(f"self.to_active_state_index_ref: {self.to_active_state_index_ref}")
        logger.debug(f"self.to_inactive_state_index_ref: {self.to_inactive_state_index_ref}")
        logger.debug("------------------------------------------------------------------------------------------------")

    @staticmethod
    def concat_matrix_list(matrix_list):
        new_matrix = np.ndarray((0, matrix_list[0].shape[1]))
        for matrix in matrix_list:
            new_matrix = np.concatenate([new_matrix, matrix])
        return new_matrix

    def get_buffer_sizes(self):
        batch_total_bytes = {key: self.bytes_pixel_ratio * value[0] * value[1] for key, value in
                             self.section_map_sizes.items()}

        return {key: int((self.max_file_size_mb * pow(2, 20)) / value) for key, value in
                batch_total_bytes.items()}

    def generate_train_capture(self, batch):
        train_detector = TrainDetector(batch, **self.config)
        processed_batch = train_detector.get_section_status()

        for section_id in self.section_ids:
            # Get processed batch of a particular section
            processed_batch_section_id = \
                [section_batch for section_batch in processed_batch if section_batch['section-id'] == section_id][0]

            if len(self.batch_buffer[section_id]) < self.buffer_sizes[section_id]:
                # Fill Buffer if not rebased
                self.batch_buffer[section_id].append(processed_batch_section_id)

                # Debug
                logger.debug(
                    f"BATCH BUFFER STATE  (FILLING)         :: section-id:"
                    f" {section_id}, buffer-length: {len(self.batch_buffer[section_id])}/{self.buffer_sizes[section_id]}")

            else:
                logger.debug(f"setting TRUE rebase flag, section: {section_id}")
                self.batch_buffer_rebase_flags[section_id] = True
                logger.debug(f"rebase-flags {section_id}: {self.batch_buffer_rebase_flags}")

            if self.batch_buffer_rebase_flags[section_id]:
                logger.debug(f"condition rebase-flags {section_id}: {self.batch_buffer_rebase_flags}")

                for chunk in self.generate_chunks(section_id):
                    yield chunk

                if self.batch_buffer[section_id]:  # Roll Buffer when rebased
                    self.batch_buffer[section_id].pop(0)
                    self.batch_buffer[section_id].append(processed_batch_section_id)

                    # Debug ---------------------------------------------------------------------------
                    # section_status = [batch['status'] for batch in self.batch_buffer[section_id]]
                    # logger.debug(f"BATCH BUFFER STATE  (ROLLING)         :: section-id: {section_id},"
                    #              f" section_status: {section_status}")
                    # ---------------------------------------------------------------------------------

    def generate_chunks(self, section_id):
        logger.debug(f"generating chunk in section {section_id} ...")
        # Get a list of the train-event status batches stored in the buffer for a particular section
        section_status = [batch['status'] for batch in self.batch_buffer[section_id]]

        # Debug
        logger.debug(f"BATCH BUFFER STATE  (CHUNK-GENERATOR) :: section-id: {section_id},"
                     f" section_status: {section_status}")

        if any(section_status):  # Not start any train capture if there isn't any train detected in the buffer

            # Get batch data
            batch_data = [batch['batch-data'] for batch in self.batch_buffer[section_id]]

            train_event_min_index = min([s for s, r in enumerate(section_status) if r])
            train_event_max_index = max([s for s, r in enumerate(section_status) if r])

            # If there isn't train in the last batch mark chunk as complete
            complete = not section_status[-1]

            if not self.batch_buffer_status_flags[section_id]:  # The section-id's train-capture is "INACTIVE"

                if train_event_min_index == self.to_active_state_index_ref[section_id]:
                    # Get initial timestamp
                    self.initial_timestamp = self.batch_buffer[section_id][0]['initial-timestamp']

                    # Concat batch data to get a chunk (only when yielded)
                    train_data = self.concat_matrix_list(batch_data)

                    if not complete:  # Mark status as ACTIVE
                        logger.debug(f"ACTIVATING capture in section {section_id}")
                        self.batch_buffer_status_flags[section_id] = True

                    # Emptying the buffer
                    self.batch_buffer.update({section_id: []})
                    self.batch_buffer_rebase_flags[section_id] = False

                    # Generate new section's chunk-uuid and restart file-chunk counter
                    self.section_uuid_chunk[section_id] = uuid4()
                    self.section_file_chunk[section_id] = 0

                    chunk = {
                        "section-id": section_id,
                        "uuid": self.section_uuid_chunk[section_id],
                        "file-chunk": self.section_file_chunk[section_id],
                        "initial-timestamp": self.initial_timestamp,
                        "complete": complete,
                        "train-data": train_data
                    }

                    # Debug ------------------------------------------------------------
                    logger.debug(
                        f"INITIAL (NEW) CHUNK GENERATED                   :: {chunk}")
                    # ------------------------------------------------------------------
                    logger.info(
                        f"batch data len: {len(batch_data)} - buffer-size: {self.buffer_sizes[section_id]}")

                    # if len(batch_data) == self.buffer_size:
                    yield chunk

            else:  # The section-id's train-capture is "ACTIVE"
                # If there isn't train in the last batch mark chunk as complete
                complete = not section_status[-1]

                # Concat batch data to get a chunk (only when yielded)
                train_data = self.concat_matrix_list(batch_data)

                if train_event_max_index <= self.to_inactive_state_index_ref[section_id]:
                    logger.debug(f"DE-ACTIVATING capture in section {section_id}")
                    self.batch_buffer_status_flags[section_id] = False

                # Emptying the buffer
                self.batch_buffer.update({section_id: []})
                self.batch_buffer_rebase_flags[section_id] = False

                # Update file-chunk counter
                self.section_file_chunk[section_id] += 1

                chunk = {
                    "section-id": section_id,
                    "uuid": self.section_uuid_chunk[section_id],
                    "file-chunk": self.section_file_chunk[section_id],
                    "initial-timestamp": self.initial_timestamp,
                    "complete": complete,
                    "train-data": train_data
                }

                # Debug ---------------------------------------------------
                logger.debug(
                    f"OTHER CHUNK GENERATED                   :: {chunk}")
                # ---------------------------------------------------------

                logger.info(f"batch data len: {len(batch_data)} - buffer-size: {self.buffer_sizes[section_id]}")
                # if len(batch_data) == self.buffer_size:
                yield chunk

        else:  # Make sure that buffer status flag is not active
            self.batch_buffer_status_flags[section_id] = False
