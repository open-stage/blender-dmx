from typing import List, Union, Optional
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
import zipfile
from .value import Matrix, ColorCIE # type: ignore


def _find_root(pkg: "zipfile.ZipFile") -> "ElementTree.Element":
    """Given a GDTF zip archive, find the GeneralSceneDescription of the
    corresponding GeneralSceneDescription.xml file."""

    with pkg.open("GeneralSceneDescription.xml", "r") as f:
        description_str = f.read().decode("utf-8")
        if description_str[-1]=="\x00": # this should not happen, but...
            description_str = description_str[:-1]
    return ElementTree.fromstring(description_str)


class GeneralSceneDescription:
    def __init__(self, path=None):
        if path is not None:
            self._package = zipfile.ZipFile(path, "r")
        if self._package is not None:
            self._root = _find_root(self._package)
            self._user_data = self._root.find("UserData")
            self._scene = self._root.find("Scene")
        if self._root is not None:
            self._read_xml()

    def _read_xml(self):
        self.version_major: str = self._root.get("verMajor", "")
        self.version_minor: str = self._root.get("verMinor", "")
        self.provider: str = self._root.get("provider", "")
        self.providerVersion: str = self._root.get("providerVersion", "")

        layers_collect = self._scene.find("Layers")
        if layers_collect:
            self.layers: List["Layer"] = [Layer(xml_node=i) for i in layers_collect.findall("Layer")]
        else:
            self.layers = []

        aux_data_collect = self._scene.find("AUXData")

        if aux_data_collect:
            self.aux_data = AUXData(xml_node=aux_data_collect)
        else:
            self.aux_data = None

        if self._user_data is not None:
            self.user_data: List["Data"] = [Data(xml_node=i) for i in self._user_data.findall("Data")]


class BaseNode:
    def __init__(self, xml_node: "Element" = None):
        if xml_node is not None:
            self._read_xml(xml_node)

    def _read_xml(self, xml_node: "Element"):
        pass


class BaseChildNode(BaseNode):
    def __init__(
        self,
        name: Union[str, None] = None,
        uuid: Union[str, None] = None,
        gdtf_spec: Union[str, None] = None,
        gdtf_mode: Union[str, None] = None,
        matrix: Matrix = Matrix(0),
        classing: Union[str, None] = None,
        fixture_id: Union[str, None] = None,
        fixture_id_numeric: Union[int, None] = None,
        unit_number: Union[int, None] = None,
        fixture_type_id: int = 0,
        custom_id: int = 0,
        custom_id_type: int = 0,
        cast_shadow: bool = False,
        addresses: List["Address"] = [],
        alignments: List["Alignment"] = [],
        custom_commands: List["CustomCommand"] = [],
        overwrites: List["Overwrite"] = [],
        connections: List["Connection"] = [],
        child_list: Union["ChildList", None] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.uuid = uuid
        self.gdtf_spec = gdtf_spec
        self.gdtf_mode = gdtf_mode
        self.matrix = matrix
        self.classing = classing
        self.fixture_id = fixture_id
        self.fixture_id_numeric = fixture_id_numeric
        self.unit_number = unit_number
        self.fixture_type_id = fixture_type_id
        self.custom_id = custom_id
        self.custom_id_type = custom_id_type
        self.cast_shadow = cast_shadow
        self.addresses = addresses
        self.alignments = alignments
        self.custom_commands = custom_commands
        self.overwrites = overwrites
        self.connections = connections
        self.child_list = child_list
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("name")
        self.uuid = xml_node.attrib.get("uuid")
        _gdtf_spec = xml_node.find("GDTFSpec")
        if _gdtf_spec is not None:
            self.gdtf_spec = _gdtf_spec.text
            if self.gdtf_spec is not None:
                self.gdtf_spec = self.gdtf_spec.encode("utf-8").decode("cp437")
            if self.gdtf_spec is not None and len(self.gdtf_spec) > 5:
                if self.gdtf_spec[-5:].lower() != ".gdtf":
                    self.gdtf_spec = f"{self.gdtf_spec}.gdtf"
        if xml_node.find("GDTFMode") is not None:
            self.gdtf_mode = xml_node.find("GDTFMode").text
        if xml_node.find("Matrix") is not None:
            self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)
        if xml_node.find("FixtureID") is not None:
            self.fixture_id = xml_node.find("FixtureID").text

        if xml_node.find("FixtureIDNumeric"):
            self.fixture_id_numeric = int(xml_node.find("FixtureIDNumeric").text)
        if xml_node.find("UnitNumber") is not None:
            self.unit_number = int(xml_node.find("UnitNumber").text)

        if xml_node.find("FixtureTypeId") is not None:
            self.fixture_type_id = int(xml_node.find("FixtureTypeId").text or 0)

        if xml_node.find("CustomId") is not None:
            self.custom_id = int(xml_node.find("CustomId").text or 0)

        if xml_node.find("CustomIdType") is not None:
            self.custom_id_type = int(xml_node.find("CustomIdType").text or 0)

        if xml_node.find("CastShadow") is not None:
            self.cast_shadow = bool(xml_node.find("CastShadow").text)

        if xml_node.find("Addresses") is not None:
            self.addresses = [Address(xml_node=i) for i in xml_node.find("Addresses").findall("Address")]
        if not len(self.addresses):
            self.addresses = [Address(dmx_break=0, universe=0, address=0)]

        if xml_node.find("Alignments"):
            self.alignments = [Alignment(xml_node=i) for i in xml_node.find("Alignments").findall("Alignment")]
        if xml_node.find("Connections"):
            self.connections = [Connection(xml_node=i) for i in xml_node.find("Connections").findall("Connection")]
        if xml_node.find("CustomCommands"):
            self.custom_commands = [CustomCommand(xml_node=i) for i in xml_node.find("CustomCommands").findall("CustomCommand")]
        if xml_node.find("Overwrites"):
            self.overwrites = [Overwrite(xml_node=i) for i in xml_node.find("Overwrites").findall("Overwrite")]
        if xml_node.find("Classing") is not None:
            self.classing = xml_node.find("Classing").text

        self.child_list = ChildList(xml_node=xml_node.find("ChildList"))

    def __str__(self):
        return f"{self.name}"


