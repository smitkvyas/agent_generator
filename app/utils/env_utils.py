import os

from dotenv import load_dotenv

load_dotenv()


class Env:
    """
    Utility class for accessing environment variables.

    - Automatically loads variables from `.env`
    - Supports default values
    - Can enforce required variables
    """

    @staticmethod
    def get(key: str, default=None, required: bool = False):
        """
        Retrieve an environment variable.

        Args:
            key: Environment variable name
            default: Fallback value if variable is not set
            required: Raise error if variable is missing

        Returns:
            Value of the environment variable

        Raises:
            RuntimeError: If required is True and variable is missing
        """
        value = os.getenv(key, default)
        if required and value is None:
            raise RuntimeError(f"Missing required env var: {key}")
        return value
