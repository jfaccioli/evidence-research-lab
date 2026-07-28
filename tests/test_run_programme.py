from pathlib import Path

import pytest

from crl.ops.run_programme import run_programme


def test_run_programme_missing_dir():
    with pytest.raises(FileNotFoundError):
        run_programme(Path("examples/batch/does_not_exist_xyz"), require_doctor=False)
