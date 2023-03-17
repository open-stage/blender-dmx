from lib import pygdtf
from typing import List, Dict, Any


def getValue(dmx_value, fine=False):
    if dmx_value.byte_count == 1:
        return dmx_value.value
    f = dmx_value.value / 255.0
    msb = int(f)
    if not fine:
        return msb
    lsb = int((f - msb) * 255)
    return lsb


def get_dmx_mode_by_name(gdtf_profile: 'pygdtf.FixtureType' = None, 
                         mode_name: str = None) -> 'pygdtf.DmxMode':
    """Find mode by name"""
    for mode in gdtf_profile.dmx_modes:
        if mode.name == mode_name:
            return mode
    return None


def get_geometry_by_name(gdtf_profile: 'pygdtf.FixtureType' = None, 
                         geometry_name: str = None) -> 'pygdtf.Geometry':
    """Recursively find a geometry of a given name"""

    def iterate_geometries(collector):
        if collector.name == geometry_name:
            matched.append(collector)
        for g in collector.geometries:
            if g.name == geometry_name:
                matched.append(g)
            if hasattr(g, "geometries"):
                iterate_geometries(g)

    matched: List['pygdtf.Geometry'] = []
    iterate_geometries(gdtf_profile)
    if matched:
        return matched[0]

    return None


def get_geometry_by_type(root_geometry: 'pygdtf.Geometry' = None, 
                         geometry_class: 'pygdtf.Geometry' = None) -> List['pygdtf.Geometry']:
    """Recursively find all geometries of a given type"""

    def iterate_geometries(collector):
        for g in collector.geometries:
            if type(g) == geometry_class:
                matched.append(g)
            if hasattr(g, "geometries"):
                iterate_geometries(g)

    matched: List['pygdtf.Geometry'] = []
    iterate_geometries(root_geometry)
    return matched


def get_model_by_name(gdtf_profile: 'pygdtf.FixtureType' = None, 
                      model_name: str = None) -> 'pygdtf.Model':
    """Find model by name"""
    for model in gdtf_profile.models:
        if model.name == model_name:
            return model

    return None


def get_channels_by_geometry(geometry_name: str = None, 
                             channels: List['pygdtf.DmxChannel'] = []) -> List['pygdtf.DmxChannel']:
    """Find channels for a given geometry"""
    matched: List['pygdtf.DmxChannel'] = []
    for channel in channels:
        if channel.geometry == geometry_name:
            matched.append(channel)

    return matched


def get_address_by_break(dmx_breaks: List['pygdtf.Break'] = [], 
                         value: int = 1) -> 'pygdtf.DmxAddress':
    """Return DMX address for a given DMX break"""
    for item in dmx_breaks:
        if item.dmx_break == value:
            return item.dmx_offset
    return None


def get_channels_for_geometry(gdtf_profile: 'pygdtf.FixtureType' = None, geometry: 'pygdtf.Geometry' = None, 
                              dmx_channels: List['pygdtf.DmxChannel'] = [], 
                              channel_list: List[Any] = []) -> List[Any]:
    """Get all channels for the device, recursively, starting from root geometry"""
    name = geometry.name

    if isinstance(geometry, pygdtf.GeometryReference):
        name = geometry.geometry

    for channel in get_channels_by_geometry(name, dmx_channels):
        channel_list.append((channel, geometry))
    if hasattr(geometry, "geometries"):
        for sub_geometry in geometry.geometries:
            channel_list = get_channels_for_geometry(
                gdtf_profile, sub_geometry, dmx_channels, channel_list
            )
    return channel_list


def get_virtual_channels(gdtf_profile: 'pygdtf.FixtureType' = None,
                         mode: str = None) -> List['Dict']:
    """Returns virtual channels"""

    dmx_mode = None
    dmx_mode = get_dmx_mode_by_name(gdtf_profile, mode)
    root_geometry = get_geometry_by_name(gdtf_profile, dmx_mode.geometry)
    device_channels = get_channels_for_geometry(
        gdtf_profile, root_geometry, dmx_mode.dmx_channels, []
    )

    virtual_channels: List[Dict[Any, Any]] = []

    for channel, geometry in device_channels:
        if channel.offset is None:
            virtual_channels.append({
            "id": str(channel.logical_channels[0].channel_functions[0].attribute),
            "default": getValue(
                channel.logical_channels[0].channel_functions[0].default
            ),
            "geometry": geometry.name,
        })
    return virtual_channels

def get_dmx_channels(gdtf_profile: 'pygdtf.FixtureType' = None, 
                     mode: str = None) -> List['Dict']:
    """Returns list of arrays, each array is one DMX Break,
    with DMX channels, defaults, geometries"""

    dmx_mode = None
    dmx_mode = get_dmx_mode_by_name(gdtf_profile, mode)
    root_geometry = get_geometry_by_name(gdtf_profile, dmx_mode.geometry)
    device_channels = get_channels_for_geometry(
        gdtf_profile, root_geometry, dmx_mode.dmx_channels, []
    )

    dmx_channels:List[Any] = []

    for channel, geometry in device_channels:
        if channel.offset is None:
            continue
        if len(dmx_channels) < channel.dmx_break:
            dmx_channels = dmx_channels + [[]] * (channel.dmx_break - len(dmx_channels))

        break_channels = dmx_channels[channel.dmx_break - 1]  # off by one...

        break_addition = 0

        if hasattr(geometry, "breaks"):
            dmx_offset = get_address_by_break(geometry.breaks, channel.dmx_break)
            if dmx_offset is not None:
                break_addition = dmx_offset.address - 1

        offset0 = channel.offset[0] + break_addition
        offset1 = 0
        # TODO: rework here to support ultra and uber

        if len(channel.offset) > 1:
            offset1 = channel.offset[1] + break_addition

        max_offset = max([offset0, offset1])

        if len(break_channels) < max_offset:
            # print(len(break_channels), break_channels)
            break_channels = break_channels + [
                {"dmx": "", "id": "", "default": 0, "geometry": "", "break": ""}
            ] * (max_offset - len(break_channels))

        break_channels[offset0 - 1] = {
            "dmx": offset0,
            "id": str(channel.logical_channels[0].channel_functions[0].attribute),
            "default": getValue(
                channel.logical_channels[0].channel_functions[0].default
            ),
            "geometry": geometry.name,
            "break": channel.dmx_break,
        }
        if offset1 > 0:
            break_channels[offset1 - 1] = {
                "dmx": offset1,
                "id": "+"
                + str(channel.logical_channels[0].channel_functions[0].attribute),
                "default": getValue(
                    channel.logical_channels[0].channel_functions[0].default, True
                ),
                "geometry": geometry.name,
                "break": channel.dmx_break,
            }
        dmx_channels[channel.dmx_break - 1] = break_channels

    # This returns multiple lists of channel arrays. Each list is for one DMX Break, these
    # can be patched onto different DMX addresses. Or, these lists can be flatten into one
    # DMX footprint this way:
    # [channel for break_channels in dmx_channels for channel in break_channels]
    # Here, we should return the list of arrays, so the consumer can decide how to process it.
    return dmx_channels
