from crl.ops.programmes import list_programmes, programmes_to_dict


def test_list_programmes_nonempty():
    rows = list_programmes()
    assert len(rows) >= 5
    d = programmes_to_dict(rows)
    assert d["n_programmes"] == len(rows)
    assert d["n_hyps_total"] >= len(rows)