class BaseChildNodeExtended(BaseChildNode):
    def __init__(
        self,
        geometries: "Geometries" = None,
        child_list: Union["ChildList", None] = None,
        *args,
        **kwargs,
    ):
        self.geometries = geometries
        self.child_list = child_list
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)
        if xml_node.find("Geometries") is not None:
            self.geometries = Geometries(xml_node=xml_node.find("Geometries"))

        self.child_list = ChildList(xml_node=xml_node.find("ChildList"))

    def __str__(self):
        return f"{self.name}"


class Data(BaseNode):
    def __init__(
        self,
        provider: str = "",
        ver: str = "",
        *args,
        **kwargs,
    ):
        self.provider = provider
        self.ver = ver
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.provider = xml_node.attrib.get("provider")
        self.ver = xml_node.attrib.get("ver")

    def __str__(self):
        return f"{self.provider} {self.ver}"


class AUXData(BaseNode):
    def __init__(
        self,
        classes: List["Class"] = [],
        symdefs: List["Symdef"] = [],
        positions: List["Position"] = [],
        mapping_definitions: List["MappingDefinition"] = [],
        *args,
        **kwargs,
    ):
        self.classes = classes
        self.symdefs = symdefs
        self.positions = positions
        self.mapping_definitions = mapping_definitions
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.classes = [Class(xml_node=i) for i in xml_node.findall("Class")]
        self.symdefs = [Symdef(xml_node=i) for i in xml_node.findall("Symdef")]
        self.positions = [Position(xml_node=i) for i in xml_node.findall("Position")]
        self.mapping_definitions = [MappingDefinition(xml_node=i) for i in xml_node.findall("MappingDefinition")]


