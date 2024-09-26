# -----------------------------------------------------------------------------------------------------------------
# Confing Parameters
# -----------------------------------------------------------------------------------------------------------------

config = {

    # TODO: Client's Parameters
    # -------------------------------------------------------------------------------------------------------------
    # Section Map
    "section-map": {
        "S01": (0, 110),
        "S02": (100, 200),
        "S03": (200, 300),
    },

    # Client
    "client": {
        "file-size-mb-list": [2, 2, 2],
        "save-binary": True,
        "start-margin-time": 0,  # Time [s]
        "end-margin-time": 0,  # Time [s]
        "total-time-max": 60  # Time [s]
    },

    # TODO: Application's Parameters
    # -------------------------------------------------------------------------------------------------------------

    # Paths
    "path": {
        "data-dev": "../data/ETS",  # For debugging purposes
        "output-dev": "./test/output",
        "output-prod": "../output"
    },

    # Signal Processor
    "signal": {
        "N": 1,  # int: Downsampling-Factor: Number of Samples to be downsampled
        "f_order": 4,  # int: The order of the Butterworth filter.
        "Wn": 0.8,  # int or list: Cutoff frequencies of Butterworth filter
        "btype": "hp",  # str: Butterworth filter type. {‘lowpass’, ‘highpass’, ‘bandpass’, ‘bandstop’}, optional
        "fs": 1000,  # int: The sampling frequency of the digital system in Hz.
    },

    # Train Detector
    "train-detector": {
        "spatial-window": 2,  # Number of adjacent samples to be considered as valid (mode 0)
        "validity-percentage": 0.05,  # Percentage of valid samples, expressed in decimal (from 0 to 1) (mode 1)
        "detection-threshold": 2,  # RMS Threshold value which marks a samples as valid (mode 0 or 1)
    },

    # Params
    "params": {
        "temporal-resolution": 5,  # Time [s]
        "spatial-resolution": 5,  # Space [m]
        "section-train-speed-mean": [144, 144, 144, 144],  # Speed [Km / h]
        "bytes-pixel-ratio": 1.9836151336393466,
        "dev-batch-shape": (1024, 2478),
        "prod-batch-shape": (4096, 5625),
        "section-limit": 10,  # Maximum number of sections
        "section-index-limit": 1000,  # Maximum upper index limit
        "total-time-max-limit": 300,  # Maximum time of the Maximum time established by the client [s]
        "buffer-size-lower-limit": 4
    },

    # TODO: Debugging Purpose Parameters
    # -------------------------------------------------------------------------------------------------------------

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

    # Batch Data Generator
    "batch-data-generator": {
        "max-files": 3,
        "waiting-time": 0.05
    }
}


# -----------------------------------------------------------------------------------------------------------------

def validate_section_limit():
    section_ids = list(config['section-map'].keys())
    section_limit = config['params']['section-limit']
    if len(section_ids) > section_limit:
        raise ValueError(f"The number of sections defined should not be higher than {section_limit}")


def validate_section_index_limit():
    section_index_limit = config['params']['section-index-limit']
    section_upper_limits = [value[1] for key, value in config['section-map'].items()]
    if len(list(filter(lambda x: x >= section_index_limit, section_upper_limits))) > 0:
        raise ValueError(f"The upper limit of any section index, should not be higher than {section_index_limit}")


def validate_total_time_max():
    total_time_max = config['client']['total-time-max']
    total_time_max_limit = config['params']['total-time-max-limit']
    if total_time_max > total_time_max_limit:
        raise ValueError(f"Total time max should not be higher than {total_time_max_limit}")


def get_config():
    validate_section_limit()
    validate_section_index_limit()
    validate_total_time_max()
    return config
