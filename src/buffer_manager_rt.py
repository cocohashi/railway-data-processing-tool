import numpy as np
from dotenv import load_dotenv
from uuid import uuid4

from src.train_detector import TrainDetector
from src.logger import load_logger

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
        self.max_file_size_mb = config["json-file-manager"]["max-file-size-mb"]

        # Batch Manager Config
        self.batch_time = config['buffer-manager']['batch-time']  # Time [s]
        self.start_margin_time = config['buffer-manager']['start-margin-time']  # Time [s]
        self.end_margin_time = config['buffer-manager']['end-margin-time']  # Time [s]
        self.temporal_length_weight_ratio = 0.002906885053135184
        self.batch_buffer_temporal_length = self.max_file_size_mb * pow(2, 20) * self.temporal_length_weight_ratio

        # Batch Buffer Config
        self.batch_buffer = {key: [] for key, _ in self.section_map.items()}
        self.batch_buffer_rebase_flags = {key: False for key, _ in self.section_map.items()}
        self.batch_buffer_status_flags = {key: False for key, _ in self.section_map.items()}
        self.section_uuid_chunk = {key: None for key, _ in self.section_map.items()}
        self.section_file_chunk = {key: 0 for key, _ in self.section_map.items()}
        self.to_active_state_index_ref = None
        self.to_inactive_state_index_ref = None
        self.initial_timestamp = None
        self.buffer_size = None

    @staticmethod
    def concat_matrix_list(matrix_list):
        new_matrix = np.ndarray((0, matrix_list[0].shape[1]))
        for matrix in matrix_list:
            new_matrix = np.concatenate([new_matrix, matrix])
        return new_matrix

    def get_buffer_size(self, batch_temporal_length):
        return int(self.batch_buffer_temporal_length / batch_temporal_length)

    def generate_train_capture(self, batch):
        train_detector = TrainDetector(batch, **self.config)
        processed_batch = train_detector.get_section_status()

        temporal_length = train_detector.get_temporal_length()
        temporal_length_sec = temporal_length * self.dt

        self.buffer_size = self.get_buffer_size(temporal_length)
        self.to_active_state_index_ref = int(self.start_margin_time / temporal_length_sec)
        self.to_inactive_state_index_ref = self.buffer_size - int(self.end_margin_time / temporal_length_sec)

        # Debugging --------------------------------------------------
        # processed_batch_info = [{"section-id": ss.get("section-id"),
        #                          "batch-id": ss.get("batch-id"),
        #                          "status": ss.get("status")}
        #                         for ss in processed_batch]
        # logger.debug(f"PROCESSED BATCH: {processed_batch_info}")
        # logger.debug(f"BUFFER SIZE: {buffer_size}")
        # logger.debug(f"ACTIVE STATE INDEX REF: {self.to_active_state_index_ref}")
        # logger.debug(f"INACTIVE STATE INDEX REF: {self.to_inactive_state_index_ref}")
        # ------------------------------------------------------------

        for section_id in self.section_ids:
            # Get processed batch of a particular section
            processed_batch_section_id = \
                [section_batch for section_batch in processed_batch if section_batch['section-id'] == section_id][0]

            if len(self.batch_buffer[section_id]) < self.buffer_size:
                # Fill Buffer if not rebased
                self.batch_buffer[section_id].append(processed_batch_section_id)

                # Debug
                logger.debug(
                    f"BATCH BUFFER STATE  (FILLING)         :: section-id:"
                    f" {section_id}, buffer-length: {len(self.batch_buffer[section_id])}/{self.buffer_size}")

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

                if train_event_min_index == self.to_active_state_index_ref:
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
                        f"batch data len: {len(batch_data)} - buffer-size: {self.buffer_size}")

                    # if len(batch_data) == self.buffer_size:
                    yield chunk

            else:  # The section-id's train-capture is "ACTIVE"
                # If there isn't train in the last batch mark chunk as complete
                complete = not section_status[-1]

                # Concat batch data to get a chunk (only when yielded)
                train_data = self.concat_matrix_list(batch_data)

                if train_event_max_index <= self.to_inactive_state_index_ref:
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

                logger.info(f"batch data len: {len(batch_data)} - buffer-size: {self.buffer_size}")
                # if len(batch_data) == self.buffer_size:
                yield chunk

        else:  # Make sure that buffer status flag is not active
            self.batch_buffer_status_flags[section_id] = False