class MappingDefinition(BaseNode):
    def __init__(
        self,
        name: Union[str, None] = None,
        uuid: Union[str, None] = None,
        size_x: int = 0,
        size_y: int = 0,
        source=None,
        scale_handling=None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.uuid = uuid
        self.size_x = size_x
        self.size_y = size_y
        self.source = source
        self.scale_handling = scale_handling
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        # TODO handle missing data...
        self.size_x = int(xml_node.find("SizeX").text)
        self.size_y = int(xml_node.find("SizeY").text)
        self.source = xml_node.find("Source")  # TODO
        self.scale_handling = xml_node.find("ScaleHandeling").text  # TODO ENUM


class Fixture(BaseChildNode):
    def __init__(
        self,
        multipatch: Union[str, None] = None,
        focus: Union[str, None] = None,
        color: Union["ColorCIE", None] = ColorCIE(),
        dmx_invert_pan: bool = False,
        dmx_invert_tilt: bool = False,
        position: Union[str, None] = None,
        function_: Union[str, None] = None,
        child_position: Union[str, None] = None,
        protocols: List["Protocol"] = [],
        mappings: List["Mapping"] = [],
        gobo: Union["Gobo", None] = None,
        *args,
        **kwargs,
    ):
        self.multipatch = multipatch
        self.focus = focus
        self.color = color
        self.dmx_invert_pan = dmx_invert_pan
        self.dmx_invert_tilt = dmx_invert_tilt
        self.position = position
        self.function_ = function_
        self.child_position = child_position
        self.protocols = protocols
        self.mappings = mappings
        self.gobo = gobo
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)

        if xml_node.attrib.get("multipatch") is not None:
            self.multipatch = xml_node.attrib.get("multipatch")

        if xml_node.find("Focus") is not None:
            self.focus = xml_node.find("Focus").text

        if xml_node.find("Color") is not None:
            self.color = ColorCIE(str_repr=xml_node.find("Color").text)

        if xml_node.find("DMXInvertPan") is not None:
            self.dmx_invert_pan = bool(xml_node.find("DMXInvertPan").text)

        if xml_node.find("DMXInvertTilt") is not None:
            self.dmx_invert_tilt = bool(xml_node.find("DMXInvertTilt").text)

        if xml_node.find("Position") is not None:
            self.position = xml_node.find("Position").text

        if xml_node.find("Function") is not None:
            self.function_ = xml_node.find("Position").text

        if xml_node.find("ChildPosition") is not None:
            self.child_position = xml_node.find("ChildPosition").text

        if xml_node.find("Protocols"):
            self.protocols = [Protocol(xml_node=i) for i in xml_node.find("Protocols").findall("Protocol")]
        if xml_node.find("Mappings"):
            self.mappings = [Mapping(xml_node=i) for i in xml_node.find("Mappings").findall("Mapping")]
        if xml_node.find("Gobo") is not None:
            self.gobo = Gobo(xml_node.attrib.get("Gobo"))

    def __str__(self):
        return f"{self.name}"


class GroupObject(BaseNode):
    def __init__(
        self,
        name: Union[str, None] = None,
        uuid: Union[str, None] = None,
        classing: Union[str, None] = None,
        child_list: Union["ChildList", None] = None,
        matrix: Matrix = Matrix(0),
        *args,
        **kwargs,
    ):
        self.name = name
        self.uuid = uuid
        self.classing = classing
        self.child_list = child_list
        self.matrix = matrix

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("name")
        self.uuid = xml_node.attrib.get("uuid")
        if xml_node.find("Classing") is not None:
            self.classing = xml_node.find("Classing").text
        self.child_list = ChildList(xml_node=xml_node.find("ChildList"))
        if xml_node.find("Matrix") is not None:
            self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)

    def __str__(self):
        return f"{self.name}"


class ChildList(BaseNode):
    def __init__(
        self,
        scene_objects: List["SceneObject"] = [],
        group_objects: List["GroupObject"] = [],
        focus_points: List["FocusPoint"] = [],
        fixtures: List["Fixture"] = [],
        supports: List["Support"] = [],
        trusses: List["Truss"] = [],
        video_screens: List["VideoScreen"] = [],
        projectors: List["Projector"] = [],
        *args,
        **kwargs,
    ):
        if scene_objects is not None:
            self.scene_objects = scene_objects
        else:
            self.scene_objects = []

        if group_objects is not None:
            self.group_objects = group_objects
        else:
            self.group_objects = []

        if focus_points is not None:
            self.focus_points = focus_points
        else:
            self.focus_points = []

        if fixtures is not None:
            self.fixtures = fixtures
        else:
            self.fixtures = []

        if supports is not None:
            self.supports = supports
        else:
            self.supports = []

        if trusses is not None:
            self.trusses = trusses
        else:
            self.trusses = []

        if video_screens is not None:
            self.video_screens = video_screens
        else:
            self.video_screens = []

        if projectors is not None:
            self.projectors = projectors
        else:
            self.projectors = []

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.scene_objects = [SceneObject(xml_node=i) for i in xml_node.findall("SceneObject")]

        self.group_objects = [GroupObject(xml_node=i) for i in xml_node.findall("GroupObject")]

        self.focus_points = [FocusPoint(xml_node=i) for i in xml_node.findall("FocusPoint")]

        self.fixtures = [Fixture(xml_node=i) for i in xml_node.findall("Fixture")]

        self.supports = [Support(xml_node=i) for i in xml_node.findall("Support")]
        self.trusses = [Truss(xml_node=i) for i in xml_node.findall("Truss")]

        self.video_screens = [VideoScreen(xml_node=i) for i in xml_node.findall("VideoScreen")]

        self.projectors = [Projector(xml_node=i) for i in xml_node.findall("Projector")]


