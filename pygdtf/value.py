from collections import namedtuple
from typing import List, Optional, Union


# Data type that only allows a specific set of values, if given a value
# which is not permitted, the value will be set to the default
class Enum:
    permitted: List[str] = []
    _default: Optional[str] = None

    def __init__(self, value):
        self.value = None
        if value not in self.permitted:
            self.value = self._default
        else:
            self.value = value

    def __str__(self):
        return str(self.value)

    def __bool__(self):
        return bool(self.value)


class PhysicalUnit(Enum):
    permitted = [
        "None",
        "Percent",
        "Length",
        "Mass",
        "Time",
        "Temperature",
        "LuminousIntensity",
        "Angle",
        "Force",
        "Frequency",
        "Current",
        "Voltage",
        "Power",
        "Energy",
        "Area",
        "Volume",
        "Speed",
        "Acceleration",
        "AngularSpeed",
        "AngularAcc",
        "WaveLength",
        "ColorComponent",
    ]
    default = "None"


class InterpolationTo(Enum):
    permitted = ["Linear", "Step", "Log"]
    _default = "Linear"


class ColorSpaceMode(Enum):
    permitted = ["Custom", "sRGB", "ProPhoto", "ANSI"]
    _default = "sRGB"


class Ces(Enum):
    permitted = [f"CES{str(n).zfill(2)}" for n in range(1, 100)]
    _default = "CES01"


class PrimitiveType(Enum):
    permitted = [
        "Undefined",
        "Cube",
        "Cylinder",
        "Sphere",
        "Base",
        "Yoke",
        "Head",
        "Scanner",
        "Conventional",
        "Pigtail",
        "Base1_1",
        "Scanner1_1",
        "Conventional1_1",
    ]
    _default = "Undefined"


class LampType(Enum):
    permitted = ["Discharge", "Tungsten", "Halogen", "LED"]
    _default = "Discharge"


class ColorType(Enum):
    permitted = ["RGB", "SingleWaveLength"]
    _default = "RGB"


class FuseRating(Enum):
    permitted = ["B", "C", "D", "K", "Z"]
    _default = "B"


class Orientation(Enum):
    permitted = ["Left", "Right", "Top", "Bottom"]
    _default = "Left"


class ComponentType(Enum):
    permitted = [
        "Input",
        "Output",
        "PowerSource",
        "Consumer",
        "Fuse",
        "NetworkProvider",
        "NetworkInput",
        "NetworkOutput",
        "NetworkInOut",
    ]
    _default = "Input"


class BeamType(Enum):
    permitted = ["Wash", "Spot", "None", "Rectangle", "PC", "Fresnel", "Glow"]
    _default = "Wash"


class Snap(Enum):
    permitted = ["Yes", "No", "On", "Off"]
    _default = "No"


class Master(Enum):
    permitted = ["None", "Grand", "Group"]
    _default = "None"


class DmxInvert(Enum):
    permitted = ["Yes", "No"]
    _default = "No"


class RelationType(Enum):
    permitted = ["Multiply", "Override"]


class StructureType(Enum):
    permitted = ["CenterLineBased", "Detail"]
    _default = "CenterLineBased"


class CrossSectionType(Enum):
    permitted = ["TrussFramework", "Tube"]
    _default = "TrussFramework"


class SupportType(Enum):
    permitted = ["Rope", "GroundSupport"]
    _default = "Rope"


class Resource:
    def __init__(self, name, extension=None, crc=None):
        self.name = name
        if name is not None:
            self.name = self.name.encode("utf-8").decode("cp437")
        self.extension = extension
        self.crc = crc

    def __str__(self):
        return ".".join([self.name, self.extension])


class DmxAddress:
    def __init__(self, str_repr):
        if "." in str_repr:
            self.universe = int(str_repr.split(".")[0])
            self.address = int(str_repr.split(".")[1])
        else:
            self.universe = 1
            self.address = int(str_repr)

    def __str__(self):
        return f"Universe: {self.universe}, Address: {self.address}"


class DmxValue:
    def __init__(self, str_repr):
        if str_repr == "None":
            self.value = None
            self.byte_count = None
        else:
            self.value = int(str_repr.split("/")[0])
            self.byte_count = int(str_repr.split("/")[1])

    def __str__(self):
        return f"Value: {self.value}, Byte count: {self.byte_count}"


class ColorCIE:
    def __init__(
        self,
        x: Union[float, None] = 0.3127,
        y: Union[float, None] = 0.3290,
        Y: Union[float, None] = 100.00,
        str_repr: Union[str, None] = None,
    ):
        self.x = x
        self.y = y
        self.Y = Y
        if str_repr is not None:
            try:
                self.x = float(str_repr.split(",")[0])
                self.y = float(str_repr.split(",")[1])
                self.Y = float(str_repr.split(",")[2])
            except:
                # Fail gracefully with default color (White)
                self.x = 0.3127
                self.y = 0.3290
                self.Y = 100.00

    def __str__(self):
        return f"{self.x}, {self.y}, {self.Y}"


class Rotation:
    def __init__(self, str_repr):
        str_repr = str_repr.replace("}{", ",")
        str_repr = str_repr.replace("{", "")
        str_repr = str_repr.replace("}", "")
        component = str_repr.split(",")
        component = [float(i) for i in component]
        self.matrix = [
            [component[0], component[1], component[2]],
            [component[3], component[4], component[5]],
            [component[6], component[7], component[8]],
        ]


class Vector3:
    def __init__(self, str_repr):
        if str_repr == "0" or str_repr == 0:
            self.vector3 = [0, 0, 0]
        else:
            str_repr = str_repr.replace("{", "")
            str_repr = str_repr.replace("}", "")
            self.vector3 = [float(i) for i in str_repr.split(",")]


class Matrix:
    def __init__(self, str_repr):
        if str_repr == "0" or str_repr == 0:
            self.matrix = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        else:
            str_repr = str_repr.replace("}{", ",")
            str_repr = str_repr.replace("{", "")
            str_repr = str_repr.replace("}", "")
            component = str_repr.split(",")
            component = [float(i) for i in component]
            self.matrix = [
                [component[0], component[1], component[2], component[3]],
                [component[4], component[5], component[6], component[7]],
                [component[8], component[9], component[10], component[11]],
                [component[12], component[13], component[14], component[15]],
            ]


# A node link represents a link to another node in the XML tree, starting from
# start_point and traversing the tree with a decimal-point notation in str_link.
# There isn't yet a standard for how start_point is formatted so the only useful
# feature of this type currently is the str_link. A typical use would be for
# specifying linked attributes. In this case, the str_link text itself is perfectly
# serviceable if all that is needed is the attribute name. For this reason, the
# str representation of the NodeLink will always give the raw str_link property.
class NodeLink:
    def __init__(self, start_point, str_link):
        self.start_point = start_point
        self.str_link = str_link

    def __str__(self):
        return str(self.str_link)


ColorSpaceDefinition = namedtuple("ColorSpaceDefinition", "r g b w")
