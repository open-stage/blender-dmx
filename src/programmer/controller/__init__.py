import bpy

class DMX_Programmer_Controller:

    @staticmethod
    def set_dimmer(context, value: float) -> None:
        core = context.scene.dmx.core
        core.engine.program(core.fixtures,{
            'Dimmer': value
        })
        core.engine.render(core)

    @staticmethod
    def on_dimmer(programmer, context) -> None:
        DMX_Programmer_Controller.set_dimmer(
            context,
            programmer.dimmer
        )
        
