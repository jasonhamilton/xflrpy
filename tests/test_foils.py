import unittest
from xflrpy import Client, exceptions
from xflrpy.foil import Foil
import pathlib
import os
import math
from base_test import TestBase

FOLDER = pathlib.Path(__file__).parent.resolve()

C = Client()



# NEED TO MAKE SURE WE CAN UPDATE STATE FROM PARENT
class TestFoils(unittest.TestCase, TestBase):

    def test_duplicate_foil(self):
        C.foils.load(os.path.join(FOLDER,'goe445.DAT'))
        f1 = C.foils.get('GOE 445 AIRFOIL')
        f2 = f1.duplicate('GOE COPY')
        # make sure other foil was returned and properties match
        assert f2.name == 'GOE COPY'
        assert f1 == f2
        # check both exist on the server
        assert 'GOE COPY' in C.foils
        assert 'GOE 445 AIRFOIL' in C.foils

        # modify geometry and compare changes impact correct foil
        f1.set_geometry(thickness=0.15)
        f2.set_geometry(thickness=0.05)
        assert math.isclose(f1.thickness, 0.15, abs_tol=0.001)
        assert math.isclose(f2.thickness, 0.05, abs_tol=0.001)
        assert f1 != f2
        f1.delete()
        f2.delete()
    
    def test_rename_foil(self):
        C.foils.load(os.path.join(FOLDER,'goe445.DAT'))
        f1 = C.foils.get('GOE 445 AIRFOIL')
        f2 = f1.duplicate('GOE COPY')
        f2.rename('RENAMED')
        f2b = C.foils.get('RENAMED')

        assert f2.name == f2b.name
        assert f1 == f2
        assert f2 == f2b

        # validate expected foils on the client
        assert 'GOE 445 AIRFOIL' in C.foils
        assert 'GOE COPY' not in C.foils
        assert 'RENAMED' in C.foils

        # modify geometry and compare changes impact correct foil
        f1.set_geometry(thickness=0.15)
        f2.set_geometry(thickness=0.05)
        f2b._update()
        assert math.isclose(f1.thickness, 0.15, abs_tol=0.001)
        assert math.isclose(f2.thickness, 0.05, abs_tol=0.001)
        assert math.isclose(f2b.thickness, 0.05, abs_tol=0.001)
        assert f2 == f2b
        f1.delete()
        f2.delete()


    def test_foil_normalize(self):
        C.foils.load(os.path.join(FOLDER,'funky_foil.dat'))
        f1 = C.foils.get('Funky Foil')
        f2 = f1.duplicate('Funky Foil Copy')
        assert f1 == f2

        f2.normalize()
        assert f2.coordinates[0] == [1,0]
        assert f2.coordinates[-1] == [1,0]
        assert f1 != f2

        f1.delete()
        f2.delete()


    def test_foil_visibility(self):
        C.foils.load(os.path.join(FOLDER,'goe445.DAT'))
        f1 = C.foils.get('GOE 445 AIRFOIL')
        f2 = f1.duplicate('GOE COPY')
        f3 = f1.duplicate('GOE COPY2')

        assert f1.is_visible 
        assert f2.is_visible 
        assert f3.is_visible 

        f1.hide()
        f2.hide()
        assert not f1.is_visible 
        assert not f2.is_visible 
        assert f3.is_visible

        f1.show()
        f2.show()
        f3.hide()
        assert f1.is_visible 
        assert f2.is_visible 
        assert not f3.is_visible 

        C.foils.hide_all()
        assert not f1.is_visible 
        assert not f2.is_visible 
        assert not f3.is_visible 

        C.foils.show_all()
        assert f1.is_visible 
        assert f2.is_visible 
        assert f3.is_visible 

        f1.delete()
        f2.delete()
        f3.delete()


    def test_set_coordinates(self):
        C.foils.load(os.path.join(FOLDER,'goe445.DAT'))
        C.foils.load(os.path.join(FOLDER,'funky_foil.dat'))
        f1 = C.foils.get('GOE 445 AIRFOIL')
        f2 = C.foils.get('Funky Foil')
        f1_mod = f1.duplicate('GOE COPY')

        f1_mod.set_coordinates(f2.coordinates)

        assert f1 != f1_mod
        assert f1_mod == f2
        f1.delete()
        f2.delete()
        f1_mod.delete()

    def test_foil_export(self):
        fn = "export.dat"
        fp = os.path.join(FOLDER,fn)
        if os.path.exists(fp):
            os.remove(fp)
        C.foils.load(os.path.join(FOLDER,'goe445.dat'))
        f1 = C.foils.get('GOE 445 AIRFOIL')
        assert not os.path.exists(fp)
        f1.export(fp)
        assert os.path.exists(fp)
        f1.delete()

    def test_foil_derotate(self):
        C.foils.load(os.path.join(FOLDER,'funky_foil.dat'))
        f1 = C.foils.get('Funky Foil')
        f2 = f1.duplicate('Funky Foil Copy')
        assert f1 == f2
        f2.derotate()
        assert f1 != f2
        f1.delete()
        f2.delete()
    
    def test_to_dat(self):
        C.foils.load(os.path.join(FOLDER,'goe445.DAT'))
        f1 = C.foils.get('GOE 445 AIRFOIL')
        dat = f1.to_dat()
        assert f1.name in dat.split("\n")[0]
        assert len(dat.split("\n")) > len(f1.coordinates) 
        f1.delete()
        # assert False
