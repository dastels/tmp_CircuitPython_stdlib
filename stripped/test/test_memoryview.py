"""Unit tests for the memoryview

   Some tests are in test_bytes. Many tests that require _testbuffer.ndarray
   are in test_buffer.
"""

import unittest
import test.support
import sys
import array
import io


class AbstractMemoryTests:
    source_bytes = b"abcdef"

    @property
    def _source(self):
        return self.source_bytes

    @property
    def _types(self):
        return filter(None, [self.ro_type, self.rw_type])

    def check_getitem_with_type(self, tp):
        b = tp(self._source)
        m = self._view(b)
        self.assertEqual(m[0], ord(b"a"))
        self.assertIsInstance(m[0], int)
        self.assertEqual(m[5], ord(b"f"))
        self.assertEqual(m[-1], ord(b"f"))
        self.assertEqual(m[-6], ord(b"a"))
        # Bounds checking
        self.assertRaises(IndexError, lambda: m[6])
        self.assertRaises(IndexError, lambda: m[-7])
        self.assertRaises(IndexError, lambda: m[sys.maxsize])
        self.assertRaises(IndexError, lambda: m[-sys.maxsize])
        # Type checking
        self.assertRaises(TypeError, lambda: m[None])
        self.assertRaises(TypeError, lambda: m[0.0])
        self.assertRaises(TypeError, lambda: m["a"])
        m = None

    def test_getitem(self):
        for tp in self._types:
            self.check_getitem_with_type(tp)

    def test_iter(self):
        for tp in self._types:
            b = tp(self._source)
            m = self._view(b)
            self.assertEqual(list(m), [m[i] for i in range(len(m))])

    def test_setitem_readonly(self):
        if not self.ro_type:
            self.skipTest("no read-only type to test")
        b = self.ro_type(self._source)
        m = self._view(b)
        def setitem(value):
            m[0] = value
        self.assertRaises(TypeError, setitem, b"a")
        self.assertRaises(TypeError, setitem, 65)
        self.assertRaises(TypeError, setitem, memoryview(b"a"))
        m = None

    def test_setitem_writable(self):
        if not self.rw_type:
            self.skipTest("no writable type to test")
        tp = self.rw_type
        b = self.rw_type(self._source)
        m = self._view(b)
        m[0] = ord(b'1')
        self._check_contents(tp, b, b"1bcdef")
        m[0:1] = tp(b"0")
        self._check_contents(tp, b, b"0bcdef")
        m[1:3] = tp(b"12")
        self._check_contents(tp, b, b"012def")
        m[1:1] = tp(b"")
        self._check_contents(tp, b, b"012def")
        m[:] = tp(b"abcdef")
        self._check_contents(tp, b, b"abcdef")

        # Overlapping copies of a view into itself
        m[0:3] = m[2:5]
        self._check_contents(tp, b, b"cdedef")
        m[:] = tp(b"abcdef")
        m[2:5] = m[0:3]

        def setitem(key, value):
            m[key] = tp(value)
        # Bounds checking
        self.assertRaises(IndexError, setitem, 6, b"a")
        self.assertRaises(IndexError, setitem, -7, b"a")
        self.assertRaises(IndexError, setitem, sys.maxsize, b"a")
        self.assertRaises(IndexError, setitem, -sys.maxsize, b"a")
        # Wrong index/slice types
        self.assertRaises(TypeError, setitem, 0.0, b"a")
        self.assertRaises(TypeError, setitem, (0,), b"a")
        self.assertRaises(TypeError, setitem, (slice(0,1,1), 0), b"a")
        self.assertRaises(TypeError, setitem, (0, slice(0,1,1)), b"a")
        self.assertRaises(TypeError, setitem, (0,), b"a")
        self.assertRaises(TypeError, setitem, "a", b"a")

    def test_delitem(self):
        for tp in self._types:
            b = tp(self._source)
            m = self._view(b)
            with self.assertRaises(TypeError):
                del m[1]
            with self.assertRaises(TypeError):
                del m[1:4]

    def test_compare(self):
        # memoryviews can compare for equality with other objects
        # having the buffer interface.
        for tp in self._types:
            m = self._view(tp(self._source))
            for tp_comp in self._types:
                self.assertTrue(m == tp_comp(b"abcdef"))
                self.assertFalse(m != tp_comp(b"abcdef"))
                self.assertFalse(m == tp_comp(b"abcde"))
                self.assertTrue(m != tp_comp(b"abcde"))
                self.assertFalse(m == tp_comp(b"abcde1"))
                self.assertTrue(m != tp_comp(b"abcde1"))
            self.assertTrue(m == m)
            self.assertTrue(m == m[:])
            self.assertTrue(m[0:6] == m[:])
            self.assertFalse(m[0:5] == m)

            # Comparison with objects which don't support the buffer API
            self.assertFalse(m == "abcdef")
            self.assertTrue(m != "abcdef")
            self.assertFalse("abcdef" == m)
            self.assertTrue("abcdef" != m)

            # Unordered comparisons
            for c in (m, b"abcdef"):
                self.assertRaises(TypeError, lambda: m < c)
                self.assertRaises(TypeError, lambda: m >= c)

    def check_attributes_with_type(self, tp):
        m = self._view(tp(self._source))
        self.assertEqual(len(m), 6)
        return m

    def test_getbuffer(self):
        # Test PyObject_GetBuffer() on a memoryview object.
        for tp in self._types:
            b = tp(self._source)
            m = self._view(b)
            s = str(m, "utf-8")
            self._check_contents(tp, b, s.encode("utf-8"))

    def _check_released(self, m, tp):
        check = self.assertRaisesRegex(ValueError, "released")
        with check: bytes(m)
        with check: m[0]
        with check: m[0] = b'x'
        with check: len(m)
        with check:
            with m:
                pass
        # str() and repr() still function
        self.assertIn("released memory", str(m))
        self.assertIn("released memory", repr(m))
        self.assertEqual(m, m)
        self.assertNotEqual(m, memoryview(tp(self._source)))
        self.assertNotEqual(m, tp(self._source))

    def test_writable_readonly(self):
        # Issue #10451: memoryview incorrectly exposes a readonly
        # buffer as writable causing a segfault if using mmap
        tp = self.ro_type
        if tp is None:
            self.skipTest("no read-only type to test")
        b = tp(self._source)
        m = self._view(b)
        i = io.BytesIO(b'ZZZZ')
        self.assertRaises(TypeError, i.readinto, m)

    def test_getbuf_fail(self):
        self.assertRaises(TypeError, self._view, {})


