from xflrpy.mixins import MsgpackMixin, DictListInterface
from xflrpy.polar2d import PolarType, Analysis2dManager, BatchAnalysisSettings2D
from xflrpy.module import ModuleType
from xflrpy import Client
from xflrpy.exceptions import InvalidFoilPathError, InvalidNacaValueError
import os

import enum


class StippleType(enum.IntEnum):
    SOLID = 0
    DASH = 1
    DOT = 2
    DASHDOT = 3
    DASHDOTDOT = 4
    NOLINE = 5


class PointStyle(enum.IntEnum):
    NOSYMBOL = 0
    LITTLECIRCLE = 1
    BIGCIRCLE = 2
    LITTLESQUARE = 3
    BIGSQUARE = 4
    TRIANGLE = 5
    TRIANGLE_INV = 6
    LITTLECIRCLE_F = 7
    BIGCIRCLE_F = 8
    LITTLESQUARE_F = 9
    BIGSQUARE_F = 10
    TRIANGLE_F = 11
    TRIANGLE_INV_F = 12
    LITTLECROSS = 13
    BIGCROSS = 14


class LineStyle(MsgpackMixin):
    visible = True
    stipple = StippleType.SOLID
    point_style = PointStyle.NOSYMBOL
    width = 1
    color = []
    tag = ""

    def __init__(self, visible=True, stipple=StippleType.SOLID, point_style=PointStyle.NOSYMBOL, width=1, color=[], tag="") -> None:
        self.visible = visible
        self.stipple = stipple
        self.point_style = point_style
        self.width = width
        self.color = color
        self.tag = tag


class Foil(MsgpackMixin):
    name = ""   # Name of the airfoil
    camber = 0.0   # Maximum camber range(0,1)
    camber_x = 0.0  # Location of maximum camber
    thickness = 0.0  # Maximum thickness
    thickness_x = 0.0
    n = 0

    def __init__(self) -> None:
        self._client = Client()
        self.analyses = Analysis2dManager(self)

    def rename(self, name):
        self._client.call("renameFoil", self.name, name)
        self.name = name

    def duplicate(self, name):
        foil_raw = self._client.call("duplicateFoil", self.name, name)
        return self.from_msgpack(foil_raw)

    def delete(self) -> None:
        self._client.call("deleteFoil", self.name)

    def set_coordinates(self, xy: list, update_gui=True):
        self._client.call("setFoilCoords", self.name, xy, update_gui)
        self._update()

    def set_geometry(self, camber=0., camber_x=0., thickness=0., thickness_x=0.):
        self._client.call("setGeom", self.name, camber,
                          camber_x, thickness, thickness_x)
        self._update()

    def normalize(self):
        self._client.call("normalizeFoil", self.name)
        self._update()

    def derotate(self):
        self._client.call("derotateFoil", self.name)
        self._update()

    def export(self, file_name):
        """
        name: name of the airfoil to export
        file_name: full path of the to be saved airfoil 
        """
        self._client.call("exportFoil", self.name, file_name)

    def to_dat(self, newline="\n"):
        text = self.name + newline
        for c in self.coordinates:
            text += f'  {c[0]:.6f}  {c[1]:.6f}{newline}'
        return text

    @property
    def coordinates(self) -> list:
        return self._client.call("getFoilCoords", self.name)

    def _update(self):
        foil_raw = self._client.call("getFoil", self.name)
        self.__dict__.update(foil_raw)

    def _compare_coordinates_set(self, other_foil):
        if len(self.coordinates) != len(other_foil):
            return False
        for i in range(len(self.coordinates)):
            if self.coordinates[i] != other_foil[i]:
                return False
        return True

    # GUI
    def select(self, set_current=False, select_in_gui=False):
        if set_current:
            self._client.call("setCurFoil", self.name, select_in_gui)

    @property
    def is_visible(self):
        return self.style.visible

    def show(self):
        self._set_visibility()

    def hide(self):
        self._set_visibility(False)

    def _set_visibility(self, is_visible=True):
        self._client.call("showFoil", self.name, is_visible)

    @property
    def style(self):
        line_style_raw = self._client.call("getLineStyle", self.name)
        line_style = LineStyle.from_msgpack(line_style_raw)
        line_style.point_style = PointStyle(line_style.point_style)
        line_style.stipple = StippleType(line_style.stipple)
        return line_style

    def set_style(self, line_style: LineStyle):
        line_style.stipple = line_style.stipple.value
        line_style.point_style = line_style.point_style.value
        self._client.call("setLineStyle", self.name, line_style.to_msgpack())

    def __str__(self):
        return f'<Foil {self.name}, {self.n} coordinates>'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other_foil):
        params_check = (
            self.camber == other_foil.camber and
            self.camber_x == other_foil.camber_x and
            self.thickness == other_foil.thickness and
            self.thickness_x == other_foil.thickness_x and
            self.n == other_foil.n
        )
        coords_check = self._compare_coordinates_set(other_foil.coordinates)
        return params_check and coords_check


