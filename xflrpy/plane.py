from xflrpy.mixins import MsgpackMixin, DictListInterface
from xflrpy.polar2d import PolarType
from xflrpy.client import Client
import enum
import re

class WingType(enum.IntEnum):
    MAINWING = 0
    SECONDWING = 1
    ELEVATOR = 2
    FIN = 3

class enumAnalysisMethod(enum.IntEnum):
    LLTMETHOD = 0
    VLMMETHOD = 1
    PANE4LMETHOD = 2
    TRILINMETHOD = 3
    TRIUNIMETHOD = 4

class enumRefDimension(enum.IntEnum):
    PLANFORMREFDIM = 0
    PROJECTEDREFDIM = 1
    MANUALREFDIM = 2

class enumWPolarResult(enum.IntEnum):
    ALPHA = 0
    CL = 1
    XCPCL = 2 
    CD = 3
    CDP = 4
    CM = 5
    ICD = 6
    SM = 7
    FX = 8
    FY = 9
    CLCD = 10
    CL32CD = 11
    FZ = 12
    QINF = 13

class WingSection(MsgpackMixin):
    y_position = 0  # yPos(m): spanwise position of segment
    chord = 0.1 # chord(m): length of segment in x (longitudinal) direction
    offset = 0.05   # offset(m): x position from origin. Check XFLR wing design module
    dihedral = 0    # dihedral (deg): absolute dihedral angle till the next segment
    twist = 0   # twist(deg): absolute twist angle with respect to the x(longitudinal) axis
    right_foil_name = ""    # rightFoil(str): right airfoil name
    left_foil_name = "" # leftFoil(str): left airfoil name
    n_x_panels = 7  # nXPanels: number of panels along the longitudinal directions
    x_panel_dist = 0    # xPanelDist: distribution of panels in longitudinal direction
    n_y_panels = 7  # nYPanels: number of panels along the lateral directions
    y_panel_dist = 0    # yPanelDist: distribution of panels in lateral direction

    def __init__(self, y_position = 0, chord = 0.1, offset = 0.05, dihedral = 0, twist = 0, right_foil_name = "", left_foil_name = "", n_x_panels = 7, x_panel_dist = 0, n_y_panels = 7, y_panel_dist = 0) -> None:
        self.y_position = y_position
        self.chord = chord
        self.offset = offset
        self.dihedral = dihedral
        self.twist = twist
        self.right_foil_name = right_foil_name
        self.left_foil_name = left_foil_name
        self.n_x_panels = n_x_panels
        self.x_panel_dist = x_panel_dist
        self.n_y_panels = n_y_panels
        self.y_panel_dist = y_panel_dist

class Wing(MsgpackMixin):
    type = WingType.MAINWING
    sections = [] # list of WingSection
    
    def __init__(self, type=WingType.MAINWING, sections:list = None):
        self.type = type
        if sections is None:
            self.sections = []
        else:
            self.sections = sections


class PlaneDetail():
    def __init__(self, data):
        self._raw_data = data
        self._parse_data()
        
    def _parse_data(self):
        lines = self._raw_data.split('\n')
        out = {}
        for line in lines:
            try:
                k,v = line.split('=')
                value = re.search("([0-9.]+)", v).group(1)
                unit = v.split(value)[1].strip()
                out[k.strip()] = {'value':float(value), 'unit':unit}
            except:
                print(f'error parsing line "{line}"')
        self.data = out

class Plane(MsgpackMixin):
    name = ""
    wing = Wing(WingType.MAINWING)
    wing2 = Wing(WingType.SECONDWING)
    elevator = Wing(WingType.ELEVATOR)
    fin = Wing(WingType.FIN)

    def __init__(self, name="Plane Name") -> None:
        self.name = name
        self.wing = Wing(WingType.MAINWING)
        self.wing2 = Wing(WingType.SECONDWING)
        self.elevator = Wing(WingType.ELEVATOR)
        self.fin = Wing(WingType.FIN)
        self._client = Client()
    
    def __str__(self):
        return f'<Plane "{self.name}">'

    def __repr__(self):
        return self.__str__()
    
    @property
    def detail(self):
        "Get information about plane"
        details = PlaneDetail(self._client.call("getPlaneData", self.name))
        return details.data
    

class PlaneManager(DictListInterface):
    """Manager for planes and 3D objects"""

    def __init__(self) -> None:
        self._client = Client()
    
    def _get_items(self) -> dict:
        return { item["name"]:Plane.from_msgpack(item) for item in self._client.call("getPlanes") }

    # def getPlane(self, name) -> Plane:
    #     """Return an existing plane by name"""
    #     plane_raw = self._client.call("getPlane", name)
    #     assert plane_raw["name"] == name, "Please specify a valid plane name"
    #     return Plane.from_msgpack(plane_raw)
    
    # def addPlane(self, plane:Plane):
    #     assert len(plane.wing.sections) >0, "The plane wing must have at least one section!"
    #     self._client.call("addPlane", plane)

    # def addDefaultPlane(self, name):
    #     """Adds a new default plane to the list of planes"""
    #     plane_raw = self._client.call("addDefaultPlane", name)
    #     assert plane_raw["name"] == name
    #     return Plane.from_msgpack(plane_raw)


