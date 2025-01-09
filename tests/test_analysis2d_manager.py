import unittest
from xflrpy import Client, exceptions
import pathlib
import os
from base_test import TestBase
import time
import pytest


FOLDER = pathlib.Path(__file__).parent.resolve()


class TestAnalysis2dManager(unittest.TestCase, TestBase):
    def test_create_analyze_get_delete_analysis(self):
        C = Client()
        C.foils.load(os.path.join(FOLDER, 'goe445.DAT'))
        foil = C.foils['GOE 445 AIRFOIL']
        analyses = foil.analyses
        assert len(analyses) == 0

        analysis = analyses.create()
        assert len(analyses) == 1

        # Make sure accessing empty analysis doesn't break it
        op_points = analysis.op_points
        params = analysis.parameters
        polar = analysis.polar
        print(op_points, params, polar)
        
        result = analysis.run_analysis(sequence=(0, 15, 0.25))
        op_points = analysis.op_points
        params = analysis.parameters
        polar = analysis.polar

        assert len(op_points) == 60
        assert len(result) == 60
        assert(len(analysis.polar) == 60)
        assert len(analyses) == 1

        analysis.delete()
        assert len(analyses) == 0

        # ENSURE CANNOT ACCESS ONCE DELETED
        with pytest.raises(exceptions.AnalysisDoesNotExistError) as e_info:
            print(analysis)
        # print(analysis)
        with pytest.raises(exceptions.AnalysisDoesNotExistError) as e_info:
            print(analysis.parameters)
        


    def test_create_multiple_analysis(self):
        C = Client()
        C.foils.load(os.path.join(FOLDER, 'goe445.DAT'))
        foil = C.foils['GOE 445 AIRFOIL']
        analyses = foil.analyses
        assert len(analyses) == 0

        for i in range(3):
            start = time.time()
            analysis = analyses.create(reynolds=(i+1)*10000)
            assert len(analyses) == i+1
            result = analysis.run_analysis(sequence=(0, 15, 0.25))
            op_points = analysis.op_points
            assert len(op_points) > 1
            assert len(result) > 1
            assert(len(analysis.polar) > 1)
            assert len(analyses) == i+1
            end = time.time()
            print(f"It took {(end - start):.2f}seconds!")
        
        for analysis in foil.analyses:
            analysis.delete()


