import os
import argparse
from dotenv import load_dotenv

from src.data_plotter import DataPlotter
from src.batch_data_generator import BatchDataGenerator
from src.buffer_manager import BufferManager
from src.buffer_manager_rt import BufferManagerRT
from src.json_file_manager_rt import JsonFileManagerRT
from src.config import get_config
from src.logger import load_logger

load_dotenv()
logger = load_logger(__name__)
config = get_config()

logger.info(f"ENVIRONMENT: {os.environ['ENVIRONMENT']}")

if not os.environ['ENVIRONMENT'] == 'dev':
    # ----- Production Path -----
    output_path = config['path']['output-prod']
    # ----------------------------
else:
    # ----- Development Path -----
    # TODO: Development environment
    #  data_path: "..data/{project_name}/{file_extension}"
    #  day_path: "..data/{project_name}/{file_extension}/{year}/{month}/{day}"
    data_path = config['path']['data-dev']
    output_path = config['path']['output-dev']
    # ----------------------------

# Set Argument Parser
parser = argparse.ArgumentParser(description="Tool to detect Trains in multiple sections and store the data.")
parser.add_argument(
    "-p", "--plot", action="store_true", help="Plot Detected Train's Waterfall", required=False
)
parser.add_argument(
    "-s", "--save", action="store_true", help="Save Detected Train's Waterfall (JSON by default)", required=False
)
parser.add_argument(
    "-b", "--binary", action="store_true",
    help="Put's binary flag to True, in order to save data as binary format (.bin)", required=False
)
parser.add_argument(
    "-f", "--files", type=int, help="Defines the number of files to be loaded"
)


# TODO: Development Environment
def main(args=None):
    args = parser.parse_args(args)

    if args.files:
        config['batch-data-generator']['max-files'] = args.files

    if args.binary:
        config['client']['save-binary'] = True

    buffer_manager_rt = BufferManagerRT(**config)

    for batch in BatchDataGenerator(data_path, **config):
        logger.info(f"batch.shape: {batch.shape}")
        logger.debug("BUFFER INFO :: ================================================================================")
        for chunk in buffer_manager_rt.generate_train_capture(batch):
            # Debug
            logger.info(
                f" --------> CHUNK GENERATED :: uuid: {chunk['uuid']} file-chunk: {chunk['file-chunk']}")

            # Save Chunk
            if args.save:
                JsonFileManagerRT(output_path, chunk, **config)

            # Plot data
            if args.plot:
                section_id = chunk['section-id']
                uuid = chunk['uuid']
                file_chunk = chunk['file-chunk']
                data_plotter = DataPlotter(chunk['train-data'], **config['plot-matrix'])
                data_plotter.set_title(f"New Train: section {section_id}. Chunk num: {file_chunk}.\nchunk-id: {uuid}")
                data_plotter.plot_matrix()

        logger.debug("===========================================================================================\n\n")


# TODO: Production Environment.
def get_buffer_manager():
    buffer_manager_rt = BufferManagerRT(**config)
    return buffer_manager_rt


def capture_train(batch, buffer_manager_rt, binary=True):
    if binary:
        config['client']['save-binary'] = True

    for chunk in buffer_manager_rt.generate_train_capture(batch):
        JsonFileManagerRT(output_path, chunk, **config)


if __name__ == "__main__":
    logger.info("Starting Railway Data Processing Tool...")
    main()
