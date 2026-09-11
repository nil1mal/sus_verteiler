from src.utils.logging_config import setup_logging
import logging

from src.utils.asp_generator import generate_asp, generate_config, load_rules
from src.utils.data_processing import load_data, prepare_data
from src.utils.solver import run_clingo
from src.utils.parser import parse_clingo_output, map_ids_to_names, save_output
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Student assignment pipeline")

    parser.add_argument(
        "--exp_name",
        type=str,
        default=None,
        required=False,
        help="Experiment name (optional)"
    )

    parser.add_argument(
        "--input_folder",
        type=str,
        default="./data/",
        help="Input folder (default: ./data/)"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "multi"],
        default="single",
        help="Assignment mode: single day (default) or multi day"
    )

    parser.add_argument(
        "--companies",
        type=str,
        nargs="+",
        default=None,
        help="Paths to company CSVs per day (required if --mode multi, e.g. --companies d1.csv d2.csv)"
    )

    parser.add_argument(
        "--prefs",
        type=str,
        nargs="+",
        default=None,
        help="Paths to preference CSVs per day (required if --mode multi, e.g. --prefs d1_prefs.csv d2_prefs.csv)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=3000,
        help="Clingo time limit in seconds (default: 3000 sec)"
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Parallel CPUs used"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    return parser.parse_args()

def main():
    args = parse_args()

    if args.timeout <= 0:
        raise ValueError("--timeout must be a positive integer")

    if args.mode == "multi":
        if not args.companies or not args.prefs:
            raise ValueError("--mode multi requires --companies and --prefs")
        if len(args.companies) != len(args.prefs):
            raise ValueError("--companies and --prefs must have the same number of paths")

    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(args.exp_name, log_level)

    logging.info("Starting pipeline [mode=%s]", args.mode)
    logging.info("Using timeout: %s seconds", args.timeout)
    logging.info("Using %s threads", args.threads)

    students, prefs, companies = load_data(
        args.input_folder,
        mode=args.mode,
        companies_paths=args.companies,
        prefs_paths=args.prefs
    )
    final_df, students_df = prepare_data(students, prefs)

    generate_asp(final_df, companies, mode=args.mode)
    rules = load_rules()
    generate_config(companies, rules)

    output = run_clingo(timeout=args.timeout, threads=args.threads)

    assignments = parse_clingo_output(output)
    final_assignments = map_ids_to_names(assignments, students_df)

    save_output(final_assignments, args.exp_name)

    logging.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()