class FoilManager(DictListInterface):
    """
    Foil Manager holds the Foil objects and is responsible for actions with the foil objects, including creating, 
    loading, deleting, etc.  It can also be used to minimally interact with the GUI.

    """

    def __init__(self) -> None:
        self._client = Client()

    def load(self, paths):
        """
        Loads .dat airfoil files on the remote XFLR5-RPC server.

        Args:
            paths (str or str[]): a path or array of absolute paths to load on the XFLR-RPC server.
        Returns:
            None
        Raises:
            InvalidFoilPathException: if a single path is invalid and will prevent any files from being loaded.
        """
        self._set_client_module(ModuleType.DIRECTFOILDESIGN)
        if type(paths) == str:
            paths = [paths]
        for path in paths:
            if path[-4:].lower() != ".dat":
                raise InvalidFoilPathError(
                    f'Please provide a valid .dat file. "{path}" is invalid.')
        validation_result = self._validate_file_paths(paths)
        for i, path in enumerate(paths):
            if validation_result[i] == False:
                raise InvalidFoilPathError(
                    f'Please provide a valid file path. "{path}" is does not exist.')
        for path in paths:
            self._client.call("loadProject", [path])

    def load_folder(self, path):
        """
        Loads all .dat airfoil files contained within a specified folder on the remote XFLR5-RPC server.

        Args:
            path (str): an absolute path to a folder on the XFLR-RPC server from which to load .dat files.
        Returns:
            None
        """
        self._client.modules.set(ModuleType.DIRECTFOILDESIGN)
        files = [f for f in os.listdir(
            path) if os.path.isfile(os.path.join(path, f))]
        loaded = []
        for file in files:
            try:
                self.load(os.path.join(path, file))
            except InvalidFoilPathError:
                continue
            loaded.append(file)

    def delete_all(self):
        "Deletes all foils on the server"
        [f.delete() for _, f in self.to_dict().items()]

    def create_naca_foil(self, digits, name=None):
        """
        Creates a new foil on the server based on the NACA value (https://en.wikipedia.org/wiki/NACA_airfoil).

        THIS WILL OVERWRITE AN EXISTING FOIL WITH THE SAME NAME!

        Args:
            digits (int or str): a 1-4 digit value specifying the naca foil parameters.
            name (str): optional.  Specifies a name for the new foil.  Default is "NACA {digits}".
        Returns:
            Foil: newly created NACA foil
        Raises:
            InvalidNacaValueError: on invalid digits value
        """
        self._set_client_module(ModuleType.DIRECTFOILDESIGN)
        try:
            digits = int(digits)
        except:
            raise InvalidNacaValueError(
                "ERROR - NACA foil value must be positive, 4 digit value")
        if not (digits > 0 and digits <= 9999):
            raise InvalidNacaValueError(
                "ERROR - NACA foil value must be positive, 4 digit value")
        if not name:
            name = "NACA " + str(digits).zfill(4)
        self._client.call("createNACAFoil", digits, name)
        return self.get(name)

    def _validate_file_paths(self, paths) -> list:
        response = self._client.call("validateFilePaths", paths)
        return [r[0] for r in response]

    def get(self, name=None):
        """
        Retrieves a single Foil by name from the server.

        Returns:
            Foil
        Raises:
            KeyError: on invalid name
        """
        if name not in [k for k, v in self.to_dict().items()]:
            raise KeyError(f'Key "{name}" does not exist')
        return Foil.from_msgpack(self._client.call("getFoil", name))

    def _get_items(self) -> dict:
        return {item["name"]: Foil.from_msgpack(item) for item in self._client.call("foilList")}

    def run_batch_analysis(self, re_list, foil_list=None, polar_type=PolarType.FIXEDLIFTPOLAR, mach=0, ncrit=9, transition_top=1, 
                           transition_bot=1, range_type_alpha=True, sequence=(-15, 15, 0.25), from_zero=True, 
                           init_bl=True, store_op_point=False, update_polar_view=False, thread_count=0):
        
        params = BatchAnalysisSettings2D()

        # if no foils have been defined analyze all
        if foil_list == None:
            foil_list = self.to_list()
        
        # foil list can be list of foil names or foil objects.
        foil_names_list = []
        for foil in foil_list:
            if type(foil) == Foil:
                foil_names_list.append(foil.name)
            else:
                foil_names_list.append(foil)

        params.foil_names = foil_names_list
        params.re_list = re_list
        params.mach = mach
        params.ncrit = ncrit
        params.polar_type = polar_type
        params.transition_top = transition_top
        params.transition_bot = transition_bot
        params.range_type_alpha = range_type_alpha
        params.min = sequence[0]
        params.max = sequence[1]
        params.increment = sequence[2]
        params.from_zero = from_zero
        params.init_bl = init_bl
        params.store_op_point = store_op_point
        params.update_polar_view = update_polar_view
        params.thread_count = thread_count

        self._client.call("batchAnalyze", params.to_msgpack())

    # GUI RELATED FUNCTIONALITY

    def hide_all(self):
        """
        Hides all foils in the server GUI.  Delegates to each individual foil to handle its visibility

        Returns:
            None
        """
        [f.hide() for _, f in self.to_dict().items()]

    def show_all(self):
        """
        Shows all foils in the server GUI.  Delegates to each individual foil to handle its visibility

        Returns:
            None
        """
        [f.show() for _, f in self.to_dict().items()]

    def _set_client_module(self, module):
        self._client.modules.set(module)
