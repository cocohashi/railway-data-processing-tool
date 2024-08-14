# JSON schema of DAS data for Railway applications

```JSON
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
```

## Properties Info

#### `sensor_name`

The name of the DAS equipment used for measurements

#### `uuid`

A unique identifier that identifies the full waterfall view (capture).

This waterfall will be composed concatenating temporally each chunk with the same uuid.

#### `sampling_rate`

The acquisition frequency.

Magnitude: Frequency [Hz]

#### `spatial_resolution`

Magnitude: Distance [m]

#### `sampling_interval`

The distance between "virtual" array sensors.

Magnitude: Distance [m]

#### `temporal_samples`

The number of temporal samples of the actual file (chunk).

It corresponds to the number of rows of the chunk-matrix.

#### `spatial_samples`

The number of spatial samples of the actual file (chunk).

It corresponds to the number of columns of the chunk-matrix.

#### `initial_timestamp`

#### `zone_ID`

It identifies a spatial section of the deployed optic-fiber.

#### `file_chunk`

The actual position of the chunk.

#### `total_chunks`

The total number of chunks that composes the waterfall.

#### `strain`

Formatted chunk's strain data.
