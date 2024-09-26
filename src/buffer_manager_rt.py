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

        # Client's Side Buffer Manager Config
        self.start_margin_time = config['client']['start-margin-time']  # Time [s]
        self.end_margin_time = config['client']['end-margin-time']  # Time [s]
        self.total_time_max = config["client"]["total-time-max"]
        self.file_size_mb_list = config["client"]["file-size-mb-list"]  # List of each section's file-sizes [MB]
        self.file_size_mb_dict = self.get_file_size_mb_dict()

        # Params
        self.bytes_pixel_ratio = config['params']['bytes-pixel-ratio']
        self.batch_shape = config['params']['dev-batch-shape'] if os.environ['ENVIRONMENT'] == 'dev' \
            else config['params']['prod-batch-shape']
        self.buffer_size_lower_limit = config['params']['buffer-size-lower-limit']

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
        self.to_active_state_index_ref = {key: int(self.start_margin_time / (self.batch_shape[0] * self.dt) + 1) for
                                          key, _ in self.section_map.items()}

        self.to_inactive_state_index_ref = {key: value - int(self.end_margin_time / (self.batch_shape[0] * self.dt) + 1)
                                            for key, value in self.buffer_sizes.items()}

        self.max_margin_times = {key: self.batch_shape[0] * self.dt * (value - 1) for key, value in
                                 self.buffer_sizes.items()}
        self.file_size_limit = self.get_file_size_limit()

        # Validations
        self.validate_index_ref()
        self.validate_file_size_limit()
        self.validate_buffer_size()
        self.debug_info()

    @staticmethod
    def concat_matrix_list(matrix_list):
        new_matrix = np.ndarray((0, matrix_list[0].shape[1]))
        for matrix in matrix_list:
            new_matrix = np.concatenate([new_matrix, matrix])
        return new_matrix

    def debug_info(self):
        logger.debug(f"BUFFER MANAGER INFO ---------------------------------------------------------------------------")
        logger.debug(f"self.file_size_mb_list: {self.file_size_mb_list}")
        logger.debug(f"self.batch_shape: {self.batch_shape}")
        logger.debug(f"self.buffer_sizes: {self.buffer_sizes}")
        logger.debug(f"self.section_map_sizes: {self.section_map_sizes}")
        logger.debug(f"self.to_active_state_index_ref: {self.to_active_state_index_ref}")
        logger.debug(f"self.to_inactive_state_index_ref: {self.to_inactive_state_index_ref}")
        logger.debug(f"self.max_margin_times: {self.max_margin_times} seconds")
        logger.debug(
            f"MAX FILE SIZE: {self.file_size_limit} MBytes to wait {round(self.total_time_max, 3)} seconds in"
            f" each capture.")
        logger.debug("------------------------------------------------------------------------------------------------")

    # Getters
    def get_file_size_mb_dict(self):
        res = {}
        for i, key in enumerate(self.section_ids):
            if len(self.section_ids) != len(self.file_size_mb_list):
                raise ValueError(
                    f"Defined sections_ids ({self.section_ids}) and maximum file's sizes {self.file_size_mb_list}"
                    f" do not match. Please add/reduce more sections or file-size values."
                )
            else:
                res.update({key: self.file_size_mb_list[i]})
        return res

    def get_buffer_sizes(self, m_byte=True):
        batch_total_bytes = {key: self.bytes_pixel_ratio * value[0] * value[1] for key, value in
                             self.section_map_sizes.items()}

        r = pow(2, 20) if m_byte else 1
        return {key: int((self.file_size_mb_dict[key] * r) / value) for key, value in
                batch_total_bytes.items()}

    def get_file_size_limit(self, m_byte=True):
        r = pow(2, 20) if m_byte else 1
        return (self.total_time_max * self.bytes_pixel_ratio * self.batch_shape[0]) / (self.dt * r)

    #  Validations
    def validate_index_ref(self):
        for section_id, value in self.buffer_sizes.items():
            section_to_active_state_index_ref = self.to_active_state_index_ref[section_id]
            section_to_inactive_state_index_ref = self.to_inactive_state_index_ref[section_id]
            if (section_to_active_state_index_ref + 1) > value or section_to_inactive_state_index_ref < 1:
                raise ValueError(
                    f"In section {section_id}, any 'margin-time' cannot be higher than "
                    f"'{self.max_margin_times[section_id]}'. "
                    f"INCREASE 'file-size' or REDUCE the section's 'selected-area' to increase "
                    f"'margin-time' limit for this section.")

    def validate_file_size_limit(self):
        if len([*filter(lambda x: x >= self.file_size_limit, self.file_size_mb_list)]) > 0:
            raise ValueError(f"Any file-size value given '{self.file_size_mb_list}' "
                             f"should not be higher than {round(self.file_size_limit, 3)} MByte")

    def validate_buffer_size(self):
        for section_id, value in self.buffer_sizes.items():
            if value < self.buffer_size_lower_limit:
                raise ValueError(f"Buffer-size in section {section_id} is {value}."
                                 f"INCREASE 'file-size' or REDUCE the section 'selected-area' to increase buffer's "
                                 f"size value for this section.")

    # Train Capture Generation
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
                    f"BATCH BUFFER STATE  (FILLING)         :: section-id:  {section_id}, "
                    f"buffer-length: {len(self.batch_buffer[section_id])}/{self.buffer_sizes[section_id]}")

            else:
                self.batch_buffer_rebase_flags[section_id] = True

            if self.batch_buffer_rebase_flags[section_id]:

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
                    logger.debug(
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
