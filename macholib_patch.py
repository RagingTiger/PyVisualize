"""
Attribution:
    Neapolitan, Wed Oct 05 2016, SGB, "py2app TypeError: dyld_find() got an
    unexpected keyword argument 'loader'", Jul 6 '15 at 7:30,
    http://stackoverflow.com/a/37794490/6926917

Usage:
    Monkey-patch macholib to fix "dyld_find() got an unexpected keyword
    argument 'loader'".

    Add 'import macholib_patch' to the top of set_py2app.py
"""

import macholib
#print("~"*60 + "macholib verion: "+macholib.__version__)
if macholib.__version__ <= "1.7":
    print("Applying macholib patch...")
    import macholib.dyld
    import macholib.MachOGraph
    dyld_find_1_7 = macholib.dyld.dyld_find
    def dyld_find(name, loader=None, **kwargs):
        #print("~"*60 + "calling alternate dyld_find")
        if loader is not None:
            kwargs['loader_path'] = loader
        return dyld_find_1_7(name, **kwargs)
    macholib.MachOGraph.dyld_find = dyld_find
