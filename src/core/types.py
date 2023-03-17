from bpy.types import Object
from typing import List, Tuple, Dict

Universe = int
Offset = Tuple[int]
BufferCoords = List[Tuple[int]]

Function = str

FixtureFnGeometryData = Tuple[Object, float]
FixtureFnData = List[FixtureFnGeometryData]
FixtureData = Dict[Function, FixtureFnData]

FunctionData = Dict[Function, float]
ChannelData = List[Tuple[Universe, Offset, float]]

ChannelMetadata = object
CustomPropertyChannel = object