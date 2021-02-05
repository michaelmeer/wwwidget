import unittest
A_BLINK = 524288
A_BOLD = 2097152
A_REVERSE = 262144
A_STANDOUT = 65536
A_DIM = 1048576
A_UNDERLINE = 131072

class CursesConstantsTestCase(unittest.TestCase):
    def setUp(self):
        scr = curses.initscr()

    def test_A_BLINK(self):
        self.assertEqual(A_BLINK, curses.A_BLINK)

    def test_A_BOLD(self):
        self.assertEqual(A_BOLD, curses.A_BOLD)

    def test_A_DIM(self):
        self.assertEqual(A_DIM, curses.A_DIM)

    def test_A_REVERSE(self):
        self.assertEqual(A_REVERSE, curses.A_REVERSE)

    def test_A_STANDOUT(self):
        self.assertEqual(A_STANDOUT, curses.A_STANDOUT)

    def test_A_UNDERLINE(self):
        self.assertEqual(A_UNDERLINE, curses.A_UNDERLINE)


if __name__ == '__main__':
    import curses
    curses.wrapper(unittest.main())
