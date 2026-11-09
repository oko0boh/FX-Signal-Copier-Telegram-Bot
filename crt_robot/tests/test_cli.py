from crt_robot.data import __main__ as cli
from crt_robot.data import dukascopy as dk


def test_download_cli_stops_on_blocked_host(monkeypatch, capsys):
    def blocked(*a, **k):
        raise dk.DataHostBlocked(dk.HOST, "HTTP 429 Too Many Requests")

    monkeypatch.setattr(dk, "download", blocked)
    assert cli.main(["download", "--symbols", "EURUSD", "--start", "2024-01-01", "--end", "2024-01-02"]) == 2
    err = capsys.readouterr().err
    assert "datafeed.dukascopy.com" in err and "No data was invented" in err


def test_quality_cli_without_data(tmp_path, monkeypatch):
    monkeypatch.setattr(dk, "DATA_CACHE", tmp_path)

    def no_data(sym, *a, **k):
        raise FileNotFoundError(f"no cached data for {sym}")

    monkeypatch.setattr(dk, "load", no_data)
    out = tmp_path / "q.md"
    assert cli.main(["quality", "--symbols", "EURUSD", "--out", str(out)]) == 0
    assert "No data" in out.read_text()