class Layer(BaseNode):
    def __init__(
        self,
        name: str = "",
        uuid: Union[str, None] = None,
        gdtf_spec: Union[str, None] = None,
        gdtf_mode: Union[str, None] = None,
        matrix: Matrix = Matrix(0),
        child_list: Union["ChildList", None] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.uuid = uuid
        self.gdtf_spec = gdtf_spec
        self.gdtf_mode = gdtf_mode
        self.child_list = child_list
        self.matrix = matrix

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("name", "")
        self.uuid = xml_node.attrib.get("uuid")
        _gdtf_spec = xml_node.find("GDTFSpec")
        if _gdtf_spec is not None:
            self.gdtf_spec = _gdtf_spec.text
            if self.gdtf_spec is not None and len(self.gdtf_spec) > 5:
                if self.gdtf_spec[-5:].lower() != ".gdtf":
                    self.gdtf_spec = f"{self.gdtf_spec}.gdtf"
        _gdtf_mode: Optional["Element"] = xml_node.find("GDTFMode")
        if _gdtf_mode is not None:
            self.gdtf_mode = _gdtf_mode.text

        self.child_list = ChildList(xml_node=xml_node.find("ChildList"))
        if xml_node.find("Matrix") is not None:
            self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)

    def __str__(self):
        return f"{self.name}"


class Address(BaseNode):
    def __init__(
        self,
        dmx_break: int = 0,
        universe: int = 1,
        address: Union[int, str] = 1,
        *args,
        **kwargs,
    ):
        self.dmx_break = dmx_break
        self.address = address
        self.universe = universe
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.dmx_break = int(xml_node.attrib.get("break", 0))
        raw_address = xml_node.text or "0"
        if "." in raw_address:
            universe, address = raw_address.split(".")
            self.universe = int(universe)
            self.address = int(address)
            return
        self.universe = 1 + int(raw_address) // 512
        self.address = int(raw_address) % 512

    def __repr__(self):
        return f"B: {self.dmx_break}, U: {self.universe}, A: {self.address}"

    def __str__(self):
        return f"B: {self.dmx_break}, U: {self.universe}, A: {self.address}"


