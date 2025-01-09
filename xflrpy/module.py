import enum

class ModuleType(enum.IntEnum):
    NOAPP = 0
    DIRECTFOILDESIGN = 2
    XFOILINVERSEDESIGN = 3
    XFOILDIRECTANALYSIS = 1
    WINGANDPLANEDESIGN = 4

from xflrpy.module import ModuleType

class ModuleManager():
    def __init__(self):
        from xflrpy.client import Client
        self._client = Client()
        self.active = None
    
    def set(self, module:ModuleType):
        if self.active != module:
            self._client.call("setApp", int(module))
            self._client._update_state()
    
    def _handle_state_change(self, newstate):
        self.active = ModuleType(newstate.current_module)

# class enumGraphView(enum.IntEnum):
#     ONEGRAPH = 0 
#     TWOGRAPHS = 1 
#     FOURGRAPHS = 2
#     ALLGRAPHS = 3
#     NOGRAPH = 4

# class XDirectDisplayState(MsgpackMixin):
#     polar_view = True  # False = OpPointView

#     # Polar View
#     graph_view = enumGraphView.ALLGRAPHS
#     which_graph = 1
    
#     # OpPointView
#     active_opp_only = True
#     show_bl = True
#     show_pressure = True
#     show_cpgraph = True # False = qgraph
#     animated = False
#     ani_speed = 500 # (0, 1000)

#     # need this init method to allow creation of a custom display
#     # state in python and send it over to cpp
#     def __init__(self, polar_view = True, graph_view = enumGraphView.ALLGRAPHS, which_graph = 1, active_opp_only = True, show_bl = False, show_pressure = False, show_cpgraph = True, animated = False, ani_speed = 500) -> None:
#         self.polar_view = polar_view
#         self.graph_view = graph_view
#         self.which_graph = which_graph
#         self.active_opp_only = active_opp_only
#         self.show_bl = show_bl
#         self.show_pressure = show_pressure
#         self.show_cpgraph = show_cpgraph
#         self.animated = animated
#         self.ani_speed = ani_speed
 