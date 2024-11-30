import datetime
import zipfile
from enum import Enum as pyEnum
from typing import List, Optional, Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .utils import *
from .value import *  # type: ignore

__version__ = "1.0.5.dev7"

# Standard predefined colour spaces: R, G, B, W-P
COLOR_SPACE_SRGB = ColorSpaceDefinition(
    ColorCIE(0.6400, 0.3300, 0.2126),
    ColorCIE(0.3000, 0.6000, 0.7152),
    ColorCIE(0.1500, 0.0600, 0.0722),
    ColorCIE(0.3127, 0.3290, 1.0000),
)
COLOR_SPACE_PROPHOTO = ColorSpaceDefinition(
    ColorCIE(0.7347, 0.2653),
    ColorCIE(0.1596, 0.8404),
    ColorCIE(0.0366, 0.0001),
    ColorCIE(0.3457, 0.3585),
)
COLOR_SPACE_ANSI = ColorSpaceDefinition(
    ColorCIE(0.7347, 0.2653),
    ColorCIE(0.1596, 0.8404),
    ColorCIE(0.0366, 0.001),
    ColorCIE(0.4254, 0.4044),
)


def _find_root(pkg: "zipfile.ZipFile") -> "ElementTree.Element":
    """Given a GDTF zip archive, find the FixtureType of the corresponding
    description.xml file."""

    with pkg.open("description.xml", "r") as f:
        description_str = f.read().decode("utf-8")
        if description_str[-1] == "\x00":  # this should not happen, but...
            description_str = description_str[:-1]
    return ElementTree.fromstring(description_str)


class FixtureType:
    def __init__(self, path=None, dsc_file: Optional[str] = None):
        self._package = None
        self._root = None
        if path is not None:
            self._package = zipfile.ZipFile(path, "r")
        if self._package is not None:
            self._gdtf = _find_root(self._package)
            self._root = self._gdtf.find("FixtureType")
        elif dsc_file is not None:
            self._gdtf = ElementTree.parse(dsc_file).getroot()
            self._root = self._gdtf.find("FixtureType")
        if self._root is not None:
            self._read_xml()

    def _read_xml(self):
        self.data_version = self._gdtf.get("DataVersion", 1.2)
        self.name = self._root.get("Name")
        self.short_name = self._root.get("ShortName")
        self.long_name = self._root.get("LongName")
        self.manufacturer = self._root.get("Manufacturer")
        self.description = self._root.get("Description")
        self.fixture_type_id = self._root.get("FixtureTypeID")
        self.thumbnail = self._root.get("Thumbnail", "").encode("utf-8").decode("cp437")
        self.thumbnails = Thumbnails(xml_node=self._root, fixture_type=self)
        self.ref_ft = self._root.get("RefFT")
        # For each attribute, we first check for the existence of the collect node
        # If such a node doesn't exist, then none of the children will exist and
        # the corresponding attribute for this class can be set to empty. Failing
        # to do this would result in AttributeError if we try to, for example, run
        # a findall on a non-existent collect
        if activation_collect := self._root.find("AttributeDefinitions").find(
            "ActivationGroups"
        ):
            self.activation_groups = [
                ActivationGroup(xml_node=i)
                for i in activation_collect.findall("ActivationGroup")
            ]
        else:
            self.activation_groups = []
        if feature_collect := self._root.find("AttributeDefinitions").find(
            "FeatureGroups"
        ):
            self.feature_groups = [
                FeatureGroup(xml_node=i)
                for i in feature_collect.findall("FeatureGroup")
            ]
        else:
            self.feature_groups = []
        if attribute_collect := self._root.find("AttributeDefinitions").find(
            "Attributes"
        ):
            self.attributes = [
                Attribute(xml_node=i) for i in attribute_collect.findall("Attribute")
            ]
        else:
            self.attributes = []
        if wheel_collect := self._root.find("Wheels"):
            self.wheels = [Wheel(xml_node=i) for i in wheel_collect.findall("Wheel")]
        else:
            self.wheels = []

        physical_descriptions_node = self._root.find("PhysicalDescriptions")

        if physical_descriptions_node:
            if emitter_collect := self._root.find("PhysicalDescriptions").find(
                "Emitters"
            ):
                self.emitters = [
                    Emitter(xml_node=i) for i in emitter_collect.findall("Emitter")
                ]
            else:
                self.emitters = []

        if physical_descriptions_node:
            if filter_collect := self._root.find("PhysicalDescriptions").find(
                "Filters"
            ):
                self.filters = [
                    Filter(xml_node=i) for i in filter_collect.findall("Filter")
                ]
            else:
                self.filters = []

        if physical_descriptions_node:
            if color_space := self._root.find("PhysicalDescriptions").find(
                "ColorSpace"
            ):
                self.color_space = ColorSpace(xml_node=color_space)
            else:
                # The default color space is sRGB if nothing else is defined
                self.color_space = ColorSpace(mode=ColorSpaceMode("sRGB"))

        if physical_descriptions_node:
            if profiles_collect := self._root.find("PhysicalDescriptions").find(
                "DMXProfiles"
            ):
                self.dmx_profiles = [
                    DmxProfile(xml_node=i)
                    for i in profiles_collect.findall("DMXProfile")
                ]
            else:
                self.dmx_profiles = []

        if physical_descriptions_node:
            if cri_collect := self._root.find("PhysicalDescriptions").find("CRIs"):
                self.cri_groups = [
                    CriGroup(xml_node=i) for i in cri_collect.findall("CRIGroup")
                ]
            else:
                self.cri_groups = []

        if physical_descriptions_node:
            if properties := self._root.find("PhysicalDescriptions").find("Properties"):
                self.properties = Properties(xml_node=properties)
            else:
                self.properties: Properties = Properties()

        self.models = []
        if model_collect := self._root.find("Models"):
            self.models = [Model(xml_node=i) for i in model_collect.findall("Model")]
        for model in self.models:
            if self._package is not None:
                if f"models/gltf/{model.file.name}.glb" in self._package.namelist():
                    model.file.extension = "glb"
                    model.file.crc = self._package.getinfo(
                        f"models/gltf/{model.file.name}.glb"
                    ).CRC
                elif f"models/3ds/{model.file.name}.3ds" in self._package.namelist():
                    model.file.extension = "3ds"
                    model.file.crc = self._package.getinfo(
                        f"models/3ds/{model.file.name}.3ds"
                    ).CRC

        self.geometries = []
        if geometry_collect := self._root.find("Geometries"):
            for i in geometry_collect.findall("Geometry"):
                self.geometries.append(Geometry(xml_node=i))
            for i in geometry_collect.findall("Axis"):
                self.geometries.append(GeometryAxis(xml_node=i))
            for i in geometry_collect.findall("FilterBeam"):
                self.geometries.append(GeometryFilterBeam(xml_node=i))
            for i in geometry_collect.findall("FilterColor"):
                self.geometries.append(GeometryFilterColor(xml_node=i))
            for i in geometry_collect.findall("FilterGobo"):
                self.geometries.append(GeometryFilterGobo(xml_node=i))
            for i in geometry_collect.findall("FilterShaper"):
                self.geometries.append(GeometryFilterShaper(xml_node=i))
            for i in geometry_collect.findall("MediaServerMaster"):
                self.geometries.append(GeometryMediaServerMaster(xml_node=i))
            for i in geometry_collect.findall("MediaServerLayer"):
                self.geometries.append(GeometryMediaServerLayer(xml_node=i))
            for i in geometry_collect.findall("MediaServerCamera"):
                self.geometries.append(GeometryMediaServerCamera(xml_node=i))
            for i in geometry_collect.findall("Inventory"):
                self.geometries.append(GeometryInventory(xml_node=i))
            for i in geometry_collect.findall("Beam"):
                self.geometries.append(GeometryBeam(xml_node=i))
            for i in geometry_collect.findall("WiringObject"):
                self.geometries.append(GeometryWiringObject(xml_node=i))
            for i in geometry_collect.findall("GeometryReference"):
                self.geometries.append(GeometryReference(xml_node=i))
            for i in geometry_collect.findall("Laser"):
                self.geometries.append(GeometryLaser(xml_node=i))
            for i in geometry_collect.findall("Support"):
                self.geometries.append(GeometrySupport(xml_node=i))
            for i in geometry_collect.findall("Structure"):
                self.geometries.append(GeometryStructure(xml_node=i))
            for i in geometry_collect.findall("Display"):
                self.geometries.append(GeometryDisplay(xml_node=i))
            for i in geometry_collect.findall("Magnet"):
                self.geometries.append(GeometryMagnet(xml_node=i))
        if dmx_mode_collect := self._root.find("DMXModes"):
            self.dmx_modes = [
                DmxMode(xml_node=i) for i in dmx_mode_collect.findall("DMXMode")
            ]
        else:
            self.dmx_modes = []

        if not self.dmx_modes:
            self.dmx_modes.append(DmxMode(name="Default"))

        # in GDTF < 1.2, there was no link from DMX Mode to Geometry root, do this manually
        for mode in self.dmx_modes:
            if mode.geometry is None:
                if self.geometries:
                    mode.geometry = self.geometries[0].name

        if revision_collect := self._root.find("Revisions"):
            self.revisions = [
                Revision(xml_node=i) for i in revision_collect.findall("Revision")
            ]
        else:
            self.revisions = []

        self.protocols = []
        if protocols_collect := self._root.find("Protocols"):
            for i in protocols_collect.findall("FTRDM"):
                self.protocols.append(Rdm(xml_node=i))
            for i in protocols_collect.findall("Art-Net"):
                self.protocols.append(ArtNet(xml_node=i))
            for i in protocols_collect.findall("sACN"):
                self.protocols.append(Sacn(xml_node=i))
            for i in protocols_collect.findall("PosiStageNet"):
                self.protocols.append(PosiStageNet(xml_node=i))
            for i in protocols_collect.findall("OpenSoundControl"):
                self.protocols.append(OpenSoundControl(xml_node=i))
            for i in protocols_collect.findall("CITP"):
                self.protocols.append(Citp(xml_node=i))


