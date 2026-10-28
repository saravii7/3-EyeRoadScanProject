"""Contract tests with fake model outputs, not an accuracy evaluation."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
import numpy as np
from PIL import Image
from roadscan_detector import RoadDamageDetector

class Tensor:
    def __init__(self, data): self.data = data
    def cpu(self): return self
    def tolist(self): return self.data

class DetectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.weights = Path(self.tmp.name) / 'weights.pt'
        self.weights.touch()
        self.model = Mock()
        self.model.names = {0:'pothole',1:'longitudinal_crack',2:'transverse_crack',3:'alligator_crack'}
        self.yolo = Mock(return_value=self.model)
        self.patch = patch.dict('sys.modules', {'ultralytics':SimpleNamespace(YOLO=self.yolo)})
        self.patch.start()
        self.detector = RoadDamageDetector(self.weights)
        self.image = Image.new('RGB', (100, 80))
    def tearDown(self):
        self.patch.stop(); self.tmp.cleanup()
    def boxes(self, xy, cls, conf):
        self.model.predict.return_value=[SimpleNamespace(boxes=SimpleNamespace(xyxy=Tensor(xy),cls=Tensor(cls),conf=Tensor(conf)))]
    def test_multiple_boxes_and_reordered_semantic_mapping(self):
        self.boxes([[1,2,30,40],[10,20,80,70]], [0,2], [.87,.61])
        found=self.detector.detect_damage(self.image)
        self.assertEqual(found,[{'damage_code':'D40','bbox_xyxy':[1.,2.,30.,40.],'confidence':.87},{'damage_code':'D10','bbox_xyxy':[10.,20.,80.,70.],'confidence':.61}])
        json.dumps(found,allow_nan=False)
        self.detector.detect_damage(self.image)
        self.yolo.assert_called_once()
    def test_empty_detections(self):
        self.boxes([],[],[]);self.assertEqual(self.detector.detect_damage(self.image),[])
    def test_d_codes(self):
        self.model.names={0:'D00',1:'D10',2:'D20',3:'D40'}
        d=RoadDamageDetector(self.weights);self.boxes([[1,2,3,4]],[3],[.8])
        self.assertEqual(d.detect_damage(self.image)[0]['damage_code'],'D40')
    def test_reject_coco_or_duplicate_classes(self):
        for names in [{0:'person'}, {0:'D00',1:'D10',2:'D20',3:'D20'}]:
            self.model.names=names
            with self.assertRaises(ValueError):RoadDamageDetector(self.weights)
    def test_parameters_and_input_errors(self):
        for conf in [-.1,1.1,float('nan')]:
            with self.assertRaises(ValueError):self.detector.detect_damage(self.image,confidence=conf)
        with self.assertRaises(TypeError):self.detector.detect_damage(None)
        with self.assertRaises(FileNotFoundError):self.detector.detect_damage(Path(self.tmp.name)/'missing.jpg')
    def test_local_file_and_predict_options(self):
        path=Path(self.tmp.name)/'road.png';self.image.save(path)
        self.boxes([[1,2,3,4]],[0],[.5])
        self.detector.detect_damage(path,confidence=.4,iou=.6)
        args=self.model.predict.call_args.kwargs
        self.assertEqual((args['conf'],args['iou'],args['imgsz'],args['device']),(.4,.6,640,'cpu'))
        self.assertEqual(args['source'].size,(100,80))

if __name__=='__main__':unittest.main()
