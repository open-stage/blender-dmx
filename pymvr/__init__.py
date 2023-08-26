from typing import List, Union, Optional
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
import zipfile
from dmx.pymvr.value import *


def _find_root(pkg: "zipfile.ZipFile") -> "ElementTree.Element":
    """Given a GDTF zip archive, find the GeneralSceneDescription of the
    corresponding GeneralSceneDescription.xml file."""

    with pkg.open("GeneralSceneDescription.xml", "r") as f:
        description_str = f.read()
    return ElementTree.fromstring(description_str)


class GeneralSceneDescription:
    def __init__(self, path=None):
        self._package = None
        self._root = None
        if path is not None:
            self._package = zipfile.ZipFile(path, "r")
        if self._package is not None:
            self._root = _find_root(self._package)
            self._user_data = self._root.find("UserData")
            self._scene = self._root.find("Scene")
        if self._root is not None:
            self._read_xml()

    def _read_xml(self):
        self.version_major = self._root.get("verMajor")
        self.version_minor = self._root.get("verMinor")

        layers_collect = self._scene.find("Layers")
        if layers_collect:
            self.layers = [Layer(xml_node=i) for i in layers_collect.findall("Layer")]
        else:
            self.layers = []


class BaseNode:
    def __init__(self, xml_node: "Element" = None):
        if xml_node is not None:
            self._read_xml(xml_node)

    def _read_xml(self, xml_node: "Element"):
        pass


class Fixture(BaseNode):
    def __init__(
        self,
        name: Union[str, None] = None,
        uuid: Union[str, None] = None,
        gdtf_spec: Union[str, None] = None,
        gdtf_mode: Union[str, None] = None,
        matrix: Matrix = Matrix(0),
        fixture_id: Union[str, None] = None,
        unit_number: Union[str, None] = None,
        fixture_type_id: int = 0,
        custom_id: int = 0,
        color: Union["ColorCIE", None] = None,
        cast_shadow: bool = False,
        addresses: List["Address"] = [],
        *args,
        **kwargs,
    ):
        self.name = name
        self.uuid = uuid
        self.gdtf_spec = gdtf_spec
        self.gdtf_mode = gdtf_mode
        self.matrix = matrix
        self.fixture_id = fixture_id
        self.unit_number = unit_number
        self.fixture_type_id = fixture_type_id
        self.custom_id = custom_id
        self.color = color
        self.cast_shadow = cast_shadow
        self.addresses = addresses

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("name")
        self.uuid = xml_node.attrib.get("uuid")
        _gdtf_spec = xml_node.find("GDTFSpec")
        if _gdtf_spec is not None:
            self.gdtf_spec = _gdtf_spec.text
            if self.gdtf_spec is not None and len(self.gdtf_spec) > 5:
                if self.gdtf_spec[-5:].lower() != ".gdtf":
                    self.gdtf_spec = f"{self.gdtf_spec}.gdtf"
        _gdtf_mode = xml_node.find("GDTFMode")
        if _gdtf_mode is not None:
            self.gdtf_mode = _gdtf_mode.text
        self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)
        self.fixture_id = xml_node.find("FixtureID").text
        self.unit_number = xml_node.find("UnitNumber").text
        fixture_type_id_node = xml_node.find("FixtureTypeId")
        if fixture_type_id_node:
            self.fixture_type_id = int(fixture_type_id_node.text or 0)
        custom_id_node = xml_node.find("CustomId")
        if custom_id_node:
            self.custom_id = int(custom_id_node.text or 0)
        color_node = xml_node.find("Color")
        if color_node:
            self.color = ColorCIE(str_repr=color_node.text)

        cast_shadow_node = xml_node.find("CastShadow")
        if cast_shadow_node:
            self.cast_shadow = bool(cast_shadow_node.text)
        self.addresses = [
            Address(xml_node=i) for i in xml_node.find("Addresses").findall("Address")
        ]

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
        if _classing := xml_node.find("Classing"):
            self.classing = _classing.text

        self.child_list = ChildList(xml_node=xml_node.find("ChildList"))
        if xml_node.find("Matrix"):
            self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)

    def __str__(self):
        return f"{self.name}"


class ChildList(BaseNode):
    def __init__(
        self,
        fixtures: List["Fixture"] = [],
        group_object: Union["GroupObject", None] = None,
        *args,
        **kwargs,
    ):
        if fixtures is not None:
            self.fixtures = fixtures
        else:
            self.fixtures = []
        self.group_object = group_object
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.fixtures = [Fixture(xml_node=i) for i in xml_node.findall("Fixture")]
        self.group_object = GroupObject(xml_node=xml_node.find("GroupObject"))


class Layer(BaseNode):
    def __init__(
        self,
        name: Union[str, None] = None,
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
        self.name = xml_node.attrib.get("name")
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
        if xml_node.find("Matrix"):
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
