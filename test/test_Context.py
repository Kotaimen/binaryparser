# -*- coding : utf-8 -*-

import unittest
import pprint
import sys, os, os.path
sys.path.insert(0, '../src')

from binaryparser import *


class TestStructContext(unittest.TestCase):
    
    def testNameParents(self):
        p = StructContext()
        c = StructContext(name='Noname', parent=p)
        self.assertEquals(c.get_name(), 'Noname')
        self.assertEquals(c.__, p)
        self.assertEquals(c.get_parent(), p)
    
    def testAttributeAccess(self):
        c = StructContext()
        c['A'] = 1
        c['B'] = 'b'
        c['C'] = 'c'
        self.assertEquals(c.A, 1)
        self.assertEquals(c.B, 'b')
        self.assertEquals(c.C, 'c')
    
        self.assertRaises(AttributeError, self.BadAttribute)
        
    def BadAttribute(self):
        c = StructContext()
        c['A'] = 'foo'
        c.a    
        

class TestArrayContext(unittest.TestCase):
    
    def testNameParents(self):
        p = ArrayContext()
        c = ArrayContext(name='Noname', parent=p)
        self.assertEquals(c.get_name(), 'Noname')
        self.assertEquals(c.__, p)
        self.assertEquals(c.get_parent(), p)
        
class TestContext(unittest.TestCase):

    def testContext(self):
        root = StructContext('Root')
        root['Magic'] = 'MGCK'
        root['Head'] = StructContext('Header', root)
        root.Head['Width'] = 2048
        root.Head['Height'] = 4096
        root.Head['Depth'] = 8
        root['Body'] = StructContext('Body', root)
        root.Body['Size'] = 0
        root.Body['Data'] = ArrayContext('Data', root.Body)
        for n in range(15):
            data = StructContext('Foo', parent=root.Body.Data)
            data['Foo1'] = n
            data['Foo2'] = n * n
            if n % 2:
                data['Foo3'] = n * n * n
            root.Body.Data.append(data)
        pprint.pprint(root)
        pretty_print(root)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    