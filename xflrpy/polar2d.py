from xflrpy.mixins import MsgpackMixin, DictListInterface
from xflrpy import Client
import enum
from xflrpy.module import ModuleType
import time
from xflrpy.exceptions import Analysis2dInitializationError, AnalysisDoesNotExistError


class PolarResultType(enum.IntEnum):
    ALPHA = 0
    CL = 1
    XCP = 2
    CD = 3
    CDP = 4
    CM = 5
    XTR1 = 6
    XTR2 = 7
    HMOM = 8
    CPMN = 9
    CLCD = 10
    CL32CD = 11
    RTCL = 12
    RE = 13


class enumSequenceType(enum.IntEnum):
    ALPHA = 0
    CL = 1
    REYNOLDS = 2


class PolarType(enum.IntEnum):
    FIXEDSPEEDPOLAR = 0
    FIXEDLIFTPOLAR = 1
    RUBBERCHORDPOLAR = 2
    FIXEDAOAPOLAR = 3
    STABILITYPOLAR = 4
    BETAPOLAR = 5


class AnalysisSettings2D(MsgpackMixin):
    sequence_type = enumSequenceType.ALPHA.value
    sequence = (0, 0, 0)
    is_sequence = False
    init_BL = True
    store_opp = True
    viscous = True
    keep_open_on_error = False

    def __init__(self, sequence_type=enumSequenceType.ALPHA.value, sequence=(0, 0, 0), init_BL=True, store_opp=True,
                 viscous=True, keep_open_on_error=False) -> None:
        self.sequence_type = sequence_type
        self.sequence = sequence
        self.is_sequence = (sequence[1] != 0 and sequence[2] != 0)
        self.init_BL = init_BL
        self.store_opp = store_opp
        self.viscous = viscous
        self.keep_open_on_error = keep_open_on_error

class BatchAnalysisSettings2D(MsgpackMixin):
    foil_names = []
    re_list = []
    mach = 0
    ncrit = 9
    polarType = PolarType.FIXEDLIFTPOLAR
    transition_top = 1
    transition_bot = 1
    range_type_alpha = True
    min = 1
    max = 10
    increment = 0.25
    from_zero = True
    init_bl = True
    store_op_point = True
    update_polar_view = True
    thread_count = 0  # 0 = auto

class PolarSpec(MsgpackMixin):
    polar_type = PolarType.FIXEDSPEEDPOLAR
    re_type = 1
    ma_type = 1
    aoa = 0.0
    mach = 0.0
    ncrit = 9.0
    xtop = 1.0
    xbot = 1.0
    reynolds = 100000.0

    def __init__(self, polar_type=PolarType.FIXEDSPEEDPOLAR, re_type=1, ma_type=1, aoa=0.0, mach=0.0, ncrit=9.0,
                 xtop=1.0, xbot=1.0, reynolds=100000.0) -> None:
        if (type(polar_type) == int):
            self.polar_type = polar_type
        elif (type(polar_type) == PolarType):
            self.polar_type = polar_type.value
        else:
            print('invalid polar type received')
        self.Re_type = re_type
        self.ma_type = ma_type
        self.aoa = aoa
        self.mach = mach
        self.ncrit = ncrit
        self.xtop = xtop
        self.xbot = xbot
        self.reynolds = reynolds


class PolarResult(MsgpackMixin):
    """ 
    A custom simplified data structure for the polar result.
    Filling this is slow so you might want to avoid it when running optimizations
    """
    alpha = []
    Cl = []
    XCp = []
    Cd = []
    Cdp = []
    Cm = []
    XTr1 = []
    XTr2 = []
    HMom = []
    Cpmn = []
    ClCd = []
    Cl32Cd = []
    RtCl = []
    Re = []

    def __init__(self):
        pass

    @property
    def keys(self):
        return [attr for attr in vars(self) if not attr.startswith('_')]

    @property
    def dict(self):
        return {k: self.__dict__[k] for k in self.keys}

    def __len__(self):
        return len(self.alpha)

    def __str__(self):
        data = self.dict
        keys = self.keys
        available_data_keys = [k for k in keys if len(data[k])>0]
        return f'PolarResult - {self.__len__()} points: {", ".join(available_data_keys)}'


