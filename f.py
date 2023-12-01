import argparse
import logging

def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Create an Archive BitBucket Project'
    )

    parser.add_argument(
        '--show-dependabot-alerts-only',
        help='Enable repos with depedendabot alerts enabled only',
        action='store_const',
        dest='dependabot_alerts_only',
        const=True, default=False,
    )

    parser.add_argument(
        '--debug',
        help='Display "debugging" in output (defaults to "info")',
        action='store_const', dest='verbosity',
        const=logging.DEBUG, default=logging.INFO,
    )

    parser.add_argument(
        '--error-only',
        help='Display "error" in output only (filters "info")',
        action='store_const', dest='verbosity',
        const=logging.ERROR,
    )

    args = parser.parse_args()
    return args
# /def