class BaseNode:
    def __init__(self, xml_node: Optional["Element"] = None):
        if xml_node is not None:
            self._read_xml(xml_node)

    def _read_xml(self, xml_node: "Element"):
        pass


class Thumbnails(BaseNode):
    def __init__(
        self,
        png: Optional["Resource"] = None,
        svg: Optional["Resource"] = None,
        fixture_type: Optional["FixtureType"] = None,
        *args,
        **kwargs,
    ):
        self.png = png
        self.svg = svg
        self.fixture_type = fixture_type
        super().__init__(*args, **kwargs)

        if self.fixture_type is not None and self.fixture_type._package is not None:
            if (
                self.png is not None
                and f"{self.png.name}.png" in self.fixture_type._package.namelist()
            ):
                self.png.extension = "png"
                self.png.crc = self.fixture_type._package.getinfo(
                    f"{self.png.name}.png"
                ).CRC
            else:
                self.png = None

            if (
                self.svg is not None
                and f"{self.svg.name}.svg" in self.fixture_type._package.namelist()
            ):
                self.svg.extension = "svg"
                self.svg.crc = self.fixture_type._package.getinfo(
                    f"{self.svg.name}.svg"
                ).CRC
            else:
                self.svg = None

    def _read_xml(self, xml_node: "Element"):
        name = xml_node.attrib.get("Thumbnail", "")
        self.png = Resource(name=name)
        self.svg = Resource(name=name)


