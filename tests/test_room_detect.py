import unittest

import numpy as np

from room import detect

# ── Fakes mimicking the ultralytics YOLO/SAM result shape, so detect_screens()
# is testable without the real (torch-heavy) models installed. ─────────────────

class _FakeTensor:
    def __init__(self, arr):
        self._arr = np.asarray(arr, dtype="float32")

    def cpu(self):
        return self

    def numpy(self):
        return self._arr


class _FakeBox:
    def __init__(self, cls_id, xyxy):
        self._cls_id = cls_id
        self._xyxy = xyxy

    @property
    def cls(self):
        return [self._cls_id]

    @property
    def xyxy(self):
        return [_FakeTensor(self._xyxy)]


class _FakeDetectionResult:
    def __init__(self, boxes, names):
        self.boxes = boxes
        self.names = names


class _FakeYOLO:
    def __init__(self, boxes, names):
        self._boxes = boxes
        self._names = names

    def predict(self, frame, conf=0.25, verbose=False):
        return [_FakeDetectionResult(self._boxes, self._names)]


class _FakeMasksContainer:
    def __init__(self, mask_arr):
        self.data = [_FakeTensor(mask_arr)] if mask_arr is not None else []


class _FakeSAMResult:
    def __init__(self, mask_arr):
        self.masks = _FakeMasksContainer(mask_arr) if mask_arr is not None else None


class _FakeSAM:
    """mask_arr, if given, is returned for every box; None simulates SAM finding nothing."""
    def __init__(self, mask_arr):
        self._mask_arr = mask_arr

    def predict(self, image, points, labels, verbose=False):
        return [_FakeSAMResult(self._mask_arr)]


def _filled_mask(shape, y1, y2, x1, x2):
    mask = np.zeros(shape, dtype="uint8")
    mask[y1:y2, x1:x2] = 1
    return mask


class TestOrderCorners(unittest.TestCase):
    def test_orders_scrambled_points_tl_tr_br_bl(self):
        # Deliberately out of order: bl, tr, tl, br
        pts = np.array([[0, 100], [100, 0], [0, 0], [100, 100]], dtype="float32")
        ordered = detect.order_corners(pts)
        tl, tr, br, bl = ordered
        np.testing.assert_array_equal(tl, [0, 0])
        np.testing.assert_array_equal(tr, [100, 0])
        np.testing.assert_array_equal(br, [100, 100])
        np.testing.assert_array_equal(bl, [0, 100])


class TestMaskToCorners(unittest.TestCase):
    def test_finds_four_corners_of_a_filled_rectangle(self):
        mask = _filled_mask((200, 200), 20, 180, 20, 180)
        corners = detect.mask_to_corners(mask)
        self.assertIsNotNone(corners)
        self.assertEqual(corners.shape, (4, 2))

    def test_empty_mask_returns_none(self):
        mask = np.zeros((200, 200), dtype="uint8")
        self.assertIsNone(detect.mask_to_corners(mask))

    def test_tiny_mask_below_area_threshold_returns_none(self):
        mask = _filled_mask((200, 200), 0, 5, 0, 5)  # 5x5 = 25px^2, well under the 200 threshold
        self.assertIsNone(detect.mask_to_corners(mask))


class TestFlattenQuad(unittest.TestCase):
    def test_produces_expected_output_size(self):
        image = np.zeros((200, 200, 3), dtype="uint8")
        corners = np.array([[20, 20], [120, 20], [120, 120], [20, 120]], dtype="float32")
        warped = detect.flatten_quad(image, corners)
        self.assertEqual(warped.shape[:2], (100, 100))


class TestRawCrop(unittest.TestCase):
    def test_crops_expected_region(self):
        image = np.arange(200 * 200 * 3, dtype="uint8").reshape(200, 200, 3)
        box = np.array([10, 20, 60, 80], dtype="float32")
        cropped = detect.raw_crop(image, box)
        self.assertEqual(cropped.shape[:2], (60, 50))  # (y2-y1, x2-x1)

    def test_clamps_out_of_bounds_box(self):
        image = np.zeros((100, 100, 3), dtype="uint8")
        box = np.array([-50, -50, 500, 500], dtype="float32")
        cropped = detect.raw_crop(image, box)
        self.assertEqual(cropped.shape[:2], (100, 100))


class TestDetectScreens(unittest.TestCase):
    def setUp(self):
        self.names = {0: "person", 1: "laptop", 2: "chair", 3: "tv"}
        self.frame = np.zeros((300, 300, 3), dtype="uint8")

    def test_filters_to_screen_classes_only(self):
        boxes = [
            _FakeBox(0, [10, 10, 50, 50]),   # person — excluded
            _FakeBox(1, [60, 60, 150, 150]), # laptop — included
            _FakeBox(2, [10, 200, 50, 250]), # chair — excluded
            _FakeBox(3, [160, 10, 290, 150]),  # tv — included
        ]
        good_mask = _filled_mask((300, 300), 0, 300, 0, 300)
        yolo = _FakeYOLO(boxes, self.names)
        sam = _FakeSAM(good_mask)

        results = detect.detect_screens(self.frame, yolo=yolo, sam=sam)

        self.assertEqual(len(results), 2)
        self.assertEqual({r["class_name"] for r in results}, {"laptop", "tv"})

    def test_happy_path_produces_warped_image(self):
        boxes = [_FakeBox(1, [60, 60, 150, 150])]
        good_mask = _filled_mask((300, 300), 60, 150, 60, 150)
        yolo = _FakeYOLO(boxes, self.names)
        sam = _FakeSAM(good_mask)

        results = detect.detect_screens(self.frame, yolo=yolo, sam=sam)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["method"], "warped")
        self.assertIsNotNone(results[0]["corners"])
        self.assertGreater(results[0]["image"].size, 0)

    def test_falls_back_to_raw_crop_when_sam_finds_nothing(self):
        boxes = [_FakeBox(1, [60, 60, 150, 150])]
        yolo = _FakeYOLO(boxes, self.names)
        sam = _FakeSAM(None)  # SAM finds no mask at all

        results = detect.detect_screens(self.frame, yolo=yolo, sam=sam)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["method"], "raw_crop")
        self.assertIsNone(results[0]["corners"])
        self.assertEqual(results[0]["image"].shape[:2], (90, 90))  # 150-60, 150-60

    def test_falls_back_to_raw_crop_when_corners_cannot_be_found(self):
        boxes = [_FakeBox(1, [60, 60, 150, 150])]
        # Mask has content, but none of it lands inside the box after clipping,
        # so mask_to_corners sees an empty contour set -> None.
        empty_in_box_mask = _filled_mask((300, 300), 0, 10, 0, 10)
        yolo = _FakeYOLO(boxes, self.names)
        sam = _FakeSAM(empty_in_box_mask)

        results = detect.detect_screens(self.frame, yolo=yolo, sam=sam)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["method"], "raw_crop")

    def test_no_screens_detected_returns_empty_list(self):
        boxes = [_FakeBox(0, [10, 10, 50, 50])]  # only a person
        yolo = _FakeYOLO(boxes, self.names)
        sam = _FakeSAM(None)

        results = detect.detect_screens(self.frame, yolo=yolo, sam=sam)
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
