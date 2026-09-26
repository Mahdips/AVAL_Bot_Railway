"""Tests for the backup manager: listing, download, restore and upload."""

import os
import sqlite3

os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("ADMIN_IDS", "1")

import bot


def _make_db(tmp_path, marker):
    tmp_path.mkdir(parents=True, exist_ok=True)
    p = tmp_path / marker
    conn = sqlite3.connect(str(p))
    conn.execute("create table t(v integer)")
    conn.execute("insert into t values (42)")
    conn.commit()
    conn.close()
    return p


def test_list_backups_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(bot, "DATABASE_FILE", tmp_path / "bot.db")
    assert bot.list_backups() == []


def test_create_and_list_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(bot, "DATABASE_FILE", tmp_path / "bot.db")
    (tmp_path / "bot.db").write_bytes(b"")
    # create_database_backup uses sqlite backup, so build a real db first
    conn = sqlite3.connect(str(tmp_path / "bot.db"))
    conn.execute("create table t(v integer)")
    conn.execute("insert into t values (1)")
    conn.commit()
    conn.close()

    path = bot.create_database_backup()
    assert path is not None
    assert path.parent == tmp_path / "backups"
    assert path.exists()

    backups = bot.list_backups()
    assert len(backups) == 1
    assert backups[0][0] == path


def test_restore_database(tmp_path, monkeypatch):
    # current db
    monkeypatch.setattr(bot, "DATABASE_FILE", tmp_path / "bot.db")
    conn = sqlite3.connect(str(tmp_path / "bot.db"))
    conn.execute("create table t(v integer)")
    conn.execute("insert into t values (1)")
    conn.commit()
    conn.close()

    # a backup with a different value
    backup_path = _make_db(tmp_path / "backups", "bot_backup_20250101_000000.db")
    conn = sqlite3.connect(str(backup_path))
    conn.execute("delete from t")
    conn.execute("insert into t values (99)")
    conn.commit()
    conn.close()

    ok = bot.restore_database_from(backup_path)
    assert ok is True

    conn = sqlite3.connect(str(tmp_path / "bot.db"))
    assert conn.execute("select v from t").fetchone() == (99,)
    conn.close()

    # a safety copy of the old db was made
    safety = list((tmp_path / "backups").glob("pre_restore_*.db"))
    assert len(safety) == 1


def test_restore_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bot, "DATABASE_FILE", tmp_path / "bot.db")
    (tmp_path / "bot.db").write_bytes(b"")
    assert bot.restore_database_from(tmp_path / "nope.db") is False
