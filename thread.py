import threading

# DMX Data/Rendering Thread Lock
# This is used on DMX_Data.set_universe and DMX.render
# to handle concurrence between ArtNet and programmer
print('Creating lock');
DMX_Lock = threading.Lock()