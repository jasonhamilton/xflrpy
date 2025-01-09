import unittest
from xflrpy.module import ModuleType
from xflrpy import Client
from base_test import TestBase

class TestModule(unittest.TestCase, TestBase):
    
    def test_active(self):
        client = Client()
        assert client.modules.active in ModuleType
        client.modules.set(ModuleType.DIRECTFOILDESIGN)
        assert client.modules.active == ModuleType.DIRECTFOILDESIGN
        client.modules.set(ModuleType.XFOILINVERSEDESIGN)
        assert client.modules.active == ModuleType.XFOILINVERSEDESIGN
        client.modules.set(ModuleType.XFOILDIRECTANALYSIS)
        assert client.modules.active == ModuleType.XFOILDIRECTANALYSIS
        client.modules.set(ModuleType.WINGANDPLANEDESIGN)
        assert client.modules.active == ModuleType.WINGANDPLANEDESIGN
        # CANNOT SET NOAPP ONCE IT'S BEEN CHANGED    

        

