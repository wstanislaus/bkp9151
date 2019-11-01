bkp9151
=======
bkp9151 is a self-contained SCPI "driver" library for the BK Precision 9151 Single Output Programmable DC Power Supply. It provides a pythonic interface to all of the documented SCPI commands in the manual.

Serial communication is handled by the pyserial library (http://pyserial.sourceforge.net/)

- Comma-separated results are contained inside a tuple
- All scientific notation values are returned as floats
- 'ON' 'OFF' values are returned as a boolean
- Integer values are returned as integers
- N or '----' values are returned as a None type
- Everything else is returned as a utf-8 string

For a detailed list of functionality see the `bkp9151/scpi.py` file

Installation:

```shell
pip install bkp9151
```

Usage:

```python
import bkp9151
command = '*IDN?'
instrument = bkp9151.connect("/dev/yourdevice", <baud_rate>) # Windows users can just pass in 'COMx'
print(instrument.sendcmd(command)) # Sending raw commands.
print(instrument.get_instrument()) # calling library function.

```


Dependencies
===========
pyserial >= 2.6


Contributing
===========
Fork and submit a pull request.


MIT License
===========
Copyright (c) 2019 William Stanislaus

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
