# Railway Data Processing Tool

This projects aims to store the data captured by DAS equipment monitoring railway
infrastructures that follows some constraints, in order to prepare this data for future post-processing pipelines.

The processing of data made in this project, has as purpose to implement different methodologies of processing and storing
the data captured by the enterprise own sofware called 'Nervision'':

## Method 1

In this method the data storage will follow these convections:

1) Data will be stored in chunks of a custom file size for a given start and end railway sections. 

NOTE: The data chunks of each section has the same file-size, even if the spatial length of each section is different. 
      This feature forces to have different time lengths, that depends on each section spatial length and desired file 
      size.
2) Data is stored in a predefined JSON format.

## Getting started

### Python Installation (Windows)

1. Download [Windows installer (64-bit)](https://www.python.org/ftp/python/3.9.11/python-3.9.11-amd64.exe) python installer for Windows from [Official Python distribution website](https://www.python.org/downloads/windows/)
2. Follow installation instructions
3. Create new Virtual environment called `venv` inside project root path.

```shell
py -3.11 venv venv
```

## Format of the output Data

The data captured by the DAS, will be saved in a JSON format with the following schema: 

````json
{
  "info":
    {
      "sensor_name": "IPV_SENER",
      "inter_sensor_distance": 5.0,
      "sampling_rate": 1001.72,
      "spatial_resolution": 5.0,
      "spatial_samples": 527,
      "temporal_samples": 30002,
      "initial_timestamp": 1679392200.6447551,
      "zone_ID": 6,
      "event_type": "train",
      "event_location": 3124.6
    },
  "strain": "disJLrwqcq4rG1mngi8MsEQx"
}
````

The key ``info`` contains the metadata. 

The key ``strain`` contains the measurement made by DAS equipment. In order to save space, the data will be formatted to 
``base64`` string format.