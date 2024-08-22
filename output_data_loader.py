import os
import json
import base64
import numpy as np
import struct

from dotenv import load_dotenv
from datetime import datetime

from src.logger import load_logger
from src.config import config
from src.data_plotter import DataPlotter

load_dotenv()
logger = load_logger(__name__)


class OutputDataLoader:
    def __init__(self, **kwargs):
        self.output_path = kwargs['output_path']
        self.datetime_obj = kwargs['datetime_obj']
        self.section_id = kwargs['section_id']
        self.extension = kwargs['extension']
        self.config = config

        self.datetime_str = datetime.strftime(self.datetime_obj, "%Y/%m/%d %H:%M:%S")
        self.items = {}
        self.output_day_path = None
        self.filenames = []
        self.npy_data_list = []
        self.full_matrix = None

        self.load_data()
        self.get_full_matrix()
        self.plot_matrix()

    def get_output_day_path(self):
        output_day_path = os.path.join(self.output_path, str(self.datetime_obj.year),
                                       f"{self.datetime_obj.month:02d}",
                                       f"{self.datetime_obj.day:02d}")
        if not os.path.exists(output_day_path):
            raise ValueError(f'Path "{output_day_path}" does not exist. Exiting...')

        return output_day_path

    def get_filenames(self):
        filenames = [filename for filename in os.listdir(self.output_day_path)
                     if self.section_id in filename
                     and f"{self.datetime_obj.hour:02d}" in filename
                     and f"{self.datetime_obj.minute:02d}" in filename
                     and f"{self.datetime_obj.second:02d}" in filename
                     and self.extension in filename]
        logger.info(f"filenames: {filenames}")
        return filenames

    # DATA LOADERS
    @staticmethod
    def deserialize_json(fullpath):
        # READ JSON FILE
        with open(fullpath, "r", encoding="utf-8") as reader:
            json_data = json.loads(reader.read())
            return json_data

    @staticmethod
    def base64_string_to_matrix(my_bytearray_base64_encoded_string, num_rows, num_cols):

        float_encoding = 'e'
        my_bytearray_reconstructed = base64.b64decode(my_bytearray_base64_encoded_string.encode('ascii'))

        my_value_reconstructed = struct.unpack("<%d%s" % (num_rows * num_cols, float_encoding),
                                               my_bytearray_reconstructed)

        my_array = np.array(my_value_reconstructed, dtype=float)
        my_matrix = my_array.reshape((num_rows, num_cols))

        return my_matrix

    @staticmethod
    def deserialize_binary(fullpath):
        with open(fullpath, 'rb') as f:
            header_len = struct.unpack('<H', f.read(2))[0]
            json_dict = json.loads(f.read(header_len).decode('ascii'))
            npy_data = np.load(f)
            return json_dict, npy_data

    def load_data(self):
        self.output_day_path = self.get_output_day_path()
        self.filenames = self.get_filenames()

        assert not len(self.filenames) == 0, \
            f"Files not found in section {self.section_id} for the given date {self.datetime_str}"

        for filename in self.filenames:
            fullpath = os.path.join(self.output_day_path, filename)
            if self.extension == '.bin':
                # do something
                logger.info(f"deserializing binary data...")
                self.items, npy_data = self.deserialize_binary(fullpath)
                self.npy_data_list.append(npy_data)
                logger.info(f"File {filename} 'info': {self.items['info']}")

            elif self.extension == '.json':
                # do something
                logger.info(f"deserializing JSON data...")
                self.items = self.deserialize_json(fullpath)
                num_rows = self.items['info'].get('temporal_samples')
                num_cols = self.items['info'].get('spatial_samples')
                strain_data = self.items.get('strain')
                npy_data = self.base64_string_to_matrix(strain_data, num_rows, num_cols)
                self.npy_data_list.append(npy_data)
                logger.info(f"File {filename} 'info': {self.items['info']}")

            else:
                logger.warning(
                    f"file extension '{self.extension}' is not implemented. It should have '.' at the beginning.")

    def get_full_matrix(self):

        total_number_rows = 0
        for i, element in enumerate(self.npy_data_list[:-1]):
            total_number_rows += element.shape[0]

        self.full_matrix = np.reshape(self.npy_data_list[:-1], (
            total_number_rows, self.npy_data_list[0].shape[1]))

        self.full_matrix = np.concatenate((self.full_matrix, self.npy_data_list[-1:][0]), axis=0)

    def plot_matrix(self):
        data_plotter = DataPlotter(self.full_matrix, **self.config['plot-matrix'])
        data_plotter.set_title(f"Loaded files: {self.filenames}")
        data_plotter.plot_matrix()


if __name__ == "__main__":
    kwargs = dict(
        output_path="./test/output",
        # datetime_obj=datetime(2024, 8, 22, 9, 32, 54),  # .bin
        datetime_obj=datetime(2024, 8, 22, 12, 35, 39),  # .json
        section_id="S02",
        extension=".json"
    )

    OutputDataLoader(**kwargs)
