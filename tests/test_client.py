import unittest
from xflrpy import exceptions
from xflrpy import Client
from base_test import TestBase
import pytest

class TestClient(unittest.TestCase, TestBase):
    
    def test_connection(self):
        c = Client()
        assert c.is_connected == True
        assert 'connected' in c.state
        assert 'display' in c.state
        assert '<XFLRClient>' in c.__repr__()

    def test_call_after_close(self):
        c = Client()
        assert c.is_connected == True
        c.close()
        with pytest.raises(exceptions.ClientNotConnectedException) as e_info:
            c.state
 
    def test_singleton(self):
        c = Client()
        assert c.is_connected == True
        c.close()
        assert c.is_connected == False
        c = Client().connect()
        assert c.is_connected == True

    # def test_timeout_connection(self):
    #     c = Client()
    #     c.close()
        # c.connect('10.10.0.1', connect_timeout = 1)
        # with pytest.raises(TimeoutError) as e_info:
        #     c.connect('10.10.0.1', connect_timeout = 1)
        # c.connect()