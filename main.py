from utils.logging_config import setup_logging
import logging
import argparse

from utils.asp_generator import generate_asp, generate_config, load_rules
from utils.data_processing import load_data, prepare_data
from utils.asp_generator import generate_asp, generate_config
from utils.solver import run_clingo
from utils.parser import parse_clingo_output, map_ids_to_names, save_output

def parse_args():
    parser = argparse.ArgumentParser(description="Student assignment pipeline")

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

    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)

    logging.info("Starting pipeline")
    logging.info("Using timeout: %s seconds", args.timeout)
    logging.info("Using %s threads", args.threads)

    students, prefs, companies = load_data()
    final_df, students_df = prepare_data(students, prefs)

    generate_asp(final_df, companies)
    rules = load_rules()
    generate_config(companies, rules)

    output = run_clingo(timeout=args.timeout, threads=args.threads)

    assignments = parse_clingo_output(output)
    final_assignments = map_ids_to_names(assignments, students_df)

    save_output(final_assignments)

    logging.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()