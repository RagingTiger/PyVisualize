# -*- mode: python -*-

block_cipher = None
added_files = [
    ('media/python_dark.gif', 'media')
]

a = Analysis(['pyvisualize.py'],
             pathex=['/Users/TigerJ/CS/Projects/ORNL_CS/PyVisualize'],
             binaries=None,
             datas=added_files,
             hiddenimports=['Tkinter', 'FileDialog'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='PyVisualize',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='PyVisualize')
app = BUNDLE(coll,
             name='PyVisualize.app',
             icon='media/python_dark.icns',
             bundle_identifier=None,
             info_plist={
                'NSHighResolutionCapable': 'True',
                },
             )
