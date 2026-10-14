import errno
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ledger.store import LedgerLocked, ledger_lock


class LedgerLockTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ledger = Path(self.dir.name) / "ledger.tsv"
        self.ledger.write_text("", encoding="utf-8")

    def tearDown(self):
        self.dir.cleanup()

    def test_the_lock_is_released_after_the_block(self):
        with ledger_lock(self.ledger):
            pass
        with ledger_lock(self.ledger):
            pass

    def test_the_lock_is_released_when_the_block_raises(self):
        with self.assertRaises(KeyError):
            with ledger_lock(self.ledger):
                raise KeyError("boom")
        with ledger_lock(self.ledger):
            pass

    def test_a_lock_another_process_holds_raises_ledger_locked(self):
        held = PermissionError(errno.EACCES, "Permission denied")
        with mock.patch("ledger.store.fcntl.flock", side_effect=held):
            with self.assertRaises(LedgerLocked):
                with ledger_lock(self.ledger):
                    pass

    def test_the_lock_file_sits_beside_the_ledger(self):
        with ledger_lock(self.ledger):
            self.assertTrue((Path(self.dir.name) / "ledger.tsv.lock").exists())


if __name__ == "__main__":
    unittest.main()
