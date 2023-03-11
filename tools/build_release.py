import re
import os
import shutil
from distutils.dir_util import copy_tree
from pygit2 import Repository

BUILD_DIR = 'build'

branch_name = Repository('.').head.shorthand
if (branch_name == None):
    raise Exception('Run the script from the project root.')

branch_name = 'master'

release_name = branch_name
if (re.match(r'^release_v\d+\.\d+\.\d+$', branch_name)):
    print('Warning: This is not a release branch. The branch should be named "release_vX.Y.Z".')
    release_name = branch_name[8:]

zip_name = 'blenderDMX_' + release_name

print('---------')
print('branch name: ' + branch_name)
print('release name: ' + release_name)
print('zip name: ' + zip_name + '.zip')
print('---------')

print('Resetting build directory...')
if (os.path.exists(BUILD_DIR)):
    shutil.rmtree(BUILD_DIR)
os.mkdir(BUILD_DIR)
os.mkdir(BUILD_DIR+'/dmx')

print('Copying dependencies to build directory...')
copy_tree('assets', BUILD_DIR+'/dmx/assets')
copy_tree('io_scene_3ds', BUILD_DIR+'/dmx/io_scene_3ds')
copy_tree('panels', BUILD_DIR+'/dmx/panels')
copy_tree('pygdtf', BUILD_DIR+'/dmx/pygdtf')
copy_tree('pymvr', BUILD_DIR+'/dmx/pymvr')
copy_tree('sacn', BUILD_DIR+'/dmx/sacn')

print('Copying source to build directory...')
for filename in os.listdir('.'):
    if filename.endswith('.py'):
        shutil.copy2(filename, BUILD_DIR+'/dmx')

print('Copying metadata to build directory...')
shutil.copy2('CHANGELOG.md', BUILD_DIR+'/dmx')
shutil.copy2('LICENSE', BUILD_DIR+'/dmx')

print('Zipping release...')
shutil.make_archive(zip_name, 'zip', BUILD_DIR)

print('Clearing build directory...')
shutil.rmtree(BUILD_DIR)

print('Build successfull! Have a great release!')