class WPolarSpec(MsgpackMixin):
    # polar tab options
    polar_type = PolarType.FIXEDSPEEDPOLAR
    free_stream_speed = 10 
    alpha = 0 # (deg) angle of attach 
    beta = 0 # (deg) sideslip angle
    
    # analysis tab options
    analysis_method = enumAnalysisMethod.VLMMETHOD
    is_viscous = True
    
    # inertia tab
    use_plane_intertia = True
    plane_mass = 0
    x_cog = 0
    z_cog = 0

    # ref dimensions
    ref_dimension = enumRefDimension.PROJECTEDREFDIM
    ref_area = 0
    ref_chord = 0
    ref_span = 0

    # aero data
    density = 1.225 # kg/m3
    kinematic_viscosity = 1.5e-05 # m2/s
    is_ground_effect = False
    height = 0 # m. Set if ground effect is tru

    def __init__(self,polar_type = PolarType.FIXEDSPEEDPOLAR, free_stream_speed = 10, alpha = 0 , beta = 0,
                 analysis_method = enumAnalysisMethod.VLMMETHOD, is_viscous = True,
                 use_plane_intertia = True, plane_mass = 0, x_cog = 0, z_cog = 0,  
                 ref_dimension = enumRefDimension.PROJECTEDREFDIM, ref_area = 0, ref_chord = 0, ref_span = 0, 
                 density = 1.225, kinematic_viscosity = 1.5e-05, is_ground_effect = False, height = 0) -> None:
        
        self.polar_type = polar_type
        self.free_stream_speed = free_stream_speed 
        self.alpha = alpha # (deg) angle of attach 
        self.beta = beta # (deg) sideslip angle
            
        # analysis tab options
        self.analysis_method = analysis_method
        self.is_viscous = is_viscous

        # inertia tab
        self.use_plane_intertia = use_plane_intertia
        self.plane_mass = plane_mass
        self.x_cog = x_cog
        self.z_cog = z_cog

        # ref dimensions
        self.ref_dimension = ref_dimension
        self.ref_area = ref_area
        self.ref_chord = ref_chord
        self.ref_span = ref_span

        # aero data
        self.density = density # kg/m3
        self.kinematic_viscosity = kinematic_viscosity # m2/s
        self.is_ground_effect = is_ground_effect
        self.height = height # m. Set if ground effect is tru
        
class WPolarResult(MsgpackMixin):
    """ 
    A custom simplified data structure for the polar result.
    Filling this is slow so you might want to avoid it when running optimizations
    """
    alpha = [] # angle of attach
    beta = [] # sideslip angle
    Q_inf = []

    # lift coefficients
    Cl = []
    ClCd = []
    Cl32Cd = []

    # drag coefficients
    TCd = [] # total drag
    ICd = [] # indueced drag
    PCd = [] # profile drag

    # moment coefficients
    Cm = []  # total pitching moment coefficient
    ICm = [] # induced pitching moment coefficient
    IYm = [] # induced yawing moment coefficient
    VCm = [] # viscous pitching moment

    # forces
    FZ = [] # total wing lift
    FX = [] # total drag force
    FY = [] # total side force

    # moments
    Rm = [] # total rolling moment
    Pm = [] # total pitching moment
    max_bending = [] # max bending moment at chord

    # stability
    XCpCl = [] # neutral point
    SM = [] # static margin

class WPolar(MsgpackMixin):
    name = ""
    plane_name = ""
    spec = WPolarSpec()
    result = WPolarResult()

    def __init__(self, name="", plane_name="") -> None:
        self.name = name
        self.plane_name = plane_name
        self.spec = WPolarSpec()
        self.result = WPolarResult()

class AnalysisSettings3D(MsgpackMixin):
    sequence = (0,0,0)
    is_sequence = False
    init_LLT = True
    store_opp = True

    def __init__(self, sequence = (0,0,0), is_sequence = False, init_LLT = True, store_opp = True) -> None:
        self.sequence = sequence
        self.is_sequence = is_sequence
        self.init_LLT = init_LLT
        self.store_opp = store_opp

class WingAndPlaneDesignModule:
    """
    to manage the plane design application
    """
    def __init__(self, client) -> None:
        self._client = client
        self.plane_mgr = PlaneManager(client)

    def define_analysis(self, wpolar:WPolar):
        """Takes Polar as argument (and not polar.name) because we're creating a new Polar on the heap everytime"""
        self._client._call("defineAnalysis3D", wpolar.to_msgpack())

    def analyze(self, polar_name:str, plane_name:str, analysis_settings: AnalysisSettings3D, result_list = []):
        """Analyses the current polar"""
        wpolar_result_raw = self._client._call("analyzeWPolar", polar_name, plane_name, analysis_settings, result_list)
        return WPolarResult.from_msgpack(wpolar_result_raw)