class Class(BaseNode):
    def __init__(
        self,
        uuid: Union[str, None] = None,
        name: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        self.uuid = uuid
        self.name = name
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("name")
        self.uuid = xml_node.attrib.get("uuid")

    def __str__(self):
        return f"{self.name}"


class Position(BaseNode):
    def __init__(
        self,
        uuid: Union[str, None] = None,
        name: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        self.uuid = uuid
        self.name = name
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("name")
        self.uuid = xml_node.attrib.get("uuid")

    def __str__(self):
        return f"{self.name}"


class Symdef(BaseNode):
    def __init__(
        self,
        uuid: Union[str, None] = None,
        name: Union[str, None] = None,
        geometry3d: List["Geometry3D"] = [],
        symbol: List["Symbol"] = [],
        *args,
        **kwargs,
    ):
        self.uuid = uuid
        self.name = name
        self.geometry3d = geometry3d
        self.symbol = symbol
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("name")
        self.uuid = xml_node.attrib.get("uuid")

        self.symbol = [Symbol(xml_node=i) for i in xml_node.findall("Symbol")]
        _geometry3d = [Geometry3D(xml_node=i) for i in xml_node.findall("Geometry3D")]
        if xml_node.find("ChildList"):
            child_list = xml_node.find("ChildList")

            symbols = [Symbol(xml_node=i) for i in child_list.findall("Symbol")]
            geometry3ds = [Geometry3D(xml_node=i) for i in child_list.findall("Geometry3D")]
            self.symbol += symbols
            _geometry3d += geometry3ds

        # sometimes the list of geometry3d is full of duplicates, eliminate them here
        self.geometry3d = list(set(_geometry3d))

class Geometry3D(BaseNode):
    def __init__(
        self,
        file_name: Union[str, None] = None,
        matrix: Matrix = Matrix(0),
        *args,
        **kwargs,
    ):
        self.file_name = file_name
        self.matrix = matrix
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.file_name = xml_node.attrib.get("fileName", "").encode("utf-8").decode("cp437")
        if xml_node.find("Matrix") is not None:
            self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)

    def __str__(self):
        return f"{self.file_name} {self.matrix}"

    def __repr__(self):
        return f"{self.file_name} {self.matrix}"

    def __eq__(self, other):
        return self.file_name == other.file_name and self.matrix == other.matrix

    def __ne__(self, other):
        return self.file_name != other.file_name or self.matrix != other.matrix

    def __hash__(self):
        return hash((self.file_name, str(self.matrix)))


class Symbol(BaseNode):
    def __init__(
        self,
        uuid: Union[str, None] = None,
        symdef: Union[str, None] = None,
        matrix: Matrix = Matrix(0),
        *args,
        **kwargs,
    ):
        self.uuid = uuid
        self.symdef = symdef
        self.matrix = matrix
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.uuid = xml_node.attrib.get("uuid")
        self.symdef = xml_node.attrib.get("symdef")
        if xml_node.find("Matrix") is not None:
            self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)

    def __str__(self):
        return f"{self.uuid}"


class Geometries(BaseNode):
    def __init__(
        self,
        geometry3d: List["Geometry3D"] = [],
        symbol: List["Symbol"] = [],
        *args,
        **kwargs,
    ):
        self.geometry3d = geometry3d
        self.symbol = symbol
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.symbol = [Symbol(xml_node=i) for i in xml_node.findall("Symbol")]
        self.geometry3d = [Geometry3D(xml_node=i) for i in xml_node.findall("Geometry3D")]
        if xml_node.find("ChildList"):
            child_list = xml_node.find("ChildList")

            symbols = [Symbol(xml_node=i) for i in child_list.findall("Symbol")]
            geometry3ds = [Geometry3D(xml_node=i) for i in child_list.findall("Geometry3D")]
            self.symbol += symbols  # TODO remove this over time, children should only be in child_list
            self.geometry3d += geometry3ds


class FocusPoint(BaseNode):
    def __init__(
        self,
        uuid: Union[str, None] = None,
        name: Union[str, None] = None,
        matrix: Matrix = Matrix(0),
        classing: Union[str, None] = None,
        geometries: "Geometries" = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.uuid = uuid
        self.matrix = matrix
        self.classing = classing
        self.geometries = geometries

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.uuid = xml_node.attrib.get("uuid")
        self.name = xml_node.attrib.get("name")
        if xml_node.find("Matrix") is not None:
            self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)
        if xml_node.find("Classing") is not None:
            self.classing = xml_node.find("Classing").text
        if xml_node.find("Geometries") is not None:
            self.geometries = Geometries(xml_node=xml_node.find("Geometries"))

    def __str__(self):
        return f"{self.name}"


class SceneObject(BaseChildNodeExtended):
    pass


class Truss(BaseChildNodeExtended):
    pass


class Support(BaseChildNodeExtended):
    def __init__(
        self,
        chain_length: float = 0,
        *args,
        **kwargs,
    ):
        self.chain_length = chain_length
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        if xml_node.find("ChainLength") is None:
            self.chain_length = float(xml_node.find("ChainLength").text or 0)


class VideoScreen(BaseChildNodeExtended):
    def __init__(
        self,
        sources: "Sources" = None,
        *args,
        **kwargs,
    ):
        self.sources = sources
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        if xml_node.find("Sources") is None:
            self.sources = Sources(xml_node=xml_node.find("Sources"))