# Variations on source objects for the buffer: bytes-like objects, then arrays
# with itemsize > 1.
# NOTE: support for multi-dimensional objects is unimplemented.

class BaseBytesMemoryTests(AbstractMemoryTests):
    ro_type = bytes
    rw_type = bytearray
    getitem_type = bytes
    itemsize = 1
    format = 'B'

class BaseArrayMemoryTests(AbstractMemoryTests):
    ro_type = None
    rw_type = lambda self, b: array.array('i', list(b))
    getitem_type = lambda self, b: array.array('i', list(b)).tobytes()
    import struct                                                               ###
    itemsize = struct.calcsize('i')                                             ###
    format = 'i'

    @unittest.skip('XXX test should be adapted for non-byte buffers')
    def test_getbuffer(self):
        pass

    @unittest.skip('XXX NotImplementedError: tolist() only supports byte views')
    def test_tolist(self):
        pass


# Variations on indirection levels: memoryview, slice of memoryview,
# slice of slice of memoryview.
# This is important to test allocation subtleties.

class BaseMemoryviewTests:
    def _view(self, obj):
        return memoryview(obj)

    def _check_contents(self, tp, obj, contents):
        self.assertEqual(obj, tp(contents))

class BaseMemorySliceTests:
    source_bytes = b"XabcdefY"

    def _view(self, obj):
        m = memoryview(obj)
        return m[1:7]

    def _check_contents(self, tp, obj, contents):
        self.assertEqual(obj[1:7], tp(contents))

class BaseMemorySliceSliceTests:
    source_bytes = b"XabcdefY"

    def _view(self, obj):
        m = memoryview(obj)
        return m[:7][1:]

    def _check_contents(self, tp, obj, contents):
        self.assertEqual(obj[1:7], tp(contents))


# Concrete test classes

class BytesMemoryviewTest(unittest.TestCase,
    BaseMemoryviewTests, BaseBytesMemoryTests):

    def test_constructor(self):
        for tp in self._types:
            ob = tp(self._source)
            self.assertTrue(memoryview(ob))
            self.assertRaises(TypeError, memoryview)
            self.assertRaises(TypeError, memoryview, ob, ob)

class ArrayMemoryviewTest(unittest.TestCase,
    BaseMemoryviewTests, BaseArrayMemoryTests):

    def test_array_assign(self):
        # Issue #4569: segfault when mutating a memoryview with itemsize != 1
        a = array.array('i', range(10))
        m = memoryview(a)
        new_a = array.array('i', range(9, -1, -1))
        m[:] = new_a
        self.assertEqual(a, new_a)


class BytesMemorySliceTest(unittest.TestCase,
    BaseMemorySliceTests, BaseBytesMemoryTests):
    pass

class ArrayMemorySliceTest(unittest.TestCase,
    BaseMemorySliceTests, BaseArrayMemoryTests):
    pass

class BytesMemorySliceSliceTest(unittest.TestCase,
    BaseMemorySliceSliceTests, BaseBytesMemoryTests):
    pass

class ArrayMemorySliceSliceTest(unittest.TestCase,
    BaseMemorySliceSliceTests, BaseArrayMemoryTests):
    pass


