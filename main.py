import os
import logging
from dotenv import load_dotenv

from src.data_plotter import DataPlotter
from src.batch_data_generator import BatchDataGenerator
from src.buffer_manager import BufferManager
from src.json_file_manager import JsonFileManager
from src.config import config

load_dotenv()

# -------------------------------------------------------------------------------------------------------------------
# Set Logger
# -------------------------------------------------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.propagate = False
handler = logging.StreamHandler() if os.environ['ENVIRONMENT'] == 'develop' else logging.FileHandler('main.log')
logger.setLevel(logging.DEBUG) if os.environ['LEVEL'] == 'debug' else logger.setLevel(logging.INFO)
formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)
# -----------------------------------------------------------------------------------------------------------------

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


def main():
    logger.debug(f"DEBUG test")
    logger.info(f"info test")
    file_id = 1
    buffer_manager = BufferManager(**config)
    for batch in BatchDataGenerator(data_path, **config):
        for chunk in buffer_manager.generate_train_capture(batch):
            # Debug
            logger.info(
                f" -------> CHUNK GENERATED {file_id}: section-id: {chunk['section-id']},"
                f" train-data (shape): {chunk['train-data'].shape}"
                f" initial-timestamp: {chunk.get('initial-timestamp')}")

            # Plot data
            # section_id = chunk['section-id']
            # data_plotter = DataPlotter(chunk['train-data'], **config['plot-matrix'])
            # data_plotter.set_title(f"New Train: section {section_id}")
            # data_plotter.plot_matrix()

            # Save Chunk
            JsonFileManager(output_path, chunk, file_id, **config)

            # Update file-id
            file_id += 1


if __name__ == "__main__":
    logger.info("Starting Railway Data Processing Tool...")
    main()