class ActivationGroup(BaseNode):
    def __init__(self, name: Optional[str] = None, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")


class FeatureGroup(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        pretty: Optional[str] = None,
        features: Optional[List["Feature"]] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.pretty = pretty
        if features is not None:
            self.features = features
        else:
            self.features = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.pretty = xml_node.attrib.get("Pretty")
        self.features = [Feature(xml_node=i) for i in xml_node.findall("Feature")]


class Feature(BaseNode):
    def __init__(self, name: Optional[str] = None, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")


class Attribute(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        pretty: Optional[str] = None,
        activation_group: Optional["NodeLink"] = None,
        feature: Optional["NodeLink"] = None,
        main_attribute: Optional["NodeLink"] = None,
        physical_unit: "PhysicalUnit" = PhysicalUnit(None),
        color: Optional["ColorCIE"] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.pretty = pretty
        self.activation_group = activation_group
        self.feature = feature
        self.main_attribute = main_attribute
        self.physical_unit = physical_unit
        self.color = color
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.pretty = xml_node.attrib.get("Pretty")
        self.activation_group = NodeLink(
            "ActivationGroups", xml_node.attrib.get("ActivationGroup")
        )
        self.feature = NodeLink("FeatureGroups", xml_node.attrib.get("Feature"))
        self.main_attribute = NodeLink(
            "Attribute", xml_node.attrib.get("MainAttribute")
        )
        self.physical_unit = PhysicalUnit(xml_node.attrib.get("PhysicalUnit"))
        self.color = ColorCIE(str_repr=xml_node.attrib.get("Color"))


class Wheel(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        wheel_slots: Optional[List["WheelSlot"]] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        if wheel_slots is not None:
            self.wheel_slots = wheel_slots
        else:
            self.wheel_slots = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.wheel_slots = [WheelSlot(xml_node=i) for i in xml_node.findall("Slot")]


class WheelSlot(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        color: Optional["ColorCIE"] = None,
        whl_filter: Optional["NodeLink"] = None,
        media_file_name: Optional["Resource"] = None,
        facets: Optional[List["PrismFacet"]] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.color = color
        self.filter = whl_filter
        self.media_file_name = media_file_name
        if facets is not None:
            self.facets = facets
        else:
            self.facets = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.color = ColorCIE(str_repr=xml_node.attrib.get("Color"))
        self.filter = NodeLink("FilterCollect", xml_node.attrib.get("Filter"))
        self.media_file_name = Resource(xml_node.attrib.get("MediaFileName", ""), "png")
        self.facets = [PrismFacet(xml_node=i) for i in xml_node.findall("Facet")]


class PrismFacet(BaseNode):
    def __init__(
        self,
        color: Optional["ColorCIE"] = None,
        rotation: Optional["Rotation"] = None,
        *args,
        **kwargs,
    ):
        self.color = color
        self.rotation = rotation
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.color = ColorCIE(str_repr=xml_node.attrib.get("Color"))
        self.rotation = Rotation(str_repr=xml_node.attrib.get("Rotation"))


class Emitter(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        color: Optional["ColorCIE"] = None,
        dominant_wave_length: Optional[float] = None,
        diode_part: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.color = color
        self.dominant_wave_length = dominant_wave_length
        self.diode_part = diode_part
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.color = ColorCIE(str_repr=xml_node.attrib.get("Color"))
        self.dominant_wave_length = float(xml_node.attrib.get("DominantWaveLength", 0))
        self.diode_part = xml_node.attrib.get("DiodePart")
        self.measurements = [
            Measurement(xml_node=i) for i in xml_node.findall("Measurement")
        ]


class Filter(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        color: Optional["ColorCIE"] = None,
        measurements: Optional[List["Measurement"]] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.color = color
        if measurements is not None:
            self.measurements = measurements
        else:
            self.measurements = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.color = ColorCIE(str_repr=xml_node.attrib.get("Color"))
        self.measurements = [
            Measurement(xml_node=i) for i in xml_node.findall("Measurement")
        ]


class Measurement(BaseNode):
    def __init__(
        self,
        physical: Optional[float] = None,
        luminous_intensity: Optional[float] = None,
        transmission: Optional[float] = None,
        interpolation_to: "InterpolationTo" = InterpolationTo(None),
        *args,
        **kwargs,
    ):
        self.physical = physical
        self.luminous_intensity = luminous_intensity
        self.transmission = transmission
        self.interpolation_to = interpolation_to
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.physical = float(xml_node.attrib.get("Physical", 0))
        self.luminous_intensity = float(xml_node.attrib.get("LuminousIntensity", 0))
        self.transmission = float(xml_node.attrib.get("Transmission", 0))
        self.interpolation_to = InterpolationTo(xml_node.attrib.get("InterpolationTo"))
        self.measurement_points = [
            MeasurementPoint(xml_node=i) for i in xml_node.findall("MeasurementPoint")
        ]


class MeasurementPoint(BaseNode):
    def __init__(
        self,
        wave_length: Optional[float] = None,
        energy: Optional[float] = None,
        *args,
        **kwargs,
    ):
        self.wave_length = wave_length
        self.energy = energy
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.wave_length = float(xml_node.attrib.get("WaveLength", 0))
        self.energy = float(xml_node.attrib.get("Energy", 0))


class ColorSpace(BaseNode):
    def __init__(
        self,
        mode: "ColorSpaceMode" = ColorSpaceMode(None),
        definition: Optional["ColorSpaceDefinition"] = None,
        *args,
        **kwargs,
    ):
        self.mode = mode
        if definition is not None:
            self.definition = definition
        else:
            self._match_definition()
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.mode = ColorSpaceMode(xml_node.attrib.get("Mode"))
        if str(self.mode) == "Custom":
            self.red = ColorCIE(str_repr=xml_node.attrib.get("Red"))
            self.green = ColorCIE(str_repr=xml_node.attrib.get("Green"))
            self.blue = ColorCIE(str_repr=xml_node.attrib.get("Blue"))
            self.white_point = ColorCIE(str_repr=xml_node.attrib.get("WhitePoint"))
        else:
            self._match_definition()

    def _match_definition(self):
        # Match the name of the color space mode with a color space definition,
        # this will only work for sRGB, ProPhoto and ANSI modes
        if self.mode is None or str(self.mode) == "Custom":
            return
        elif str(self.mode) == "sRGB":
            self.definition = COLOR_SPACE_SRGB
        elif str(self.mode) == "ProPhoto":
            self.definition = COLOR_SPACE_PROPHOTO
        elif str(self.mode) == "ANSI":
            self.definition = COLOR_SPACE_ANSI


class DmxProfile(BaseNode):
    pass


class CriGroup(BaseNode):
    def __init__(
        self,
        color_temperature: float = 6000,
        cris: Optional[List["Cri"]] = None,
        *args,
        **kwargs,
    ):
        self.color_temperature = color_temperature
        if cris is not None:
            self.cris = cris
        else:
            self.cris = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.color_temperature = float(xml_node.attrib.get("ColorTemperature", 6000))
        self.cris = [Cri(xml_node=i) for i in xml_node.findall("CRI")]


class Cri(BaseNode):
    def __init__(
        self, ces: "Ces" = Ces(None), color_temperature: int = 100, *args, **kwargs
    ):
        self.ces = ces
        self.color_temperature = color_temperature
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.ces = Ces(xml_node.attrib.get("CES"))
        self.color_temperature = int(xml_node.attrib.get("ColorTemperature", 100))


class Model(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        length: float = 0,
        width: float = 0,
        height: float = 0,
        primitive_type: "PrimitiveType" = PrimitiveType(None),
        file: Optional["Resource"] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.length = length
        self.width = width
        self.height = height
        self.primitive_type = primitive_type
        self.file = file
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.length = float(xml_node.attrib.get("Length", 0))
        self.width = float(xml_node.attrib.get("Width", 0))
        self.height = float(xml_node.attrib.get("Height", 0))
        self.primitive_type = PrimitiveType(xml_node.attrib.get("PrimitiveType"))
        self.file = Resource(xml_node.attrib.get("File", ""))


class Geometry(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        model: Optional[str] = None,
        position: "Matrix" = Matrix(0),
        geometries: Optional[List] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.model = model
        self.position = position
        if geometries is not None:
            self.geometries = geometries
        else:
            self.geometries = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.model = xml_node.attrib.get("Model")
        self.position = Matrix(xml_node.attrib.get("Position", 0))
        for i in xml_node.findall("Geometry"):
            self.geometries.append(Geometry(xml_node=i))
        for i in xml_node.findall("Axis"):
            self.geometries.append(GeometryAxis(xml_node=i))
        for i in xml_node.findall("FilterBeam"):
            self.geometries.append(GeometryFilterBeam(xml_node=i))
        for i in xml_node.findall("FilterColor"):
            self.geometries.append(GeometryFilterColor(xml_node=i))
        for i in xml_node.findall("FilterGobo"):
            self.geometries.append(GeometryFilterGobo(xml_node=i))
        for i in xml_node.findall("FilterShaper"):
            self.geometries.append(GeometryFilterShaper(xml_node=i))
        for i in xml_node.findall("MediaServerMaster"):
            self.geometries.append(GeometryMediaServerMaster(xml_node=i))
        for i in xml_node.findall("MediaServerLayer"):
            self.geometries.append(GeometryMediaServerLayer(xml_node=i))
        for i in xml_node.findall("MediaServerCamera"):
            self.geometries.append(GeometryMediaServerCamera(xml_node=i))
        for i in xml_node.findall("Inventory"):
            self.geometries.append(GeometryInventory(xml_node=i))
        for i in xml_node.findall("Beam"):
            self.geometries.append(GeometryBeam(xml_node=i))
        for i in xml_node.findall("WiringObject"):
            self.geometries.append(GeometryWiringObject(xml_node=i))
        for i in xml_node.findall("GeometryReference"):
            self.geometries.append(GeometryReference(xml_node=i))
        for i in xml_node.findall("Laser"):
            self.geometries.append(GeometryLaser(xml_node=i))
        for i in xml_node.findall("Structure"):
            self.geometries.append(GeometryStructure(xml_node=i))
        for i in xml_node.findall("Support"):
            self.geometries.append(GeometrySupport(xml_node=i))
        for i in xml_node.findall("Magnet"):
            self.geometries.append(GeometryMagnet(xml_node=i))
        for i in xml_node.findall("Display"):
            self.geometries.append(GeometryDisplay(xml_node=i))

    def __str__(self):
        return f"{self.name} ({self.model})"


class GeometryAxis(Geometry):
    pass


class GeometryFilterBeam(Geometry):
    pass


class GeometryFilterColor(Geometry):
    pass


class GeometryFilterGobo(Geometry):
    pass


class GeometryFilterShaper(Geometry):
    pass


class GeometryMediaServerLayer(Geometry):
    pass


class GeometryMediaServerCamera(Geometry):
    pass


class GeometryMediaServerMaster(Geometry):
    pass


class GeometryDisplay(Geometry):
    def __init__(self, texture: Optional[str] = None, *args, **kwargs):
        self.texture = texture

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)
        self.texture = xml_node.attrib.get("texture")


class GeometryStructure(Geometry):
    def __init__(
        self,
        linked_geometry: Optional[str] = None,
        structure_type: StructureType = StructureType(None),
        cross_section_type: CrossSectionType = CrossSectionType(None),
        cross_section_height: float = 0,
        cross_section_wall_thickness: float = 0,
        truss_cross_section: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.linked_geometry = linked_geometry
        self.structure_type = structure_type
        self.cross_section_type = cross_section_type
        self.cross_section_height = cross_section_height
        self.cross_section_wall_thickness = cross_section_wall_thickness
        self.truss_cross_section = truss_cross_section

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)
        self.linked_geometry = xml_node.attrib.get("LinkedGeometry")
        self.structure_type = StructureType(xml_node.attrib.get("StructureType"))
        self.cross_section_type = CrossSectionType(
            xml_node.attrib.get("CrossSectionType")
        )
        self.cross_section_height = float(xml_node.attrib.get("CrossSectionHeight", 0))
        self.cross_section_wall_thickness = float(
            xml_node.attrib.get("CrossSectionWallThickness", 0)
        )
        self.truss_cross_section = xml_node.attrib.get("TrussCrossSection")


class GeometrySupport(Geometry):
    def __init__(
        self,
        support_type: SupportType = SupportType(None),
        rope_cross_section: Optional[str] = None,
        rope_offset: Vector3 = Vector3(0),
        capacity_x: float = 0,
        capacity_y: float = 0,
        capacity_z: float = 0,
        capacity_xx: float = 0,
        capacity_yy: float = 0,
        capacity_zz: float = 0,
        resistance_x: float = 0,
        resistance_y: float = 0,
        resistance_z: float = 0,
        resistance_xx: float = 0,
        resistance_yy: float = 0,
        resistance_zz: float = 0,
        *args,
        **kwargs,
    ):
        self.support_type = support_type
        self.rope_cross_section = rope_cross_section
        self.rope_offset = rope_offset
        self.capacity_x = capacity_x
        self.capacity_y = capacity_y
        self.capacity_z = capacity_z
        self.capacity_xx = capacity_xx
        self.capacity_yy = capacity_yy
        self.capacity_zz = capacity_zz
        self.resistance_x = resistance_x
        self.resistance_y = resistance_y
        self.resistance_z = resistance_z
        self.resistance_xx = resistance_xx
        self.resistance_yy = resistance_yy
        self.resistance_zz = resistance_zz

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)
        self.support_type = SupportType(xml_node.attrib.get("SupportType"))
        self.rope_cross_section = xml_node.attrib.get("RopeCrossSection")
        self.rope_offset = Vector3(xml_node.attrib.get("RopeOffset", 0))
        self.capacity_x = float(xml_node.attrib.get("CapacityX", 0))
        self.capacity_y = float(xml_node.attrib.get("CapacityY", 0))
        self.capacity_z = float(xml_node.attrib.get("CapacityZ", 0))
        self.capacity_xx = float(xml_node.attrib.get("CapacityXX", 0))
        self.capacity_yy = float(xml_node.attrib.get("CapacityYY", 0))
        self.capacity_zz = float(xml_node.attrib.get("CapacityZZ", 0))
        self.resistance_x = float(xml_node.attrib.get("ResistanceX", 0))
        self.resistance_y = float(xml_node.attrib.get("ResistanceY", 0))
        self.resistance_z = float(xml_node.attrib.get("ResistanceZ", 0))
        self.resistance_xx = float(xml_node.attrib.get("ResistanceXX", 0))
        self.resistance_yy = float(xml_node.attrib.get("ResistanceYY", 0))
        self.resistance_zz = float(xml_node.attrib.get("ResistanceZZ", 0))


class GeometryMagnet(Geometry):
    pass


class GeometryInventory(Geometry):
    def __init__(self, count: int = 1, *args, **kwargs):
        self.count = count

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)
        self.count = int(xml_node.attrib.get("Count", 1))


class GeometryBeam(Geometry):
    def __init__(
        self,
        lamp_type: "LampType" = LampType(None),
        power_consumption: float = 1000,
        luminous_flux: float = 10000,
        color_temperature: float = 6000,
        beam_angle: float = 25.0,
        field_angle: float = 25.0,
        beam_radius: float = 0.05,
        beam_type: BeamType = BeamType(None),
        color_rendering_index: int = 100,
        *args,
        **kwargs,
    ):
        self.lamp_type = lamp_type
        self.power_consumption = power_consumption
        self.luminous_flux = luminous_flux
        self.color_temperature = color_temperature
        self.beam_angle = beam_angle
        self.field_angle = field_angle
        self.beam_radius = beam_radius
        self.beam_type = beam_type
        self.color_rendering_index = color_rendering_index
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)
        self.lamp_type = LampType(xml_node.attrib.get("LampType"))
        self.power_consumption = float(xml_node.attrib.get("PowerConsumption", 1000))
        self.luminous_flux = float(xml_node.attrib.get("LuminousFlux", 10000))
        self.color_temperature = float(xml_node.attrib.get("ColorTemperature", 6000))
        self.beam_angle = float(xml_node.attrib.get("BeamAngle", 25))
        self.field_angle = float(xml_node.attrib.get("FieldAngle", 25))
        self.beam_radius = float(xml_node.attrib.get("BeamRadius", 0.05))
        self.beam_type = BeamType(xml_node.attrib.get("BeamType"))
        self.color_rendering_index = int(
            xml_node.attrib.get("ColorRenderingIndex", 100)
        )


class GeometryLaser(Geometry):
    def __init__(
        self,
        color_type: "ColorType" = ColorType(None),
        color: float = 0,
        output_strength: float = 0,
        emitter: Optional["NodeLink"] = None,
        beam_diameter: float = 0,
        beam_divergence_min: float = 0,
        beam_divergence_max: float = 0,
        scan_angle_pan: float = 0,
        scan_angle_tilt: float = 0,
        scan_speed: float = 0,
        protocols: List = [],
        *args,
        **kwargs,
    ):
        self.color_type = color_type
        self.color = color
        self.output_strength = output_strength
        self.emitter = emitter
        self.beam_diameter = beam_diameter
        self.beam_divergence_min = beam_divergence_min
        self.beam_divergence_max = beam_divergence_max
        self.scan_angle_pan = scan_angle_pan
        self.scan_angle_tilt = scan_angle_tilt
        self.scan_speed = scan_speed
        self.protocols = protocols
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)
        self.color_type = ColorType(xml_node.attrib.get("ColorType"))
        self.color = float(xml_node.attrib.get("Color", 530))  # Green
        self.output_strength = float(xml_node.attrib.get("OutputStrength", 1))
        self.emitter = NodeLink("EmitterCollect", xml_node.attrib.get("Emitter"))
        self.beam_diameter = float(xml_node.attrib.get("BeamDiameter", 0.005))
        self.beam_divergence_min = float(xml_node.attrib.get("BeamDivergenceMin", 0))
        self.beam_divergence_max = float(xml_node.attrib.get("BeamDivergenceMax", 0))
        self.scan_angle_pan = float(xml_node.attrib.get("ScanAnglePan", 30))
        self.scan_angle_tilt = float(xml_node.attrib.get("ScanAngleTilt", 30))
        self.scan_speed = float(xml_node.attrib.get("ScanSpeed", 0))
        self.protocols = [Protocol(xml_node=i) for i in xml_node.findall("Protocol")]


class Protocol(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")

    def __str__(self):
        return f"{self.name}"


class GeometryWiringObject(Geometry):
    def __init__(
        self,
        connector_type: Optional[str] = None,
        component_type: "ComponentType" = ComponentType(None),
        signal_type: Optional[str] = None,
        pin_count: int = 0,
        electrical_payload: float = 0,
        voltage_range_max: float = 0,
        voltage_range_min: float = 0,
        frequency_range_max: float = 0,
        frequency_range_min: float = 0,
        max_payload: float = 0,
        voltage: float = 0,
        signal_layer: int = 0,
        cos_phi: float = 0,
        fuse_current: float = 0,
        fuse_rating: "FuseRating" = FuseRating(None),
        orientation: "Orientation" = Orientation(None),
        wire_group: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.connector_type = connector_type
        self.component_type = component_type
        self.signal_type = signal_type
        self.pin_count = pin_count
        self.electrical_payload = electrical_payload
        self.voltage_range_max = voltage_range_max
        self.voltage_range_min = voltage_range_min
        self.frequency_range_min = frequency_range_min
        self.frequency_range_max = frequency_range_max
        self.max_payload = max_payload
        self.voltage = voltage
        self.signal_layer = signal_layer
        self.cos_phi = cos_phi
        self.fuse_current = fuse_current
        self.fuse_rating = fuse_rating
        self.orientation = orientation
        self.wire_group = wire_group
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        super()._read_xml(xml_node)
        self.connector_type = xml_node.attrib.get("ConnectorType")
        self.component_type = ComponentType(xml_node.attrib.get("ComponentType"))
        self.signal_type = xml_node.attrib.get("SignalType")
        self.pin_count = int(xml_node.attrib.get("PinCount", 0))
        self.electrical_payload = float(xml_node.attrib.get("ElectricalPayLoad", 0))
        self.voltage_range_max = float(xml_node.attrib.get("VoltageRangeMax", 0))
        self.voltage_range_min = float(xml_node.attrib.get("VoltageRangeMin", 0))
        self.frequency_range_max = float(xml_node.attrib.get("FrequencyRangeMax", 0))
        self.frequency_range_min = float(xml_node.attrib.get("FrequencyRangeMin", 0))
        self.max_payload = float(xml_node.attrib.get("MaxPayLoad", 0))
        self.voltage = float(xml_node.attrib.get("Voltage", 0))
        self.signal_layer = int(xml_node.attrib.get("SignalLayer", 0))
        self.cos_phi = float(xml_node.attrib.get("CosPhi", 0))
        self.fuse_current = float(xml_node.attrib.get("FuseCurrent", 0))
        self.fuse_rating = FuseRating(xml_node.attrib.get("FuseRating"))
        self.orientation = Orientation(xml_node.attrib.get("Orientation"))
        self.wire_group = xml_node.attrib.get("WireGroup")


class GeometryReference(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        position: "Matrix" = Matrix(0),
        geometry: Optional[str] = None,
        model: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.position = position
        self.geometry = geometry
        self.model = model
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.position = Matrix(xml_node.attrib.get("Position", 0))
        self.geometry = xml_node.attrib.get("Geometry")
        self.model = xml_node.attrib.get("Model")
        self.breaks = [Break(xml_node=i) for i in xml_node.findall("Break")]

    def __str__(self):
        return f"{self.name} ({self.model})"


class Break(BaseNode):
    def __init__(
        self,
        dmx_offset: "DmxAddress" = DmxAddress("1"),
        dmx_break: int = 1,
        *args,
        **kwargs,
    ):
        self.dmx_offset = dmx_offset
        self.dmx_break = dmx_break
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.dmx_offset = DmxAddress(xml_node.attrib.get("DMXOffset"))
        self.dmx_break = int(xml_node.attrib.get("DMXBreak", 1))

    def __str__(self):
        return f"Break: {self.dmx_break}, Offset: {self.dmx_offset}"


class DmxMode(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        geometry: Optional[str] = None,
        dmx_channels: Optional[List["DmxChannel"]] = None,
        relations: Optional[List["Relation"]] = None,
        ft_macros: Optional[List["Macro"]] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.geometry = geometry
        if dmx_channels is not None:
            self.dmx_channels = dmx_channels
        else:
            self.dmx_channels = []
        if relations is not None:
            self.relations = relations
        else:
            self.relations = []
        if ft_macros is not None:
            self.ft_macros = ft_macros
        else:
            self.ft_macros = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.geometry = xml_node.attrib.get("Geometry")

        if dmx_channels_collect := xml_node.find("DMXChannels"):
            self.dmx_channels = [
                DmxChannel(xml_node=i)
                for i in dmx_channels_collect.findall("DMXChannel")
            ]

        if relations_node := xml_node.find("Relations"):
            self.relations = [
                Relation(xml_node=i) for i in relations_node.findall("Relation")
            ]

        if ftmacros_node := xml_node.find("FTMacros"):
            self.ft_macros = [
                Macro(xml_node=i) for i in ftmacros_node.findall("FTMacro")
            ]


class DmxChannel(BaseNode):
    def __init__(
        self,
        dmx_break: Union[int, str] = 1,
        offset: Optional[List[int]] = None,
        default: "DmxValue" = DmxValue("0/1"),
        highlight: Optional["DmxValue"] = None,
        initial_function: Optional["NodeLink"] = None,
        geometry: Optional[str] = None,
        logical_channels: Optional[List["LogicalChannel"]] = None,
        *args,
        **kwargs,
    ):
        self.dmx_break = dmx_break
        self.offset = offset
        self.default = default
        self.highlight = highlight
        self.initial_function = initial_function
        self.geometry = geometry
        self.logical_channels = logical_channels
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        try:
            self.dmx_break = int(xml_node.attrib.get("DMXBreak", 1))
        except ValueError:
            self.dmx_break = "Overwrite"
        _offset = xml_node.attrib.get("Offset")
        if _offset is None or _offset == "None" or _offset == "":
            self.offset = None
        else:
            self.offset = [
                int(i)
                for i in xml_node.attrib.get("Offset", "").split(",")
                if xml_node.attrib.get("Offset")
            ]

        # obsoleted by initial function in GDTF 1.2
        self.default = DmxValue(xml_node.attrib.get("Default", "0/1"))

        highlight_node = xml_node.attrib.get("Highlight")
        if highlight_node is not None:
            highlight_value = xml_node.attrib.get("Highlight", "0/1")

            if highlight_value != "None":
                self.highlight = DmxValue(highlight_value)

        self.geometry = xml_node.attrib.get("Geometry")
        self.logical_channels = [
            LogicalChannel(xml_node=i) for i in xml_node.findall("LogicalChannel")
        ] or [LogicalChannel(attribute=NodeLink("Attributes", "NoFeature"))]

        initial_function_node = xml_node.attrib.get("InitialFunction")
        if initial_function_node:
            self.initial_function = NodeLink(
                xml_node, xml_node.attrib.get("InitialFunction")
            )
            for logical_channel in self.logical_channels:
                for channel_function in logical_channel.channel_functions:
                    if channel_function.name == self.initial_function:
                        self.default = channel_function.default


class LogicalChannel(BaseNode):
    def __init__(
        self,
        attribute: Optional["NodeLink"] = None,
        snap: "Snap" = Snap(None),
        master: "Master" = Master(None),
        mib_fade: float = 0,
        dmx_change_time_limit: float = 0,
        channel_functions: Optional[List["ChannelFunction"]] = None,
        *args,
        **kwargs,
    ):
        self.attribute = attribute
        self.snap = snap
        self.master = master
        self.mib_fade = mib_fade
        self.dmx_change_time_limit = dmx_change_time_limit
        if channel_functions is not None:
            self.channel_functions = channel_functions
        else:
            self.channel_functions = [
                ChannelFunction(
                    attribute=NodeLink("Attributes", "NoFeature"),
                    default=DmxValue("0/1"),
                )
            ]
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.attribute = NodeLink("Attributes", xml_node.attrib.get("Attribute"))
        self.snap = Snap(xml_node.attrib.get("Snap"))
        self.master = Master(xml_node.attrib.get("Master"))
        self.mib_fade = float(xml_node.attrib.get("MibFade", 0))
        self.dmx_change_time_limit = float(xml_node.attrib.get("DMXChangeTimeLimit", 0))
        self.channel_functions = [
            ChannelFunction(xml_node=i) for i in xml_node.findall("ChannelFunction")
        ] or [
            ChannelFunction(
                attribute=NodeLink("Attributes", "NoFeature"),
                default=DmxValue("0/1"),
            )
        ]


class ChannelFunction(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        attribute: Union["NodeLink", str] = NodeLink("Attributes", "NoFeature"),
        original_attribute: Optional[str] = None,
        dmx_from: "DmxValue" = DmxValue("0/1"),
        default: "DmxValue" = DmxValue("0/1"),
        physical_from: float = 0,
        physical_to: float = 1,
        real_fade: float = 0,
        wheel: Optional["NodeLink"] = None,
        emitter: Optional["NodeLink"] = None,
        chn_filter: Optional["NodeLink"] = None,
        dmx_invert: "DmxInvert" = DmxInvert(None),
        mode_master: Optional["NodeLink"] = None,
        mode_from: "DmxValue" = DmxValue("0/1"),
        mode_to: "DmxValue" = DmxValue("0/1"),
        channel_sets: Optional[List["ChannelSet"]] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        self.attribute = attribute
        self.original_attribute = original_attribute
        self.dmx_from = dmx_from
        self.default = default
        self.physical_from = physical_from
        self.physical_to = physical_to
        self.real_fade = real_fade
        self.wheel = wheel
        self.emitter = emitter
        self.filter = chn_filter
        self.dmx_invert = dmx_invert
        self.mode_master = mode_master
        self.mode_from = mode_from
        self.mode_to = mode_to
        if channel_sets is not None:
            self.channel_sets = channel_sets
        else:
            self.channel_sets = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.attribute = NodeLink(
            "Attributes", xml_node.attrib.get("Attribute", "NoFeature")
        )
        self.original_attribute = xml_node.attrib.get("OriginalAttribute")
        self.dmx_from = DmxValue(xml_node.attrib.get("DMXFrom", "0/1"))
        self.default = DmxValue(xml_node.attrib.get("Default", "0/1"))
        self.physical_from = float(xml_node.attrib.get("PhysicalFrom", 0))
        self.physical_to = float(xml_node.attrib.get("PhysicalTo", 1))
        self.real_fade = float(xml_node.attrib.get("RealFade", 0))
        self.wheel = NodeLink("WheelCollect", xml_node.attrib.get("Wheel"))
        self.emitter = NodeLink("EmitterCollect", xml_node.attrib.get("Emitter"))
        self.filter = NodeLink("FilterCollect", xml_node.attrib.get("Filter"))
        self.dmx_invert = DmxInvert(xml_node.attrib.get("DMXInvert"))
        self.mode_master = NodeLink("DMXChannel", xml_node.attrib.get("ModeMaster"))
        self.mode_from = DmxValue(xml_node.attrib.get("ModeFrom", "0/1"))
        self.mode_to = DmxValue(xml_node.attrib.get("ModeTo", "0/1"))
        self.channel_sets = [
            ChannelSet(xml_node=i) for i in xml_node.findall("ChannelSet")
        ]


class ChannelSet(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        dmx_from: "DmxValue" = DmxValue("0/1"),
        physical_from: float = 0,
        physical_to: float = 1,
        wheel_slot_index: int = 1,
        *args,
        **kwargs,
    ):
        self.name = name
        self.dmx_from = dmx_from
        self.physical_from = physical_from
        self.physical_to = physical_to
        self.wheel_slot_index = wheel_slot_index
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.dmx_from = DmxValue(xml_node.attrib.get("DMXFrom", "0/1"))
        self.physical_from = float(xml_node.attrib.get("PhysicalFrom", 0))
        self.physical_to = float(xml_node.attrib.get("PhysicalTo", 1))
        self.wheel_slot_index = int(xml_node.attrib.get("WheelSlotIndex", 1))


class Relation(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        master: Optional["NodeLink"] = None,
        follower: Optional["NodeLink"] = None,
        rel_type: "RelationType" = RelationType(None),
        *args,
        **kwargs,
    ):
        self.name = name
        self.master = master
        self.follower = follower
        self.type = rel_type
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")
        self.master = NodeLink("DMXMode", xml_node.attrib.get("Master"))
        self.follower = NodeLink("DMXMode", xml_node.attrib.get("Follower"))
        self.type = RelationType(xml_node.attrib.get("Type"))


class Macro(BaseNode):
    def __init__(
        self,
        name: Optional[str] = None,
        dmx_steps: Optional[List["MacroDmxStep"]] = None,
        visual_steps: Optional[List["MacroVisualStep"]] = None,
        *args,
        **kwargs,
    ):
        self.name = name
        if dmx_steps is not None:
            self.dmx_steps = dmx_steps
        else:
            self.dmx_steps = []
        if visual_steps is not None:
            self.visual_steps = visual_steps
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")

        if macro_dmx_collect := xml_node.find("MacroDMX"):
            self.dmx_steps = [
                MacroDmxStep(xml_node=i)
                for i in macro_dmx_collect.findall("MacroDMXStep")
            ]
        if macro_visual_collect := xml_node.find("MacroVisual"):
            self.visual_steps = [
                MacroVisualStep(xml_node=i)
                for i in macro_visual_collect.findall("MacroVisualStep")
            ]


class MacroDmxStep(BaseNode):
    def __init__(
        self,
        duration: float = 1,
        dmx_values: Optional[List["MacroDmxValue"]] = None,
        *args,
        **kwargs,
    ):
        self.duration = duration
        if dmx_values is not None:
            self.dmx_values = dmx_values
        else:
            self.dmx_values = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.duration = float(xml_node.attrib.get("Duration", 0.0))
        self.dmx_values = [
            MacroDmxValue(xml_node=i) for i in xml_node.findall("MacroDMXValue")
        ]


class MacroDmxValue(BaseNode):
    def __init__(
        self,
        macro_value: Optional["DmxValue"] = None,
        dmx_channel: Optional["NodeLink"] = None,
        *args,
        **kwargs,
    ):
        self.value = macro_value
        self.dmx_channel = dmx_channel
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.value = DmxValue(xml_node.attrib.get("Value"))
        self.dmx_channel = NodeLink(
            "DMXChannelCollect", xml_node.attrib.get("DMXChannel")
        )


class MacroVisualStep(BaseNode):
    def __init__(
        self,
        duration: int = 1,
        fade: float = 0.0,
        delay: float = 0.0,
        visual_values: Optional[List["MacroVisualValue"]] = None,
        *args,
        **kwargs,
    ):
        self.duration = duration
        self.fade = fade
        self.delay = delay
        if visual_values is not None:
            self.visual_values = visual_values
        else:
            self.visual_values = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.duration = int(xml_node.attrib.get("Duration", 1))
        self.fade = float(xml_node.attrib.get("Fade", 0.0))
        self.delay = float(xml_node.attrib.get("Delay", 0.0))
        self.visual_values = [
            MacroVisualValue(xml_node=i) for i in xml_node.findall("MacroVisualValue")
        ]


class MacroVisualValue(BaseNode):
    def __init__(
        self,
        macro_value: Optional["DmxValue"] = None,
        channel_function: Optional["NodeLink"] = None,
        *args,
        **kwargs,
    ):
        self.value = macro_value
        self.channel_function = channel_function
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.value = DmxValue(xml_node.attrib.get("Value"))
        self.channel_function = NodeLink(
            "DMXChannelCollect", xml_node.attrib.get("ChannelFunction")
        )


class Revision(BaseNode):
    def __init__(
        self,
        text: Optional[str] = None,
        date: Optional[str] = None,
        user_id: int = 0,
        *args,
        **kwargs,
    ):
        self.text = text
        self.date = date
        self.user_id = user_id
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.text = xml_node.attrib.get("Text")
        self.date = xml_node.attrib.get("Date")
        self.user_id = int(xml_node.attrib.get("UserID", 0))

    class date_formats(pyEnum):
        STRING = "string"
        DATETIME = "datetime"
        TIMESTAMP = "timestamp"

    def get_date(self, format_as: "date_formats" = date_formats.STRING):
        if self.date is not None:
            if format_as == self.date_formats.DATETIME:
                return parse_date(self.date)
            elif format_as == self.date_formats.STRING:
                return self.date
            elif format_as == self.date_formats.TIMESTAMP:
                return int(parse_date(self.date).timestamp())

    def __str__(self):
        return f"{self.text} {self.date}"


class Properties(BaseNode):
    def __init__(
        self,
        weight: float = 0,
        operating_temperature_low: float = 0,
        operating_temperature_high: float = 40,
        leg_height: float = 0,
        *args,
        **kwargs,
    ):
        self.weight = weight
        self.leg_height = leg_height
        self.operating_temperature_low = operating_temperature_low
        self.operating_temperature_high = operating_temperature_high

        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        operating_temperatures = xml_node.find("OperatingTemperature")
        if operating_temperatures is not None:
            self.operating_temperature_low = float(
                operating_temperatures.attrib.get("Low", 0)
            )
            self.operating_temperature_high = float(
                operating_temperatures.attrib.get("High", 30)
            )
        leg_height_tag = xml_node.find("LegHeight")
        if leg_height_tag is not None:
            self.leg_height = float(leg_height_tag.attrib.get("Value", 0))

        weight_tag = xml_node.find("Weight")
        if weight_tag is not None:
            self.weight = float(weight_tag.attrib.get("Value", 0))


class Rdm(BaseNode):
    def __init__(
        self,
        manufacturer_id: int = 0,
        device_model_id: int = 0,
        software_versions: Optional[List["SoftwareVersionId"]] = None,
        *args,
        **kwargs,
    ):
        self.manufacturer_id = manufacturer_id
        self.device_model_id = device_model_id
        if software_versions is not None:
            self.software_versions = software_versions
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.manufacturer_id = int(xml_node.attrib.get("ManufacturerID", "0"), 16)
        self.device_model_id = int(xml_node.attrib.get("DeviceModelID", "0"), 16)
        self.software_versions = [
            SoftwareVersionId(xml_node=i) for i in xml_node.findall("SoftwareVersionID")
        ]

    def __str__(self):
        return (
            f"{self.manufacturer_id} ({self.device_model_id}) {self.software_versions}"
        )


class SoftwareVersionId(BaseNode):
    def __init__(
        self,
        value: Optional[str] = None,
        dmx_personalities: Optional[List["DmxPersonality"]] = None,
        *args,
        **kwargs,
    ):
        self.value = value
        if dmx_personalities is not None:
            self.dmx_personalities = dmx_personalities
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.value = xml_node.attrib.get("Value")
        self.dmx_personalities = [
            DmxPersonality(xml_node=i) for i in xml_node.findall("DMXPersonality")
        ]

    def __str__(self):
        return f"{self.value} {self.dmx_personalities}"


class DmxPersonality(BaseNode):
    def __init__(
        self,
        dmx_mode: Optional[str] = None,
        value: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.dmx_mode = dmx_mode
        self.value = value
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.dmx_mode = xml_node.attrib.get("DMXMode")
        self.value = xml_node.attrib.get("Value")

    def __str__(self):
        return f"{self.dmx_mode} ({self.value})"


class ArtNet(BaseNode):
    def __init__(
        self,
        maps: Optional[List["Map"]] = None,
        *args,
        **kwargs,
    ):
        if maps is not None:
            self.maps = maps
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.maps = [Map(xml_node=i) for i in xml_node.findall("Map")]


class Map(BaseNode):
    def __init__(
        self,
        key: int = 0,
        value: int = 0,
        *args,
        **kwargs,
    ):
        self.key = key
        self.value = value
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.key = int(xml_node.attrib.get("Key", 0))
        self.value = int(xml_node.attrib.get("Value", 0))

    def __str__(self):
        return f"{self.key} {self.value}"


class Sacn(BaseNode):
    pass


class PosiStageNet(BaseNode):
    pass


class OpenSoundControl(BaseNode):
    pass


class Citp(BaseNode):
    pass