class XflrPolar(MsgpackMixin):
    name = ""
    foil_name = ""
    spec = PolarSpec()

    def __init__(self):
        self._client = Client()
        self.spec = PolarSpec()

    @classmethod
    def from_msgpack(cls, msgpack):
        p = cls()
        p.foil_name = msgpack['foil_name']
        p.name = msgpack['name']
        p.spec = msgpack['spec']
        return p

    def to_msgpack(self):
        return {
            'foil_name': self.foil_name,
            'name': self.name,
            'spec': self.spec,
            # 'result': self.result,
        }

    def __str__(self):
        return f'<XflrPolar>(foil:{self.foil_name} name:{self.name})'



class Analysis2d(MsgpackMixin):
    """
    An Analysis2d creates an simplified interface retrieving and working with the XFLR objects XflrPolar, PolarResult, 
    PolarSpec, and OPPoint.

    XflrPolar contains PolarSpec - Once created these are immutable

    INTERFACE:
        XflrPolar + PolarSpec
        result = PolarResult
        TODO: OPPoint


    
    """

    @classmethod
    def create(cls, foil_name, name='', polar_type=PolarType.FIXEDSPEEDPOLAR, reynolds=10000, re_type=1, ma_type=1,
               aoa=0, mach=0.0, ncrit=9.0, xtop=1.0, xbot=1.0):
        
        spec = PolarSpec(polar_type, re_type=re_type, ma_type=ma_type, aoa=aoa,
                           mach=mach, ncrit=ncrit, xtop=xtop, xbot=xbot, reynolds=reynolds)
        return cls.create_from_polarspec(foil_name, name, spec)
    
    @classmethod
    def create_from_polarspec(cls, foil_name, name='', polar_spec=None):
        if not polar_spec:
            polar_spec = PolarSpec()

        p = XflrPolar()
        p.foil_name = foil_name
        p.name = name
        p.spec = polar_spec
        res = Client().call("defineAnalysis2D", p.to_msgpack())
        p = XflrPolar.from_msgpack(res)
        return Analysis2d(polar=p)
    
    def __init__(self, foil_name=None, polar=None) -> None:
        self.deleted = False
        if not foil_name and not polar:
            raise Analysis2dInitializationError(
                "error, cannot initialize Analysis2d.  Need either a foil or a polar")
        if foil_name and polar:
            if polar.foil_name != foil_name:
                raise Analysis2dInitializationError(
                    'error: foil name and polar name do not match!')
        if foil_name:
            self._foil_name = foil_name
        if polar:
            self._xflr_polar = polar
            self._foil_name = polar.foil_name
        else:
            self._xflr_polar = XflrPolar()

        self._client = Client()
        # self._polar_result = PolarResult()
        # self._fetch_polar_info()
        # self._fetch_polar_analysis()

    @property
    def parameters(self) -> dict:
        "Get the analysis parameters"
        info = self._fetch_polar_info()
        return info
    
    @property
    def polar(self):
        polar_result = self._fetch_polar_analysis()
        return polar_result

    
    @property
    def op_points(self):
        return self._fetch_op_points()
    
    def run_analysis(self, sequence_type=enumSequenceType.ALPHA, sequence=(0, 0, 0),
                     op_point_values=[r for r in PolarResultType]):
        self._ensure_not_deleted()
        settings = AnalysisSettings2D(
            sequence_type=sequence_type, sequence=sequence)
        if (not self._validate_data_requested_data_points(op_point_values)):
            return
        self._client.modules.set(ModuleType.XFOILDIRECTANALYSIS)
        polar_result_raw = self._client.call(
            "analyzePolar", self._xflr_polar, settings, op_point_values)
        return PolarResult.from_msgpack(polar_result_raw)

    def delete(self):
        self.deleted = True
        self._client.call(
            "deletePolar", self._xflr_polar.foil_name, self._xflr_polar.name)

    def _fetch_polar_point_count(self):
        self._ensure_not_deleted()
        self._fetch_polar_analysis([PolarResultType.ALPHA])
        if self._polar_result == None:
            return 0
        return len(self._polar_result)


    # FETCHING METHODS
    def _fetch_polar_info(self, set_current=True, select=True) -> XflrPolar:
        self._ensure_not_deleted()
        """
        Get polar info from server.  
        """
        polar_raw = self._client.call(
            "getPolar", self._foil_name, self._xflr_polar.name, set_current, select)
        res = XflrPolar.from_msgpack(polar_raw)
        self._xflr_polar.spec = res
        return res

    def _fetch_polar_analysis(self, op_point_values=[r for r in PolarResultType]):
        self._ensure_not_deleted()
        if (not self._validate_data_requested_data_points(op_point_values)):
            return
        polar_result_raw = self._client.call(
            "getPolarResult", self._xflr_polar.foil_name, self._xflr_polar.name, op_point_values)
        return PolarResult.from_msgpack(polar_result_raw)
    
    def _fetch_op_points(self):
        res = self._client.call("getOpPoints", self._xflr_polar.foil_name, self._xflr_polar.name)
        return [OpPoint.from_msgpack(o) for o in res]
        
    def _validate_data_requested_data_points(self, values):
        "Validate the PolarResultType values to ensure they are valid"
        if not all([r in PolarResultType for r in values]):
            print('invalid op_point_values values')
            return False
            # TODO: create exception
        return True

    def _ensure_not_deleted(self):
        if self.deleted:
            raise AnalysisDoesNotExistError('analysis has been deleted')
    
    def __str__(self):
        pt = self.parameters['polar_type']
        return f'{self._xflr_polar.name} Type:{pt} Analysis'
        # return f'{self._xflr_polar.name} Type:{pt} Analysis, {self.op_point_count} Points'


    # def setDisplayState(self, dsp_state:XDirectDisplayState):
    #     self._client._call("setXDirectDisplay", dsp_state)

    # def getDisplayState(self):
    #     dsp_state_raw = self._client._call("getXDirectDisplay")
    #     return XDirectDisplayState.from_msgpack(dsp_state_raw)


