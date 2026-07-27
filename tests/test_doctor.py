from crl.ops.doctor import run_doctor


def test_doctor_runs_and_live_disabled():
    rep = run_doctor()
    assert rep.checks
    by = {c.name: c for c in rep.checks}
    assert by["live_disabled_by_default"].ok
    assert by["gates_loaded"].ok
    assert by["bare_place_order_disabled"].ok
