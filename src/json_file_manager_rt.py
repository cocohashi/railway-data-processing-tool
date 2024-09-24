import os
import json
import base64
import struct
import asyncio
import traceback
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

from src.schema import json_schema
from src.logger import load_logger

load_dotenv()
logger = load_logger(__name__)


class JsonFileManagerRT:
    def __init__(self, output_path: str, chunk: dict, **config):
        # Paths
        self.output_path = output_path
        self.json_fullpath = None
        self.binary_fullpath = None
        self.output_day_path = None
        self.filename = None

        # Chunk
        self.section_id = chunk["section-id"]
        self.uuid = chunk["uuid"]
        self.initial_timestamp = chunk["initial-timestamp"]
        self.file_chunk = chunk["file-chunk"]
        self.train_data = chunk["train-data"]
        self.temporal_samples = self.train_data.shape[0]
        self.spatial_samples = self.train_data.shape[1]

        # Config
        self.config = config
        self.spatial_resolution = config["params"]["spatial-resolution"]
        self.max_file_size_mb = config["client"]["max-file-size-mb"]
        self.save_binary = config["client"]["save-binary"]
        self.fs = config["signal"]["fs"]

        # Signal
        self.dt = 1 / self.fs

        # JSON schema
        self.json_schema = json_schema

        # Run File Handler
        if not os.environ['ENVIRONMENT'] == 'dev':
            # TODO: Production Environment (Python 3.6)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.file_handler())
        else:
            # TODO: Development Environment (Python > 3.6)
            asyncio.run(self.file_handler())

    # SERIALIZE JSON
    async def serialize(self):
        with open(self.json_fullpath, "w", encoding="utf-8") as file:
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
                "uuid": str(self.uuid),
                "spatial_resolution": self.spatial_resolution,
                "temporal_samples": self.temporal_samples,
                "spatial_samples": self.spatial_samples,
                "initial_timestamp": self.initial_timestamp,
                "zone_ID": self.section_id,
                "file_chunk": self.file_chunk
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
            f"{initial_datetime.hour:02d}_{initial_datetime.minute:02d}_{initial_datetime.second:02d}_{self.section_id}"
            f"_part_{self.file_chunk:02d}")

        logger.info(f"Saving data as filename: {filename}")
        self.json_fullpath = os.path.join(self.output_day_path, f"{filename}.json")
        self.binary_fullpath = os.path.join(self.output_day_path, f"{filename}.bin")

    async def file_handler(self):
        try:
            # Update JSON
            await self.update_json_schema()

            # Convert data to base64
            train_data_base64 = await self.matrix_to_base64_string(self.train_data)

            # Make output dirs and get full paths
            self.make_output_dirs()
            self.get_fullpath()

            # Save JSON schema
            if self.save_binary:
                logger.debug(f"Saving binary (.bin) file {self.filename} in path '{self.binary_fullpath}'")
                await self.serialize_bytes(self.train_data)
            else:
                logger.debug(f"Saving JSON (.json) file {self.filename} in path '{self.json_fullpath}'")
                self.json_schema.update({"strain": train_data_base64})
                await self.serialize()

            return True

        except Exception as e:
            logger.error(f"SERIALIZATION ERROR: {e}")
            print(traceback.format_exc())
            return False
