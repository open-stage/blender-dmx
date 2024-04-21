from typing import List, Union, Optional
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
import zipfile
from .value import *  # type: ignore
from .utils import *

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
        if description_str[-1]=="\x00": # this should not happen, but...
            description_str = description_str[:-1]
    return ElementTree.fromstring(description_str)


class FixtureType:
    def __init__(self, path=None):
        self._package = None
        self._root = None
        if path is not None:
            self._package = zipfile.ZipFile(path, "r")
        if self._package is not None:
            self._gdtf = _find_root(self._package)
            self._root = self._gdtf.find("FixtureType")
        if self._root is not None:
            self._read_xml()

    def _read_xml(self):
        self.data_version = self._gdtf.get("DataVersion")
        self.name = self._root.get("Name")
        self.short_name = self._root.get("ShortName")
        self.long_name = self._root.get("LongName")
        self.manufacturer = self._root.get("Manufacturer")
        self.description = self._root.get("Description")
        self.fixture_type_id = self._root.get("FixtureTypeID")
        self.thumbnail = self._root.get("Thumbnail", "").encode("utf-8").decode("cp437")
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
            if f"models/gltf/{model.file.name}.glb" in self._package.namelist():
                model.file.extension = "glb"
            else:
                model.file.extension = "3ds"

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
        if dmx_mode_collect := self._root.find("DMXModes"):
            self.dmx_modes = [
                DmxMode(xml_node=i) for i in dmx_mode_collect.findall("DMXMode")
            ]
        else:
            self.dmx_modes = []
        if revision_collect := self._root.find("Revisions"):
            self.revisions = [
                Revision(xml_node=i) for i in revision_collect.findall("Revision")
            ]
        else:
            self.revisions = []


class BaseNode:
    def __init__(self, xml_node: "Element" = None):
        if xml_node is not None:
            self._read_xml(xml_node)

    def _read_xml(self, xml_node: "Element"):
        pass


