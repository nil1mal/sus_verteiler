import subprocess
import logging


def run_clingo(timeout: int = 3000, threads: int = 4, multi: bool = False):
    logging.info("Running Clingo with timeout=%s seconds", timeout)

    try:
        if multi:
            result = subprocess.run(
            [
                "clingo",
                "src/data.lp",
                "src/config.lp",
                "src/model_multi.lp",
                "--opt-mode=optN",
                f"--time-limit={timeout}",
                "-t", f"{threads}"
            ],
            capture_output=True,
            text=True
            )
        else:
            result = subprocess.run(
                [
                    "clingo",
                    "src/data.lp",
                    "src/config.lp",
                    "src/model.lp",
                    "--opt-mode=optN",
                    f"--time-limit={timeout}",
                    "-t", f"{threads}"
                ],
                capture_output=True,
                text=True
            )
    except FileNotFoundError:
        logging.error("Clingo executable not found")
        raise RuntimeError("Clingo not installed or not in PATH")

    logging.info("Clingo finished")

    if result.returncode != 0:
        logging.warning("Clingo returned non-zero exit code")

    return result.stdout