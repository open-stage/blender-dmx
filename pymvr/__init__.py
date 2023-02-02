from typing import List
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
import zipfile
from dmx.pymvr.value import *


def _find_root(pkg: "zipfile.ZipFile") -> "ElementTree.Element":
    """Given a GDTF zip archive, find the FixtureType of the corresponding
    description.xml file."""

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
        name: str = None,
        uuid: str = None,
        gdtf_spec: str = None,
        gdtf_mode: str = None,
        matrix: Matrix = Matrix(0),
        fixture_id: str = None,
        unit_number: str = None,
        fixture_type_id: int = 0,
        custom_id: int = 0,
        color: "ColorCIE" = None,
        cast_shadow: bool = False,
        addresses: List["Address"] = None,
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
        self.gdtf_spec = xml_node.find("GDTFSpec").text
        self.gdtf_mode = xml_node.find("GDTFMode").text
        self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)
        self.fixture_id = xml_node.find("FixtureID").text
        self.unit_number = xml_node.find("UnitNumber").text
        self.fixture_type_id = xml_node.find("FixtureTypeId").text
        self.custom_id = xml_node.find("CustomId").text
        self.color = xml_node.find("Color").text
        self.cast_shadow = xml_node.find("CastShadow").text
        self.addresses = [
            Address(xml_node=i) for i in xml_node.find("Addresses").findall("Address")
        ]


class Layer(BaseNode):
    def __init__(
        self,
        name: str = None,
        uuid: str = None,
        gdtf_spec: str = None,
        gdtf_mode: str = None,
        fixtures: List["Fixture"] = None,
        matrix: Matrix = Matrix(0),
        *args,
        **kwargs,
    ):
        self.name = name
        self.uuid = uuid
        self.gdtf_spec = gdtf_spec
        self.gdtf_mode = gdtf_mode

        if fixtures is not None:
            self.fixtures = fixtures
        else:
            self.fixtures = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("name")
        self.uuid = xml_node.attrib.get("uuid")
        self.gdtf_spec = xml_node.find("GDTFSpec").text
        self.gdtf_mode = xml_node.find("GDTFMode").text
        self.fixtures = [
            Fixture(xml_node=i) for i in xml_node.find("ChildList").findall("Fixture")
        ]
        if xml_node.find("Matrix"):
            self.matrix = Matrix(str_repr=xml_node.find("Matrix").text)


class Address(BaseNode):
    def __init__(
        self, dmx_break: int = 0, universe: int = 1, address: int = 1, *args, **kwargs
    ):
        self.dmx_break = dmx_break
        self.address = address
        self.universe = universe

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.dmx_break = int(xml_node.attrib.get("break"))
        raw_address = xml_node.text
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
