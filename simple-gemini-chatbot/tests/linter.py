import subprocess
import os
import sys

def run_linting(src_dir, tests_dir):
    """Runs pylint on the source directory and saves the output to a log file."""

    lint_log_file = os.path.join(tests_dir, "lint_report.txt")

    # Create the tests directory if it doesn't exist
    os.makedirs(tests_dir, exist_ok=True)

    try:
        # Run pylint (capture stdout and stderr)
        result = subprocess.run(
            ["pylint", "--recursive=y", src_dir],
            capture_output=True,
            text=True,  # Important for decoding output as text
            check=True,  # Raise an exception if pylint fails
        )

        with open(lint_log_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)
            f.write(result.stderr) # captures any errors that pylint may throw
            
        print(f"Linting passed. Report written to: {lint_log_file}")
        return True

    except subprocess.CalledProcessError as e:
        with open(lint_log_file, "w", encoding="utf-8") as f:
            f.write(e.stdout)
            f.write(e.stderr)
        print(f"Linting failed. Report written to: {lint_log_file}")
        return False
    except FileNotFoundError:
        print("Error: pylint not found. Make sure it's installed.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


if __name__ == "__main__":
    src_dir = "./src"
    tests_dir = "./tests"
    
    if run_linting(src_dir, tests_dir):
      sys.exit(0) # Success
    else:
      sys.exit(1) # Failure