class Analysis2dManager(DictListInterface):
    """
    Analysis2dManager manages the polars for an individual Foil
    Each Foil object has its own Analysis2dManager
    """

    def __init__(self, foil) -> None:
        self._client = Client()
        self.foil = foil

    def _get_items(self) -> dict:
        return self._fetch()

    def _fetch(self):
        polar_list_raw = self._client.call("polarList", self.foil.name)
        return {polar_data['name']: Analysis2d(
            XflrPolar.from_msgpack(polar_data)) for polar_data in polar_list_raw}

    def create(self, name='', polar_type=PolarType.FIXEDLIFTPOLAR, reynolds=10000, re_type=1, ma_type=1,
               aoa=0, mach=0.0, ncrit=9.0, xtop=1.0, xbot=1.0) -> Analysis2d:
        analysis = Analysis2d.create(self.foil.name, name=name, polar_type=polar_type, reynolds=reynolds,
                                     re_type=re_type, ma_type=ma_type, aoa=aoa, mach=mach, ncrit=ncrit, xtop=xtop,
                                     xbot=xbot)
        return analysis


class OpPoint(MsgpackMixin):
    """A raw single point result"""
    alpha = ""
    polar_name = ""
    foil_name = ""
    Cl = 0.0
    XCp = 0.0
    Cd = 0.0
    Cdp = 0.0
    Cm = 0.0
    XTr1 = 0.0
    XTr2 = 0.0
    HMom = 0.0
    Cpmn = 0.0
    Re = 0.0
    mach = 0.0

# class OpPoints():
#     def __init__(self, points):
#         self.points = points
    
#     def __str__(self):
#         return f'OpPoints: {len(self.points)}'
    
#     def __repr__(self):
#         return self.__str__()
    
    

# class OpPointManager:
#     def __init__(self) -> None:
#         self._client = Client()

#     def getOpPoint(self, alpha, polar_name=" ", foil_name=""):
#         opp_raw = self._client.call("getOpPoint", alpha, polar_name, foil_name)
#         return OpPoint.from_msgpack(opp_raw)