class ActivationGroup(BaseNode):
    def __init__(self, name: str = None, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")


class FeatureGroup(BaseNode):
    def __init__(
        self,
        name: str = None,
        pretty: str = None,
        features: List["Feature"] = None,
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
    def __init__(self, name: str = None, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.name = xml_node.attrib.get("Name")


class Attribute(BaseNode):
    def __init__(
        self,
        name: str = None,
        pretty: str = None,
        activation_group: "NodeLink" = None,
        feature: "NodeLink" = None,
        main_attribute: "NodeLink" = None,
        physical_unit: "PhysicalUnit" = PhysicalUnit(None),
        color: "ColorCIE" = None,
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
        self, name: str = None, wheel_slots: List["WheelSlot"] = None, *args, **kwargs
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
        name: str = None,
        color: "ColorCIE" = None,
        whl_filter: "NodeLink" = None,
        media_file_name: "Resource" = None,
        facets: List["PrismFacet"] = None,
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
        self, color: "ColorCIE" = None, rotation: "Rotation" = None, *args, **kwargs
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
        name: str = None,
        color: "ColorCIE" = None,
        dominant_wave_length: float = None,
        diode_part: str = None,
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
        try:
            self.dominant_wave_length = float(xml_node.attrib.get("DominantWaveLength"))
        except TypeError:
            self.dominant_wave_length = None
        self.diode_part = xml_node.attrib.get("DiodePart")
        self.measurements = [
            Measurement(xml_node=i) for i in xml_node.findall("Measurement")
        ]


class Filter(BaseNode):
    def __init__(
        self,
        name: str = None,
        color: "ColorCIE" = None,
        measurements: List["Measurement"] = None,
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
        physical: float = None,
        luminous_intensity: float = None,
        transmission: float = None,
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
        self.physical = float(xml_node.attrib.get("Physical"))
        try:
            self.luminous_intensity = float(xml_node.attrib.get("LuminousIntensity"))
        except TypeError:
            self.luminous_intensity = None
        try:
            self.transmission = float(xml_node.attrib.get("Transmission"))
        except TypeError:
            self.transmission = None
        self.interpolation_to = InterpolationTo(xml_node.attrib.get("InterpolationTo"))
        self.measurement_points = [
            MeasurementPoint(xml_node=i) for i in xml_node.findall("MeasurementPoint")
        ]


class MeasurementPoint(BaseNode):
    def __init__(
        self, wave_length: float = None, energy: float = None, *args, **kwargs
    ):
        self.wave_length = wave_length
        self.energy = energy
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.wave_length = float(xml_node.attrib.get("WaveLength"))
        self.energy = float(xml_node.attrib.get("Energy"))


class ColorSpace(BaseNode):
    def __init__(
        self,
        mode: "ColorSpaceMode" = ColorSpaceMode(None),
        definition: "ColorSpaceDefinition" = None,
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
        self, color_temperature: float = 6000, cris: List["Cri"] = None, *args, **kwargs
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
        name: str = None,
        length: float = 0,
        width: float = 0,
        height: float = 0,
        primitive_type: "PrimitiveType" = PrimitiveType(None),
        file: Resource = None,
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
        name: str = None,
        model: str = None,
        position: "Matrix" = Matrix(0),
        geometries: List = None,
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


class GeometryMediaServerMaster(Geometry):
    pass


class GeometryMediaServerCamera(Geometry):
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
        emitter: "NodeLink" = None,
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
        self.color = float(xml_node.attrib.get("Color", 530)) # Green
        self.output_strength = float(xml_node.attrib.get("OutputStrength", 1))
        self.emitter = NodeLink("EmitterCollect", xml_node.attrib.get("Emitter"))
        self.beam_diameter = float(xml_node.attrib.get("BeamDiameter", 0.005))
        self.beam_divergence_min = float(xml_node.attrib.get("BeamDivergenceMin", 0))
        self.beam_divergence_max = float(xml_node.attrib.get("BeamDivergenceMax", 0))
        self.scan_angle_pan = float(xml_node.attrib.get("ScanAnglePan", 30))
        self.scan_angle_tilt = float(xml_node.attrib.get("ScanAngleTilt", 30))
        self.scan_speed = float(xml_node.attrib.get("ScanSpeed", 0))
        self.protocols = [
            Protocol(xml_node=i) for i in xml_node.findall("Protocol")
        ]

class Protocol(BaseNode):
    def __init__(
        self,
        name: str = None,
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
        connector_type: str = None,
        component_type: "ComponentType" = ComponentType(None),
        signal_type: str = None,
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
        wire_group: str = None,
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
        self.pin_count = int(xml_node.attrib.get("PinCount"))
        self.electrical_payload = float(xml_node.attrib.get("ElectricalPayLoad"))
        self.voltage_range_max = float(xml_node.attrib.get("VoltageRangeMax"))
        self.voltage_range_min = float(xml_node.attrib.get("VoltageRangeMin"))
        self.frequency_range_max = float(xml_node.attrib.get("FrequencyRangeMax"))
        self.frequency_range_min = float(xml_node.attrib.get("FrequencyRangeMin"))
        self.max_payload = float(xml_node.attrib.get("MaxPayLoad"))
        self.voltage = float(xml_node.attrib.get("Voltage"))
        self.signal_layer = int(xml_node.attrib.get("SignalLayer"))
        self.cos_phi = float(xml_node.attrib.get("CosPhi"))
        self.fuse_current = float(xml_node.attrib.get("FuseCurrent"))
        self.fuse_rating = FuseRating(xml_node.attrib.get("FuseRating"))
        self.orientation = Orientation(xml_node.attrib.get("Orientation"))
        self.wire_group = xml_node.attrib.get("WireGroup")


class GeometryReference(BaseNode):
    def __init__(
        self,
        name: str = None,
        position: "Matrix" = Matrix(0),
        geometry: str = None,
        model: str = None,
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
        name: str = None,
        geometry: str = None,
        dmx_channels: List["DmxChannel"] = None,
        relations: List["Relation"] = None,
        ft_macros: List["Macro"] = None,
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
        self.dmx_channels = [
            DmxChannel(xml_node=i)
            for i in xml_node.find("DMXChannels").findall("DMXChannel")
        ]

        relations_node = xml_node.find("Relations")
        if relations_node:
            self.relations = [
                Relation(xml_node=i) for i in relations_node.findall("Relation")
            ]

        ftmacros_node = xml_node.find("FTMacros")
        if ftmacros_node:
            self.ft_macros = [
                Macro(xml_node=i) for i in ftmacros_node.findall("FTMacro")
            ]


class DmxChannel(BaseNode):
    def __init__(
        self,
        dmx_break: Union[int, str] = 1,
        offset: List[int] = None,
        default: "DmxValue" = DmxValue("0/1"),
        highlight: Optional["DmxValue"] = None,
        initial_function: "NodeLink" = None,
        geometry: Optional[str] = None,
        logical_channels: List["LogicalChannel"] = None,
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
            self.offset = [int(i) for i in xml_node.attrib.get("Offset").split(",")]

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
        ]

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
        attribute: "NodeLink" = None,
        snap: "Snap" = Snap(None),
        master: "Master" = Master(None),
        mib_fade: float = 0,
        dmx_change_time_limit: float = 0,
        channel_functions: List["ChannelFunction"] = None,
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
            self.channel_functions = []
        super().__init__(*args, **kwargs)

    def _read_xml(self, xml_node: "Element"):
        self.attribute = NodeLink("Attributes", xml_node.attrib.get("Attribute"))
        self.snap = Snap(xml_node.attrib.get("Snap"))
        self.master = Master(xml_node.attrib.get("Master"))
        self.mib_fade = float(xml_node.attrib.get("MibFade", 0))
        self.dmx_change_time_limit = float(xml_node.attrib.get("DMXChangeTimeLimit", 0))
        self.channel_functions = [
            ChannelFunction(xml_node=i) for i in xml_node.findall("ChannelFunction")
        ]


class ChannelFunction(BaseNode):
    def __init__(
        self,
        name: str = None,
        attribute: Union["NodeLink", str] = "NoFeature",
        original_attribute: str = None,
        dmx_from: "DmxValue" = DmxValue("0/1"),
        default: "DmxValue" = DmxValue("0/1"),
        physical_from: float = 0,
        physical_to: float = 1,
        real_fade: float = 0,
        wheel: "NodeLink" = None,
        emitter: "NodeLink" = None,
        chn_filter: "NodeLink" = None,
        dmx_invert: "DmxInvert" = DmxInvert(None),
        mode_master: "NodeLink" = None,
        mode_from: "DmxValue" = DmxValue("0/1"),
        mode_to: "DmxValue" = DmxValue("0/1"),
        channel_sets: List["ChannelSet"] = None,
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
        name: str = None,
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
        name: str = None,
        master: "NodeLink" = None,
        follower: "NodeLink" = None,
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
        name: str = None,
        dmx_steps: List["MacroDmxStep"] = None,
        visual_steps: List["MacroVisualStep"] = None,
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
        try:
            self.dmx_steps = [
                MacroDmxStep(xml_node=i)
                for i in xml_node.find("MacroDMX").findall("MacroDMXStep")
            ]
        except AttributeError:
            pass
        try:
            self.visual_steps = [
                MacroVisualStep(xml_node=i)
                for i in xml_node.find("MacroVisual").findall("MacroVisualStep")
            ]
        except AttributeError:
            pass


class MacroDmxStep(BaseNode):
    def __init__(
        self,
        duration: float = 1,
        dmx_values: List["MacroDmxValue"] = None,
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
        self.duration = float(xml_node.attrib.get("Duration"))
        self.dmx_values = [
            MacroDmxValue(xml_node=i) for i in xml_node.findall("MacroDMXValue")
        ]


class MacroDmxValue(BaseNode):
    def __init__(
        self,
        macro_value: "DmxValue" = None,
        dmx_channel: "NodeLink" = None,
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
        visual_values: List["MacroVisualValue"] = None,
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
        macro_value: "DmxValue" = None,
        channel_function: "NodeLink" = None,
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
        text: Union[str, None] = None,
        date: Union[str, None] = None,
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


class Properties(BaseNode):
    def __init__(
        self,
        weight=0,
        operating_temperature_low=0,
        operating_temperature_high=40,
        leg_height=0,
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
