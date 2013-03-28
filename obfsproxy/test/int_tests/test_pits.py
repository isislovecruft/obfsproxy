import os
import logging
import twisted.trial.unittest

import pits

class PITSTest(twisted.trial.unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        self.treader.cleanup()

    def _doTest(self, transport_name, test_case_file):
        self.treader = pits.TestReader(self.assertTrue, test_case_file)
        return self.treader.do_test(
            ('%s' % transport_name,
             'client',
             '127.0.0.1:%d' % pits.CLIENT_OBFSPORT,
             '--dest=127.0.0.1:%d' % pits.SERVER_OBFSPORT),
            ('%s' % transport_name,
             'server',
             '127.0.0.1:%d' % pits.SERVER_OBFSPORT,
             '--dest=127.0.0.1:%d' % self.treader.pits.get_pits_inbound_address().port))

    def _doTest_shared_secret(self, transport_name, test_case_file):
        self.treader = pits.TestReader(self.assertTrue, test_case_file)
        return self.treader.do_test(
            ('%s' % transport_name,
             'client',
             '127.0.0.1:%d' % pits.CLIENT_OBFSPORT,
             '--shared-secret=test',
             "--ss-hash-iterations=50",
             '--dest=127.0.0.1:%d' % pits.SERVER_OBFSPORT),
            ('%s' % transport_name,
             'server',
             '127.0.0.1:%d' % pits.SERVER_OBFSPORT,
             '--shared-secret=test',
             "--ss-hash-iterations=50",
             '--dest=127.0.0.1:%d' % self.treader.pits.get_pits_inbound_address().port))

    # XXX This is pretty ridiculous. Find a smarter way to make up for the
    # absense of load_tests().
    def test_dummy_1(self):
        return self._doTest("dummy", "../test_case.pits")

    def test_dummy_2(self):
        return self._doTest("dummy", "../test_case_simple.pits")

    def test_obfs2_1(self):
        return self._doTest("obfs2", "../test_case.pits")

    def test_obfs2_2(self):
        return self._doTest("obfs2", "../test_case_simple.pits")

    def test_obfs2_shared_secret_1(self):
        return self._doTest_shared_secret("obfs2", "../test_case.pits")

    def test_obfs2_shared_secret_2(self):
        return self._doTest_shared_secret("obfs2", "../test_case_simple.pits")

    def test_obfs3_1(self):
        return self._doTest("obfs3", "../test_case.pits")

    def test_obfs3_2(self):
        return self._doTest("obfs3", "../test_case_simple.pits")

if __name__ == '__main__':
    from unittest import main
    main()
