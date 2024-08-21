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
    },

    # Train Detector
    "train-detector": {
        "spatial-window": 2,
        "detection-threshold": 3
    },

    # Batch Data Generator
    "batch-data-generator": {
        "max-files": 3,
        "waiting-time": 0.05
    },

    # Buffer Manager
    "buffer-manager": {
        "batch-time": 5,  # Time [s]
        "spatial-resolution": 5,  # Space [m]
        "section-train-speed-mean": [144, 144, 144, 144],  # Speed [Km / h]
        "start-margin-time": 10,  # Time [s]
        "end-margin-time": 20,  # Time [s]
    },

    # JSON File Manager
    "json-file-manager": {
        "max-file-size-mb": 3,
        "save-binary": False
    }
}

# -----------------------------------------------------------------------------------------------------------------
