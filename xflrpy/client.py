import msgpackrpc as rpc
from xflrpy.module import ModuleType
from xflrpy.exceptions import ClientAlreadyConnectedException, ClientNotConnectedException
from collections import defaultdict
import time

class ServerStateMessage():

    @classmethod
    def from_msgpack(cls, msgpack):
        state = cls()
        state.project_path = msgpack['projectPath']
        state.project_name = msgpack['projectName']
        state.current_module = msgpack['app']
        state.saved = msgpack['saved']
        state.display = msgpack['display']
        state.app_enum = ModuleType(msgpack['app'])
        return state

class Client():
    """
    Client class manages the connection to the XFLR5-RPC server.  The class uses the singleton pattern to
    avoid having to pass the client down the class hierarchy to each child.

    Returns:
        Client: instance of Client
    """
    _instance = None
    call_count = defaultdict(lambda: 0)
    call_time = defaultdict(lambda: 0)
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Client, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance
    def connect(self, ip = '127.0.0.1', port = 8080, connect_timeout = 300):
        """
        Initiates the connection to the server.  This should only be run only if the client is not connected, otherwise
        it will throw a ClientAlreadyConnectedException.  Returns self to allow chaining, for example 'client = Client().connect()'.

        Args:
            ip (str): IP Address of remote XFLR5-RPC server
            port (int): Port of remote XFLR5-RPC server
            connect_timeout (int): timeout in seconds to wait before raising an error.  Note that some calls stay open while the server
                is processing so too low of a value may cause problems.
        Returns:
            Client: instance of Client on success
        """
        if self.is_connected:
            raise ClientAlreadyConnectedException('client already connected')
        
        from xflrpy.project import ProjectManager
        from xflrpy.foil import FoilManager
        from xflrpy.plane import PlaneManager
        from xflrpy.module import ModuleManager
        
        self.remote_address = f"{ip}:{port}"
        self._state = {}
        self._rpc_client = rpc.Client(rpc.Address(ip, port), timeout=connect_timeout, pack_encoding='utf-8', unpack_encoding='utf-8')
        self.project = ProjectManager()
        self.foils = FoilManager()
        self.planes = PlaneManager()
        self.modules = ModuleManager()
        try:
            if self.is_connected:
                self._update_state()
                return self
        except rpc.error.TransportError:
            print("Could not connect to the XFLR5 server. Is the application gui running?\n")
    
    def call(self, rpc_call, *args, **kwargs):
        """
        Delegates call method to the RPC client.  Updates state after each call to ensure state is in sync.

        Args:
            rpc_call (str): name of rpc function on server
        Returns:
            any: returns raw result of rpc response from server
        """
        self.call_count[rpc_call] += 1
        call_id = sum(self.call_count.values())
        
        self._ensure_rpc_client_exists()
        # print(f'CALL STARTED: {rpc_call} ({call_id})', *args, **kwargs)
        # print(f'CALL STARTED: {rpc_call} ({call_id})')
        start = time.time()
        res = self._rpc_client.call(rpc_call, *args, **kwargs)
        timer = time.time() - start
        # print(f'CALL COMPLETE: {timer:.2f} seconds ({call_id})', res)
        # print(f'CALL COMPLETE: {timer:.2f} seconds ({call_id})')
        self.call_time[rpc_call] += timer
        # self._update_state()
        return res
    
    def close(self) -> None:
        """
        Closes the connection with the server.

        Returns:
            None
        """
        self._rpc_client.close()
        delattr(self, "_rpc_client")

    @property
    def is_connected(self) -> bool:
        """
        Returns true is the server is connected to the client and data can be exchanged.
        """
        if not hasattr(self, '_rpc_client'):
            return False
        return self.call("ping")
    
    @property
    def state(self) -> dict:
        self._ensure_rpc_client_exists()
        self._update_state()
        return { 
                'connected': self.is_connected, 
                'display': self._state['display'],
                }
    def _ensure_rpc_client_exists(self):
        if not hasattr(self, '_rpc_client'):
            raise ClientNotConnectedException("Client is not connected")

    def _update_state(self) -> None:
        """
        Gets updated state from server and passes updated state to children

        Returns:
            None
        """  
        new_state =  ServerStateMessage.from_msgpack(self._rpc_client.call("getState"))
        self._state = {
            'current_module' : new_state.current_module,
            'saved' : new_state.saved,
            'display' : new_state.display
        }
        self.project._handle_state_change(new_state)
        self.modules._handle_state_change(new_state)

    def __str__(self):
        connected_str = "connected" if self.is_connected else "not connected"
        return f"<XFLRClient>(server:{self.remote_address}, status:{connected_str})"
    
    def __repr__(self):        
        return self.__str__()
