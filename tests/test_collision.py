from __future__ import annotations

import unittest

from smalloldgames.engine.collision import AABB, SpatialHash, aabb_overlaps, aabb_overlaps_raw, covered_cells


class AABBOverlapsTests(unittest.TestCase):
    def test_overlapping(self) -> None:
        a = AABB(0, 0, 10, 10)
        b = AABB(5, 5, 10, 10)
        self.assertTrue(aabb_overlaps(a, b))

    def test_separated_x(self) -> None:
        a = AABB(0, 0, 10, 10)
        b = AABB(20, 0, 10, 10)
        self.assertFalse(aabb_overlaps(a, b))

    def test_separated_y(self) -> None:
        a = AABB(0, 0, 10, 10)
        b = AABB(0, 20, 10, 10)
        self.assertFalse(aabb_overlaps(a, b))

    def test_edge_touching_is_not_overlap(self) -> None:
        a = AABB(0, 0, 10, 10)
        b = AABB(10, 0, 10, 10)
        self.assertFalse(aabb_overlaps(a, b))

    def test_contained(self) -> None:
        outer = AABB(0, 0, 20, 20)
        inner = AABB(5, 5, 5, 5)
        self.assertTrue(aabb_overlaps(outer, inner))


class AABBOverlapsRawTests(unittest.TestCase):
    def test_matches_object_version(self) -> None:
        cases = [
            ((0, 0, 10, 10, 5, 5, 10, 10), True),
            ((0, 0, 10, 10, 20, 0, 10, 10), False),
            ((0, 0, 10, 10, 10, 0, 10, 10), False),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                self.assertEqual(aabb_overlaps_raw(*args), expected)


class CoveredCellsTests(unittest.TestCase):
    def test_single_cell(self) -> None:
        cells = covered_cells(5.0, 5.0, 1.0, 1.0, 10.0)
        self.assertEqual(cells, [(0, 0)])

    def test_spans_multiple_cells(self) -> None:
        cells = covered_cells(8.0, 8.0, 4.0, 4.0, 10.0)
        self.assertIn((0, 0), cells)
        self.assertIn((1, 1), cells)

    def test_negative_coords(self) -> None:
        cells = covered_cells(-5.0, -5.0, 1.0, 1.0, 10.0)
        self.assertEqual(cells, [(-1, -1)])


class SpatialHashTests(unittest.TestCase):
    def test_insert_and_query(self) -> None:
        sh = SpatialHash(10.0)
        sh.insert(1, 5.0, 5.0, 4.0, 4.0)
        sh.insert(2, 50.0, 50.0, 4.0, 4.0)
        result = sh.query(3.0, 3.0, 8.0, 8.0)
        self.assertIn(1, result)
        self.assertNotIn(2, result)

    def test_query_empty_region(self) -> None:
        sh = SpatialHash(10.0)
        sh.insert(1, 0.0, 0.0, 5.0, 5.0)
        result = sh.query(100.0, 100.0, 5.0, 5.0)
        self.assertEqual(result, set())

    def test_clear(self) -> None:
        sh = SpatialHash(10.0)
        sh.insert(1, 0.0, 0.0, 5.0, 5.0)
        sh.clear()
        result = sh.query(0.0, 0.0, 10.0, 10.0)
        self.assertEqual(result, set())

    def test_large_entity_spans_multiple_cells(self) -> None:
        sh = SpatialHash(10.0)
        sh.insert(1, 0.0, 0.0, 25.0, 25.0)
        # Should be findable from any cell it covers
        result = sh.query(20.0, 20.0, 1.0, 1.0)
        self.assertIn(1, result)


if __name__ == "__main__":
    unittest.main()
