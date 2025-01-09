from xflrpy import Client

class TestBase:
    def setup_method(self, test_method):
        Client().connect()
        Client().foils.delete_all()

    def teardown_method(self, test_method):
        if Client().is_connected:
            Client().foils.delete_all()
            Client().close()