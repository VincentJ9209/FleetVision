from fleetvision.vision.compare_damage import calculate_iou


def test_iou_identical_boxes():
    assert calculate_iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0


def test_iou_no_overlap():
    assert calculate_iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0.0
