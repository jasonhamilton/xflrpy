import unittest
from xflrpy import Client, exceptions
from xflrpy.foil import Foil
import pathlib
import os
from base_test import TestBase
import pytest

FOLDER = pathlib.Path(__file__).parent.resolve()

C = Client()


    

class TestFoilManager(unittest.TestCase, TestBase):

    def test_get_foil(self):
        C.foils.delete_all()
        f1a = C.foils.create_naca_foil(1111)
        f2a = C.foils.create_naca_foil(2222)
        
        f1b = C.foils['NACA 1111']
        assert type(f1b) == Foil
        assert f1a == f1b
        f2b = C.foils['NACA 2222']
        assert type(f2b) == Foil
        assert f2a == f2b

        with pytest.raises(KeyError) as e_info:
            C.foils['NACA3333']
        with pytest.raises(KeyError) as e_info:
            C.foils['']
        with pytest.raises(IndexError) as e_info:
            C.foils[10]
        
        assert len(C.foils) == 2
        f1a.delete()
        f2a.delete()
        f1b.delete()
        f2b.delete()
        assert len(C.foils) == 0
    
    def test_load_get_delete_foils(self):
        # an invalid path should throw an exception
        with pytest.raises(exceptions.InvalidFoilPathError) as e_info:
            C.foils.load('invalidfileasdf')
        with pytest.raises(exceptions.InvalidFoilPathError) as e_info:
            C.foils.load(['invalidfileasdf'])
        with pytest.raises(exceptions.InvalidFoilPathError) as e_info:
            C.foils.load(['invalidfileasdf','t'])
        with pytest.raises(exceptions.InvalidFoilPathError) as e_info:
            C.foils.load(['filedoesnotexist.dat',os.path.join(FOLDER,'Zone-21.dat')])

        # test valid foils are loaded
        C.foils.load([os.path.join(FOLDER,'Zone-21.dat'), os.path.join(FOLDER,'goe445.DAT')])
        assert len(C.foils) == 2

        # test get foil
        f1 = C.foils['Zone-21']
        f2 = C.foils['GOE 445 AIRFOIL']
        assert f1.name == 'Zone-21'
        assert f2.name == 'GOE 445 AIRFOIL'
        
        f1.delete()
        f2.delete()

        # Try to load a foil that does not exist
        with pytest.raises(exceptions.InvalidFoilPathError) as e_info:
            C.foils.load('invalidfileasdf')

        C.foils.load_folder(FOLDER)
        C.foils.delete_all()
    
    def test_create_naca_foil(self):
        # test with some valid foils first
        assert self._create_and_validate_thickness(1, 0.01)
        assert self._create_and_validate_thickness(1105, 0.05)
        assert self._create_and_validate_thickness(2515, 0.15)
        assert self._create_and_validate_thickness("1", 0.01)
        assert self._create_and_validate_thickness("1105", 0.05)
        assert self._create_and_validate_thickness("2515", 0.15)
        
        assert self._create_bad_foil(1) == False
        assert self._create_bad_foil(1000) == False
        assert self._create_bad_foil(9999) == False
        # bad foils
        assert self._create_bad_foil(-10)
        assert self._create_bad_foil('-10')
        assert self._create_bad_foil(0)
        assert self._create_bad_foil('0')
        assert self._create_bad_foil(10000)
        assert self._create_bad_foil('#') 

    
    def _create_and_validate_thickness(self, value, expected, max_diference = 0.0001):
        f = C.foils.create_naca_foil(value)
        res =  abs(f.thickness - expected) < max_diference
        f.delete()
        return res
    
    def _create_bad_foil(self, value):
        try:
            f = C.foils.create_naca_foil(value)
        except exceptions.InvalidNacaValueError:
            return True
        f.delete()
        return False