class Projector(BaseChildNodeExtended):
    def __init__(
        self,
        projections: "Projections" = None,
        *args,
        **kwargs,
    ):
        self.projections = projections
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        if xml_node.find("Projections") is None:
            self.projections = Projections(xml_node.find("Projections"))


class Protocol(BaseNode):
    def __init__(
        self,
        geometry: Union[str, None] = None,
        name: Union[str, None] = None,
        type_: Union[str, None] = None,
        version: Union[str, None] = None,
        transmission: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        self.geometry = geometry
        self.name = name
        self.type = type_
        self.version = version
        self.transmission = transmission
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.geometry = xml_node.attrib.get("geometry")
        self.name = xml_node.attrib.get("name")
        self.type = xml_node.attrib.get("type")
        self.version = xml_node.attrib.get("version")
        self.transmission = xml_node.attrib.get("transmission")

    def __str__(self):
        return f"{self.name}"


class Alignment(BaseNode):
    def __init__(
        self,
        geometry: Union[str, None] = None,
        up: Union[str, None] = "0,0,1",
        direction: Union[str, None] = "0,0,-1",
        *args,
        **kwargs,
    ):
        self.geometry = geometry
        self.up = up
        self.direction = direction
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.geometry = xml_node.attrib.get("geometry")
        self.up = xml_node.attrib.get("up", "0,0,1")
        self.direction = xml_node.attrib.get("direction", "0,0,-1")

    def __str__(self):
        return f"{self.geometry}"


class Overwrite(BaseNode):
    def __init__(
        self,
        universal: Union[str, None] = None,
        target: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        self.universal = universal
        self.target = target
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.universal = xml_node.attrib.get("universal")
        self.target = xml_node.attrib.get("target")

    def __str__(self):
        return f"{self.universal} {self.target}"


class Connection(BaseNode):
    def __init__(
        self,
        own: Union[str, None] = None,
        other: Union[str, None] = None,
        to_object: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        self.own = own
        self.other = other
        self.to_object = to_object
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.own = xml_node.attrib.get("own")
        self.other = xml_node.attrib.get("other")
        self.to_object = xml_node.attrib.get("toObject")

    def __str__(self):
        return f"{self.own} {self.other}"


class Mapping(BaseNode):
    def __init__(
        self,
        link_def: Union[str, None] = None,
        ux: Union[int, None] = None,
        uy: Union[int, None] = None,
        ox: Union[int, None] = None,
        oy: Union[int, None] = None,
        rz: Union[int, None] = None,
        *args,
        **kwargs,
    ):
        self.link_def = link_def
        self.ux = ux
        self.uy = uy
        self.ox = ox
        self.oy = oy
        self.rz = rz
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.link_def = xml_node.attrib.get("linkedDef")
        self.ux = int(xml_node.find("ux").text)
        self.uy = int(xml_node.find("uy").text)
        self.ox = int(xml_node.find("ox").text)
        self.oy = int(xml_node.find("oy").text)
        self.rz = int(xml_node.find("rz").text)

    def __str__(self):
        return f"{self.link_def}"


class Gobo(BaseNode):
    def __init__(
        self,
        rotation: Union[str, float, None] = None,
        filename: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        self.rotation = rotation
        self.filename = filename
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.rotation = float(xml_node.attrib.get("rotation", 0))
        self.filename = xml_node.text

    def __str__(self):
        return f"{self.filename} {self.rotation}"


class CustomCommand(BaseNode):
    # TODO: split more: <CustomCommand>Body_Pan,f 50</CustomCommand>
    def __init__(
        self,
        custom_command: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        self.custom_command = custom_command
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.custom_command = xml_node.text

    def __str__(self):
        return f"{self.custom_command}"


class Projections(BaseNode):
    ...
    # todo


class Sources(BaseNode):
    def __init__(
        self,
        linked_geometry: Union[str, None] = None,
        type_: Union[str, None] = None,
        *args,
        **kwargs,
    ):
        self.linked_geometry = linked_geometry
        self.type_ = type_
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.linked_geometry = xml_node.attrib.get("linkedGeometry")
        self.type_ = xml_node.attrib.get("type")

    def __str__(self):
        return f"{self.linked_geometry} {self.type_}"
