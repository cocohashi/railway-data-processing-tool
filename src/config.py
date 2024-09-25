# -----------------------------------------------------------------------------------------------------------------
# Confing Parameters
# -----------------------------------------------------------------------------------------------------------------

config = {

    # TODO: Client's Parameters
    # -------------------------------------------------------------------------------------------------------------
    # Section Map
    "section-map": {
        # "S01": (200, 300),
        "S02": (100, 300),
        "S03": (100, 150),
    },

    # Client
    "client": {
        "file-size-mb-list": [5, 5],
        "save-binary": True,
        "start-margin-time": 10,  # Time [s]
        "end-margin-time": 20,  # Time [s]
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
        "N": 5,  # int: Downsampling-Factor: Number of Samples to be downsampled
        "f_order": 4,  # int: The order of the Butterworth filter.
        "Wn": 0.8,  # int or list: Cutoff frequencies of Butterworth filter
        "btype": "hp",  # str: Butterworth filter type. {‘lowpass’, ‘highpass’, ‘bandpass’, ‘bandstop’}, optional
        "fs": 1000,  # int: The sampling frequency of the digital system in Hz.
    },

    # Train Detector
    "train-detector": {
        "spatial-window": 2,
        "detection-threshold": 3
    },

    # Buffer Manager
    "params": {
        "temporal-resolution": 5,  # Time [s]
        "spatial-resolution": 5,  # Space [m]
        "section-train-speed-mean": [144, 144, 144, 144],  # Speed [Km / h]
        "bytes-pixel-ratio": 1.9836151336393466,
        "dev-batch-shape": (1024, 2478),
        "prod-batch-shape": (4096, 5625),
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
