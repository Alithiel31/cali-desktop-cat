"""Tests du pont entre les fenêtres natives et les surfaces du chat."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from desktopcat.screens import ScreenInfo, build_floors
from desktopcat.surfaces import Surface
from desktopcat.winapi import WinInfo
from desktopcat.world import build_surfaces, window_geometry


class WorldTest(unittest.TestCase):
    def setUp(self):
        self.screens = [ScreenInfo((0, 0, 1000, 800), (0, 0, 1000, 760), 1.0)]
        self.works = [self.screens[0].work]
        self.floors = build_floors(self.works)

    def test_window_geometry_converts_native_rect_and_respects_setting(self):
        def get_rect(_hwnd):
            return (100, 120, 500, 500)

        self.assertEqual(window_geometry(7, self.screens, True, get_rect), (120, 100, 500))
        self.assertIsNone(window_geometry(7, self.screens, False, get_rect))
        self.assertIsNone(window_geometry(7, self.screens, True, lambda _hwnd: None))

    def test_build_surfaces_converts_windows_and_always_includes_floors(self):
        windows = [WinInfo(7, "Éditeur", (100, 300, 600, 700), False)]
        def list_windows(exclude=()):
            return [window for window in windows if window.hwnd not in exclude]

        surfaces = build_surfaces(self.screens, self.works, self.floors, True, {7}, 40, 80, list_windows)
        self.assertEqual(surfaces, [Surface(None, 760, 0, 1000, 0, "sol", floor=0)])

        surfaces = build_surfaces(self.screens, self.works, self.floors, True, set(), 40, 80, list_windows)
        self.assertTrue(any(surface.hwnd == 7 for surface in surfaces))
        self.assertTrue(any(surface.hwnd is None for surface in surfaces))

    def test_disabled_perching_skips_window_enumeration(self):
        def unexpected_scan(**_kwargs):
            raise AssertionError("les fenêtres ne doivent pas être lues quand le perchage est désactivé")

        surfaces = build_surfaces(self.screens, self.works, self.floors, False, (), 40, 80, unexpected_scan)
        self.assertEqual(len(surfaces), 1)
        self.assertIsNone(surfaces[0].hwnd)


if __name__ == "__main__":
    unittest.main()
