import os
import os.path as osp
import sys
import logging
from datetime import datetime
from transformers import HfArgumentParser
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path

from seqlbtoolkit.io import set_logging, logging_args, progress_bar

from chempp import parse_html, parse_xml
from chempp.utils import get_file_paths, map_doi_to_filename

logger = logging.getLogger(__name__)


@dataclass
class ArticleProcessingArgs:
    input_dir: str = field(metadata={"help": "The path or dir to the HTML/XML article file."})
    output_dir: Optional[str] = field(
        default="./output",
        metadata={"help": "The output directory where the validation results and relevant information is saved."},
    )
    output_type: Optional[str] = field(
        default="pt", metadata={"choices": ["pt", "html", "jsonl"], "help": "output type"}
    )
    log_path: Optional[str] = field(
        default=None, metadata={"help": "the directory of the log file. Set to 'none' to disable logging"}
    )
    keep_input_file_name: Optional[bool] = field(
        default=False, metadata={"help": "Keep the original file name when saving the output file."}
    )


def process_articles(args: ArticleProcessingArgs):

    if osp.isfile(args.input_dir):
        file_list = [args.input_dir]
    else:
        logger.info("Getting article paths")
        file_list = get_file_paths(args.input_dir)
        logger.info(f"{len(file_list)} articles to be processed")

    logger.info("Processing articles")

    with progress_bar as pbar:
        for file_path in pbar.track(file_list):

            file_path = osp.normpath(file_path)
            logger.info(f"Processing {file_path}")

            try:
                if file_path.lower().endswith("html"):
                    article, component_check = parse_html(file_path)
                elif file_path.lower().endswith("xml"):
                    article, component_check = parse_xml(file_path)
                else:
                    logger.error(f"Unsupported file type!")
                    continue
            except Exception as e:
                logger.error(f"Failed to parse file. Error: {e}")
                continue

            try:
                # save article to disk with specified file type
                out_name = Path(file_path).stem if args.keep_input_file_name else map_doi_to_filename(article.doi)
                save_path = osp.join(args.output_dir, f"{out_name}.{args.output_type}")

                os.makedirs(osp.split(save_path)[0], exist_ok=True)

                getattr(article, f"save_{args.output_type}")(save_path)

            except Exception as e:
                logger.exception(f"Failed to save the parsed file. Error: {e}")
                continue

    logger.info("Program finished.")


if __name__ == "__main__":
    _time = datetime.now().strftime("%m.%d.%y-%H.%M")
    _current_file_name = osp.basename(__file__)
    if _current_file_name.endswith(".py"):
        _current_file_name = _current_file_name[:-3]

    # --- set up arguments ---
    parser = HfArgumentParser(ArticleProcessingArgs)
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # If we pass only one argument to the script and it's the path to a json file,
        # let's parse it to get our arguments.
        (arguments,) = parser.parse_json_file(json_file=osp.abspath(sys.argv[1]))
    else:
        (arguments,) = parser.parse_args_into_dataclasses()

    if arguments.log_path is None:
        arguments.log_path = osp.join("logs", f"{_current_file_name}.{_time}.log")

    set_logging(arguments.log_path, level="INFO")
    logging_args(arguments)

    process_articles(args=arguments)
