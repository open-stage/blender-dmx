import os
from types import SimpleNamespace as SN
import requests

fixture_files = [
    SN(
        name="Ayrton@Argo_6_FX@V1.1_First_Release.gdtf",
        url="https://github.com/user-attachments/files/16462386/Ayrton%40Argo_6_FX%40V1.1_First_Release.zip",
        reason="glb files are scaled differently",
    ),
    SN(
        name="Cameo@Evos_W7@Firmware-1.4_GDTF-1.2.gdtf",
        url="https://github.com/user-attachments/files/16462384/Cameo%40Evos_W7%40Firmware-1.4_GDTF-1.2.zip",
        reason="3DS files",
    ),
    SN(
        name="Chauvet_Professional@Maverick_Storm_2_Profile@Rev_1.0.4.gdtf",
        url="https://github.com/open-stage/blender-dmx/files/13418605/Chauvet_Professional%40Maverick_Storm_2_Profile%40Rev_1.0.4.zip",
        reason="3D visual issue, Multipart model",
    ),
    SN(
        name="Anolis@Calumma_S_SC@not_applied_models.gdtf",
        url="https://github.com/open-stage/blender-dmx/files/13418886/Anolis%40Calumma_S_SC%40not_applied_models.zip",
        reason="3D visual issue, Not applied transforms",
    ),
    SN(
        name="BlenderDMX@LED_PAR_64_RGBW@v0.3.zip",
        url="https://github.com/user-attachments/files/16461350/BlenderDMX%40LED_PAR_64_RGBW%40v0.3.zip",
        reason="One of the scaling dimensions is zero, producing division by 0",
    ),
    SN(
        name="Martin_Professional@ERA_400_Performance_CLD@20230226.zip",
        url="https://github.com/open-stage/blender-dmx/files/13853506/Martin_Professional%40ERA_400_Performance_CLD%4020230226.zip",
        reason="3D visual issue, Has legs not joined to the model of base",
    ),
    SN(
        name="Clay_Paky@Axcor_Beam_300@Claypaky_Official_File_Fw_V5.0.zip",
        url="https://github.com/open-stage/blender-dmx/files/13853520/Clay_Paky%40Axcor_Beam_300%40Claypaky_Official_File_Fw_V5.0.zip",
        reason="3D visual issue",
    ),
]


def get_files():
    addon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.chdir(addon_path)
    profiles_path = os.path.join(addon_path, "assets", "profiles")

    for fixture_file in fixture_files:
        print("Downloading", fixture_file.name)
        r = requests.get(fixture_file.url)
        path = os.path.join(profiles_path, fixture_file.name)
        with open(path, "wb") as f:
            f.write(r.content)


if __name__ == "__main__":
    get_files()
