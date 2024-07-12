from typing import List, Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element


# Data type that only allows a specific set of values, if given a value
# which is not permitted, the value will be set to the default
class Enum:
    permitted: List[str] = []
    _default = None

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


class Color:
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

    def to_xml(self, root):
        element = ElementTree.SubElement(root, type(self).__name__)
        element.text = f"{self.x},{self.y},{self.Y}"


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


class Matrix:
    def __init__(self, str_repr):
        if str_repr == "0" or str_repr == 0:
            self.matrix = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 0]]
        elif isinstance(str_repr, list):
            self.matrix = str_repr
        else:
            str_repr = str_repr.replace("}{", ",")
            str_repr = str_repr.replace("{", "")
            str_repr = str_repr.replace("}", "")
            component = str_repr.split(",")
            component = [float(i) for i in component]
            self.matrix = [
                [component[0], component[1], component[2], 0],
                [component[3], component[4], component[5], 0],
                [component[6], component[7], component[8], 0],
                [component[9] * 0.001, component[10] * 0.001, component[11] * 0.001, 0],
            ]
            # TODO: the matrix down-scaling should not be done here but in the consumer, based on scaling settings and so on
            # same below, where we up-scale it again as mere re-processing via pymvr will cause loss of precision
            # another option is to have a global settings for the GeneralSceneDescription but we then must pass the GSD class
            # down through the hierarchy all the way to the Matrix class

    def __eq__(self, other):
        return self.matrix == other.matrix

    def __ne__(self, other):
        return self.matrix == other.matrix

    def __str__(self):
        return f"{self.matrix}"

    def __repr__(self):
        return f"{self.matrix}"

    def to_xml(self, parent):
        u, v, w, x = self.matrix
        matrix_str = f"{{{u[0]},{u[1]},{u[2]}}}{{{v[0]},{v[1]},{v[2]}}}{{{w[0]},{w[1]},{w[2]}}}{{{x[0]/0.001},{x[1]/0.001},{x[2]/0.001}}}"
        matrix = ElementTree.SubElement(parent, type(self).__name__)
        matrix.text = matrix_str


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
