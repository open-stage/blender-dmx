class Function:
    Dimmer = ['Dimmer']
    ColorAdd = [
        'ColorAdd_R',
        'ColorAdd_G',
        'ColorAdd_B',
        'ColorAdd_H',
        'ColorAdd_S',
        'ColorAdd_V'
    ]

Renderables = {
    k: getattr(Function,k) for k in dir(Function) if not k.startswith('__')
}