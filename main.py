import os
import logging

os.environ['ENVIRONMENT'] = "develop"  # 'develop' and 'production' environments only allowed

from src.data_plotter import DataPlotter
from src.batch_data_generator import BatchDataGenerator
from src.buffer_manager import BufferManager

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

logger.info(os.environ['ENVIRONMENT'])

if not os.environ['ENVIRONMENT'] == 'develop':
    # ----- Production Path -----
    data_path = ""
    # ----------------------------
else:
    # ----- Development Path -----
    # TODO: Development environment
    #  data_path: "..data/{project_name}/{file_extension}"
    #  day_path: "..data/{project_name}/{file_extension}/{year}/{month}/{day}"
    data_path = "../data/ETS"
    # ----------------------------

# -----------------------------------------------------------------------------------------------------------------
# Confing Parameters
# -----------------------------------------------------------------------------------------------------------------

config = {

    # Signal Processor
    "signal": {
        "N": 5,  # int: Downsampling-Factor: Number of Samples to be downsampled
        "f_order": 4,  # int: The order of the Butterworth filter.
        "Wn": 0.8,  # int or list: Cutoff frequencies of Butterworth filter
        "btype": "hp",  # str: Butterworth filter type. {‘lowpass’, ‘highpass’, ‘bandpass’, ‘bandstop’}, optional
        "fs": 1000,  # int: The sampling frequency of the digital system in Hz.
    },

    # Data Plotting
    "plot-matrix": {
        "section": 0,
        "vmin": None,
        "vmax": None,
        "xlabel": "x-axis (samples)",
        "ylabel": "y-axis (samples)",
        "title": "",
        "cmap": "seismic",
        "figsize": None,
        "extent": None
    },

    # Section Map
    "section-map": {
        "S01": (95, 200),
        "S02": (201, 330),
        "S03": (331, 370),
        # "S04": (371, 635),
    },

    # Buffer Manager
    "buffer-manager": {
        "batch-time": 5,  # Time [s]
        "spatial-resolution": 5,  # Space [m]
        "section-train-speed-mean": [144, 144, 144, 144],  # Speed [Km / h]
        "start-margin-time": 10,  # Time [s]
        "end-margin-time": 20,  # Time [s]
    }
}


# -----------------------------------------------------------------------------------------------------------------


def main():
    buffer_manager = BufferManager(**config)
    for batch in BatchDataGenerator(data_path, **config):
        for chunk in buffer_manager.generate_train_capture(batch):
            section_id = chunk['section-id']
            train_data = chunk['train-data']

            # Debug
            logger.info(f" -------> CHUNK GENERATED: section-id: {section_id}, train-data (shape): {train_data.shape}")

            # Plot data
            data_plotter = DataPlotter(chunk['train-data'], **config['plot-matrix'])
            data_plotter.set_title(f"New Train: section {section_id}")
            data_plotter.plot_matrix()


if __name__ == "__main__":
    logger.info("Starting Railway Data Processing Tool...")
    main()
