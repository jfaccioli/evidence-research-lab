from pathlib import Path

from crl.production.kill_switch import (
    clear_kill_switch,
    engage_kill_switch,
    is_kill_switch_engaged,
    kill_switch_path,
)


def test_kill_switch_file(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CRL_KILL_SWITCH", raising=False)
    # point project root via chdir
    import crl.production.kill_switch as ks

    monkeypatch.setattr(ks, "project_root", lambda: tmp_path)
    assert is_kill_switch_engaged() is False
    engage_kill_switch(tmp_path, reason="test")
    assert is_kill_switch_engaged() is True
    clear_kill_switch(tmp_path)
    assert is_kill_switch_engaged() is False
    assert kill_switch_path(tmp_path).exists()
