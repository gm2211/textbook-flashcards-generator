import logging as log


# Configure the logging system
class HumanFriendlyFormatter(log.Formatter):
    def formatTime(self, record, datefmt=None):
        """
        Override the formatTime method to display elapsed time in a human-readable format:
        X seconds Y millis, or minutes/hours when appropriate.
        """
        # Get the number of milliseconds since the start of the logging system
        elapsed_time = record.relativeCreated

        # Calculate hours, minutes, seconds, and milliseconds
        millis = int(elapsed_time % 1000)
        seconds = int((elapsed_time / 1000) % 60)
        minutes = int((elapsed_time / (1000 * 60)) % 60)
        hours = int((elapsed_time / (1000 * 60 * 60)) % 24)

        if hours > 0:
            return f"{hours} hours {minutes} minutes {seconds} seconds {millis} millis"
        elif minutes > 0:
            return f"{minutes} minutes {seconds} seconds {millis} millis"
        else:
            return f"{seconds} seconds {millis} millis"


def setup_logging(clear_existing_handlers=False):
    logger = log.getLogger()
    logger.setLevel(log.INFO)
    if logger.hasHandlers() and clear_existing_handlers:
        logger.handlers.clear()
    console_handler = log.StreamHandler()
    console_handler.setFormatter(
        HumanFriendlyFormatter(
            '[Proc ID: %(process)s] %(levelname)s - %(message)s - [Elapsed: %(asctime)s]'
        )
    )
    logger.addHandler(console_handler)
