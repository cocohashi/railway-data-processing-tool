import os
import json
import base64
import struct
import asyncio
import traceback
import numpy as np
from datetime import datetime

from uuid import uuid4
from dotenv import load_dotenv

from src.schema import json_schema
from src.logger import load_logger

load_dotenv()
logger = load_logger(__name__)


class JsonFileManager:
    def __init__(self, output_path: str, chunk: dict, file_id=0, **config):
        # Paths
        self.output_path = output_path
        self.fullpath = None
        self.binary_fullpath = None
        self.output_day_path = None

        # Chunk
        self.chunk = chunk
        self.train_data = chunk["train-data"]
        self.section_id = chunk["section-id"]
        self.initial_timestamp = chunk["initial-timestamp"]

        # File
        self.file_id = file_id
        self.file = None

        # Config
        self.config = config
        self.spatial_resolution = config["buffer-manager"]["spatial-resolution"]
        self.max_file_size_mb = config["json-file-manager"]["max-file-size-mb"]
        self.save_binary = config["json-file-manager"]["save-binary"]
        self.fs = config["signal"]["fs"]

        # Signal
        self.dt = 1 / self.fs

        # JSON schema
        self.json_schema = json_schema
        self.uuid = str(uuid4())
        self.temporal_samples = self.train_data.shape[0]
        self.spatial_samples = self.train_data.shape[1]
        self.max_file_size_b = self.max_file_size_mb * pow(2, 20)
        self.temporal_length_weight_ratio = 0.002906885053135184
        self.file_batch_size = self.max_file_size_b * self.temporal_length_weight_ratio
        self.total_file_chunks = round(self.temporal_samples / self.file_batch_size)
        self.file_batch_temporal_length = round(self.total_file_chunks * self.file_batch_size)
        self.file_chunk_num = 0

        # Run File Handler
        if not os.environ['ENVIRONMENT'] == 'dev':
            # TODO: Production Environment (Python 3.6)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.file_handler())
        else:
            # TODO: Development Environment (Python > 3.6)
            asyncio.run(self.file_handler())

    async def __aenter__(self):
        await self.serialize()
        return self.file

    async def __aexit__(self, exc_type, exc, tb):
        self.file.close()

    # SERIALIZE JSON
    async def serialize(self):
        with open(self.fullpath, "w", encoding="utf-8") as file:
            json.dump(self.json_schema, file, indent=4)

    async def serialize_bytes(self, matrix):
        with open(self.binary_fullpath, "wb") as file:
            json_bytearray = json.dumps(self.json_schema).encode('ascii')
            file.write(struct.pack('<H', len(json_bytearray)))
            file.write(json_bytearray)
            np.save(file, matrix.astype(np.float16))

    async def update_json_schema(self):
        """
        Updates JSON schema.
        Properties:
            "info": {
                "sensor_name",
                "uuid",
                "sampling_rate",
                "spatial_resolution",
                "temporal_samples",
                "spatial_samples",
                "initial_timestamp",
                "zone_ID",
                "file_chunk",
                "total_chunks"
            }
            "strain": ""

        :return: json_schema (dict)
        """

        self.json_schema['info'].update(
            {
                "uuid": self.uuid,
                "spatial_resolution": self.spatial_resolution,
                "temporal_samples": self.temporal_samples,
                "spatial_samples": self.spatial_samples,
                "initial_timestamp": self.initial_timestamp,
                "zone_ID": self.section_id,
                "total_chunks": self.total_file_chunks + 1
            }
        )

    # STRING DATA CONVERSION
    @staticmethod
    async def matrix_to_base64_string(my_matrix):

        float_encoding = 'e'
        my_bytearray = bytearray()

        for i_row in range(my_matrix.shape[0]):
            for i_col in range(my_matrix.shape[1]):
                my_bytearray += bytearray(struct.pack("<%s" % float_encoding, my_matrix[i_row, i_col]))
        my_bytearray_base64_encoded = base64.b64encode(my_bytearray)

        return my_bytearray_base64_encoded.decode('ascii')

    def make_output_dirs(self):
        # Exterior Data Path
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)

        # Get actual year, month and day
        initial_datetime = datetime.fromtimestamp(self.initial_timestamp)

        self.output_day_path = os.path.join(self.output_path, str(initial_datetime.year),
                                            f"{initial_datetime.month:02d}",
                                            f"{initial_datetime.day:02d}")

        logger.debug(f"Saving data in path: {self.output_day_path}")

        if not os.path.isdir(self.output_day_path):
            os.makedirs(self.output_day_path)

    def get_fullpath(self):
        initial_datetime = datetime.fromtimestamp(self.initial_timestamp)

        filename = (
            f"{self.section_id}_{initial_datetime.hour:02d}_{initial_datetime.minute:02d}_{initial_datetime.second:02d}"
            f"_part_{self.file_chunk_num:02d}")

        logger.info(f"Saving data as filename: {filename}")
        self.fullpath = os.path.join(self.output_day_path, f"{filename}.json")
        self.binary_fullpath = os.path.join(self.output_day_path, f"{filename}.bin")

    async def file_handler(self):
        await self.update_json_schema()

        for i, index in enumerate(range(0, self.file_batch_temporal_length, round(self.file_batch_size))):
            try:
                # Get file-chunk indexes
                file_chunk_indexes = (index, index + round(self.file_batch_size))
                train_data_chunk = self.train_data[file_chunk_indexes[0]: file_chunk_indexes[1], :]

                # Compute file-chunk's initial-timestamp
                chunk_initial_timestamp = self.initial_timestamp + index * self.dt

                # Convert data to base64
                train_data_base64 = await self.matrix_to_base64_string(train_data_chunk)

                # Update JSON schema
                self.file_chunk_num = i + 1
                self.json_schema["info"].update({"temporal_samples": train_data_chunk.shape[0]})
                self.json_schema["info"].update({"initial_timestamp": chunk_initial_timestamp})
                self.json_schema["info"].update({"file_chunk": self.file_chunk_num})

                # Make output dirs and get full paths
                self.make_output_dirs()
                self.get_fullpath()

                # Get fullpath (for debugging purposes) -------------------------------------
                # filename = f"test_{self.file_id:02d}_part_{file_chunk_num:02d}"
                # self.fullpath = os.path.join(self.output_path, f"{filename}.json")
                # self.binary_fullpath = os.path.join(self.output_path, f"{filename}.bin")
                # ---------------------------------------------------------------------------

                # Save JSON schema
                if self.save_binary:
                    logger.debug(f"Saving JSON (.json) file-chunks... Size: {file_chunk_indexes}")
                    await self.serialize_bytes(train_data_chunk)
                else:
                    logger.debug(f"Saving binary (.bin) file-chunks... Size: {file_chunk_indexes}")
                    self.json_schema.update({"strain": train_data_base64})
                    await self.serialize()

            except Exception as e:
                logger.error(f"JSON SERIALIZATION ERROR: {e}")
                print(traceback.format_exc())
