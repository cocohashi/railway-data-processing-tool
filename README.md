# Railway Data Processing Tool

This projects aims to store the data captured by DAS equipment monitoring railway
infrastructures that follows some constraints, in order to prepare this data for future post-processing pipelines.

The processing of data made in this project, has as purpose to implement different methodologies of processing and storing
the data captured by the enterprise own sofware called 'Nervision'':

## Method 1

This method detects trains in real-time, in defined N sections of the monitored fiber-optic and stores the output 
matrixes in a single or multiple file-chunks in JSON or binary formats.

In this method the data storage will follow these conventions:

1) Data will be stored in file-chunks of a custom file size for a given start and end railway sections. 

2) Data is stored in a predefined JSON format (.json) or binary format (.bin).

3) The data will be saved in the path: `/{proyect_root_path}/output/{year}/{month}/{day}`

4) Stored filenames will be named with the convention; ``{section-id}_{hour}_{minute}_{second}_part_{XX}``

> NOTE: 
> 
> Available output extensions includes `.json` and `.bin`

## Getting started

### Python Installation (Windows)

1. Download [Windows installer (64-bit)](https://www.python.org/ftp/python/3.9.11/python-3.9.11-amd64.exe) python installer for Windows from [Official Python distribution website](https://www.python.org/downloads/windows/)
2. Follow installation instructions
3. Create new Virtual environment called `venv` inside project root path.

```shell
py -3.11 venv venv
```

4. Activate environment:

On Windows:
```shell
venv\Scripts\activate
```
On Linux:
```shell
source venv/bin/activate
```

5. Install `requirements.txt` file

```shell
pip install -r requirements.txt 
```

## Format of the output Data

The data captured by the DAS, will be saved in a JSON format with the following schema: 

````JSON
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "info": {
      "type": "object",
      "properties": {
        "sensor_name": {
          "type": "string"
        },
        "uuid": {
          "type": "string"
        },
        "sampling_rate": {
          "type": "integer"
        },
        "spatial_resolution": {
          "type": "number"
        },
          "sampling_interval": {
          "type": "number"
        },
        "temporal_samples": {
          "type": "integer"
        },
        "spatial_samples": {
          "type": "integer"
        },
        "initial_timestamp": {
          "type": "number"
        },
        "zone_ID": {
          "type": "string"
        },
        "file_chunk": {
          "type": "integer"
        },
        "total_chunks": {
          "type": "integer"
        }
      },
      "required": [
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
      ]
    },
    "strain": {
      "type": "string"
    }
  },
  "required": [
    "info",
    "strain"
  ]
}
````

The key ``info`` contains the metadata. 

The key ``strain`` contains the measurement made by DAS equipment. In order to save space, the data will be formatted to 
``base64`` string format.

You can find more information in [JSON_schema.md](JSON_schema.md)

## Usage

Run `main.py` with `-h` option to show 'help' dialog.

```shell
python .\main.py -h
```

```shell
usage: main.py [-h] [-p] [-s] [-b] [-f FILES]

Tool to detect Trains in multiple sections and store the data.

options:
  -h, --help            show this help message and exit
  -p, --plot            Plot Detected Train's Waterfall
  -s, --save            Save Detected Train's Waterfall (JSON by default)
  -b, --binary          Put's binary flag to True, in order to save data as binary format (.bin)
  -f FILES, --files FILES
                        Defines the number of files to be loaded
```

Usage examples:

To save detected trains in `.json` format extension, run:

```shell
python .\main.py -s
```

To save detected trains in `.bin` format extension by loading 5 files, run:

```shell
python .\main.py -sb -f 5
```

> NOTE:
> 
> The `files` input argument it is used for simulating a real-time scenario by loading N
> waterfall files. 
> For the development of this project, the data obtained in the project made for 'Euskal Trenbide Sarea' (ETS) has been 
> used.


