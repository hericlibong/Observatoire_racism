import os
import tempfile
from pathlib import Path
import unittest

from src.assemblee_contextualization.env import load_dotenv


class EnvLoaderTest(unittest.TestCase):
    def test_loads_dotenv_without_overriding_existing_env(self) -> None:
        old_key = os.environ.get("MISTRAL_API_KEY")
        old_model = os.environ.get("MISTRAL_MODEL")
        try:
            os.environ["MISTRAL_API_KEY"] = "from-env"
            os.environ.pop("MISTRAL_MODEL", None)
            with tempfile.TemporaryDirectory() as tmp_dir:
                env_path = Path(tmp_dir) / ".env"
                env_path.write_text(
                    "MISTRAL_API_KEY=from-file\nMISTRAL_MODEL=test-model\n",
                    encoding="utf-8",
                )

                load_dotenv(env_path)

            self.assertEqual(os.environ["MISTRAL_API_KEY"], "from-env")
            self.assertEqual(os.environ["MISTRAL_MODEL"], "test-model")
        finally:
            _restore_env("MISTRAL_API_KEY", old_key)
            _restore_env("MISTRAL_MODEL", old_model)

    def test_missing_dotenv_keeps_safe_fallback_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            load_dotenv(Path(tmp_dir) / ".env")


def _restore_env(key: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
