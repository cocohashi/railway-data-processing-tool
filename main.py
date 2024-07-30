import os
import logging

os.environ['ENVIRONMENT'] = "develop"  # 'develop' and 'production' environments only allowed

from src.data_loader import DataLoader

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


def main():
    sample = 0
    files = [filepath for filepath in os.listdir(data_path)]
    data_loader = DataLoader(fullpath=os.path.join(data_path, files[sample]))

    logger.info(f"data: {data_loader.data}")


if __name__ == "__main__":
    logger.info("Starting Railway Data Processing Tool...")
    main()
