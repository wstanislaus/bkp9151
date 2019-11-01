''' Unit tests for bkp9151.py '''
from __future__ import print_function

import unittest
import bkp9151
from serial import SerialException


def dummy_sendcmd(command):
    ''' Dummy sendcmd method for testing SCPI command generation '''
    return bytes('{0}\n'.format(command), 'utf-8')


class TestConnect(unittest.TestCase):
    ''' Test cases for the connect function '''

    def setUp(self):
        ''' Test setup '''
        self.bkp = bkp9151
        self.goodserial = '/dev/ttyUSB0'
        self.badserial = '/dev/null'

    def test_goodconnect(self):
        ''' Test to ensure our 'happy path' of a valid serial connection.
            Assumes self.goodserial is set to a valid serial device '''

        try:
            scpi_obj = self.bkp.connect(self.goodserial)
        except SerialException:
            print('\n!!!!!!! IMPORTANT !!!!!!!!\n',
                  'Skipped test: test_goodconnect because no device found\n'
                  '!!!!!!! IMPORTANT !!!!!!!!')
            return

        self.assertTrue(isinstance(scpi_obj, bkp9151.ScpiConnection))

    def test_badconnect(self):
        ''' Test to ensure our 'unhappy path' is producing the correct
            exception. Assumes self.badserial is set to an invalid
            serial device. '''
        with self.assertRaises(SerialException):
            self.bkp.connect(self.badserial)



class TestScpiConnection(unittest.TestCase):
    ''' Tests SCPI Connection object - specifically the command output '''

    def setUp(self):
        ''' Sets up our ScpiConnection object with sendcmd dummy object '''
        self.scpi = bkp9151.ScpiConnection(None, 100)
        self.scpi.sendcmd = dummy_sendcmd


if __name__ == '__main__':
    unittest.main()
