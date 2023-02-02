from collections import namedtuple


# Data type that only allows a specific set of values, if given a value
# which is not permitted, the value will be set to the default
class Enum:
    permitted = []
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


class ColorCIE:
    def __init__(
        self, x: float = None, y: float = None, z: float = None, str_repr: str = None
    ):
        self.x = x
        self.y = y
        self.z = z
        if str_repr is not None:
            self.x = float(str_repr.split(",")[0])
            self.y = float(str_repr.split(",")[1])
            self.Y = float(str_repr.split(",")[2])


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
        else:
            str_repr = str_repr.replace("}{", ",")
            str_repr = str_repr.replace("{", "")
            str_repr = str_repr.replace("}", "")
            component = str_repr.split(",")
            component = [float(i) * 0.001 for i in component]
            self.matrix = [
                [component[0], component[1], component[2], 0],
                [component[3], component[4], component[5], 0],
                [component[6], component[7], component[8], 0],
                [component[9], component[10], component[11], 0],
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
