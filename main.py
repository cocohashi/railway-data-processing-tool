import os
import argparse
from dotenv import load_dotenv

from src.data_plotter import DataPlotter
from src.batch_data_generator import BatchDataGenerator
from src.buffer_manager import BufferManager
from src.json_file_manager import JsonFileManager
from src.config import config
from src.logger import load_logger

load_dotenv()
logger = load_logger(__name__)

logger.info(f"ENVIRONMENT: {os.environ['ENVIRONMENT']}")

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
    output_path = "./test/output"
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


def main(args=None):
    args = parser.parse_args(args)
    file_id = 1

    if args.files:
        config['batch-data-generator']['max-files'] = args.files

    if args.binary:
        config['json-file-manager']['save-binary'] = True

    buffer_manager = BufferManager(**config)
    for batch in BatchDataGenerator(data_path, **config):
        for chunk in buffer_manager.generate_train_capture(batch):
            # Debug
            logger.info(
                f" --------> CHUNK GENERATED {file_id}: section-id: {chunk['section-id']},"
                f" train-data (shape): {chunk['train-data'].shape}"
                f" initial-timestamp: {chunk.get('initial-timestamp')}")

            # Plot data
            if args.plot:
                section_id = chunk['section-id']
                data_plotter = DataPlotter(chunk['train-data'], **config['plot-matrix'])
                data_plotter.set_title(f"New Train: section {section_id}")
                data_plotter.plot_matrix()

            # Save Chunk
            if args.save:
                JsonFileManager(output_path, chunk, file_id, **config)

            # Update file-id
            file_id += 1


if __name__ == "__main__":
    logger.info("Starting Railway Data Processing Tool...")
    main()
