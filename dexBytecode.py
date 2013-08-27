#   Copyright [2013] [alex-ko askovacheva<<at>>gmail<<dot>>com]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

#   Note: This code is based on previous work with the link below:
#   https://github.com/thuxnder/dalvik-obfuscator/blob/master/injector.py


import array
import struct
import zlib
import sys

class DexMethod:
    def __init__(self, dexfile, offset, name):
        self._name = name
        self._dexfile = dexfile
        self._offset = offset
        self._numRegisters = 0
        self._numInstructions = 0
        if offset > 0:
            self._parseHeader()
        if self._numInstructions > 0:
            self.code = list(self._dexfile.getData(self._offset+16, self.getMethodCodeSize(), 'B'*self.getMethodCodeSize()))            
                

    def _parseHeader(self):
        (self._numRegisters, ) = self._dexfile.getData(self._offset, 2, 'H')
        (self._numInstructions, )   = self._dexfile.getData(self._offset+12, 4, 'I')

    def getMethodCodeSize(self):
        # each instruction is 2 bytes long
        return self._numInstructions * 2


    def containsOurCode(self):
        ourCode = [0x13,0x00, 0x67,0x00, 0x13,0x01, 0xe4,0xa1, 0x00,0x00, 0x00,0x00, 0x00,0x00]

        for start in range(len(self.code) - len(ourCode)):
            for i in range(len(ourCode)):
                if self.code[start + i] != ourCode[i]:
                    break
            if self.code[start + i] == ourCode[i]:
                return start
        return -1


    def replaceCode(self, newCode, offset):
        if self._offset == 0:
            return False

        if len(newCode)+offset > self.getMethodCodeSize:
            raise Exception("Method too short, cannot inject bytecode.")

        bytecode = self._dexfile.getData(self._offset+16+offset, len(newCode), 'B'*len(newCode))

        for opcode in bytecode:
            if opcode != 0x00:
                raise Exception("Not NOP codes only! Unable to replace code.")

        self._dexfile.setData(self._offset+16+offset, len(newCode), 'B'*len(newCode), newCode)

        return True


class DexClass:
    def __init__(self, dexfile, offset, supressVerification):
        self._dexfile = dexfile
        self._access_flags = 0
        self._offset = offset
        self._directMethods = {}
        self._virtualMethods = {}
        self._parseHeader()
        if self.hasData():
            self._parseClassDataItem()
            self.setVerified(supressVerification)


    def hasData(self):
        return self._class_data_off > 0


    def setVerified(self, supressVerification):
        if supressVerification:
            self._dexfile.setData(self._offset+4, 4, 'I', (self._access_flags|0x10000,) )


    def _parseHeader(self):
        (self._access_flags, )   = self._dexfile.getData(self._offset+4, 4, 'I')
        (self._class_data_off, ) = self._dexfile.getData(self._offset+24, 4, 'I')


    def getMethods(self):
        return self._directMethods.values()+self._virtualMethods.values()


    def _parseMethod(self, offset, idx):
        (size, method_idx_diff) = self._dexfile.parseUleb128(offset)
        idx += method_idx_diff
        offset += size
        
        (size, access_flags) = self._dexfile.parseUleb128(offset)
        offset += size
        
        (size, code_off) = self._dexfile.parseUleb128(offset)
        offset += size

        method = 0
        if (code_off > 0):
            method = self._dexfile.createMethod(idx, code_off)
        return offset, code_off, method, idx

    def _parseClassDataItem(self):
        # get class sections size
        offset = self._class_data_off
        (size, self.static_filds_size) = self._dexfile.parseUleb128(offset)
        offset += size
        (size, self.instance_fields_size) = self._dexfile.parseUleb128(offset)
        offset += size
        (size, self.direct_methods_size)  = self._dexfile.parseUleb128(offset)
        offset += size
        (size, self.virtual_methods_size) = self._dexfile.parseUleb128(offset)
        offset += size

        # skip fields
        for i in range ((self.static_filds_size + self.instance_fields_size) * 2):
            (size, tmp) = self._dexfile.parseUleb128(offset)
            offset += size

        # parse methods
        idx = 0
        badCode = [0x74,0x00, 0x00,0x00, 0x00,0x00,              # invoke-virtual/range {} method@0000 (1st in table)
                   0x00,0x01, 0x00,0x00, 0x00,0x00,              # packed swith data table, len = 0
                   0x2B,0x01, 0xfd,0xff, 0xff,0xff,              # packed-switch v1, with invalid table offset - fdff ffff (-2), 
                                                                 # but passes the verification
                   0x00,0x03, 0x01,0x00, 0xFF,0xFF, 0xFF,0xFF,   # fill array data table, size 0xffff 0xffff 
                                                                 # but is truncated to the method boundaries by the DVM
                   0x00,0x00]

        for i in range (self.direct_methods_size):
            (offset, code_off, method, idx) = self._parseMethod(offset, idx)
            if code_off == 0: # no code -> method is abstract or native
                continue

            pos = method.containsOurCode()
            if (pos > 0):
                method.replaceCode(badCode, pos+10)
            self._directMethods[code_off] = method

        idx = 0
        for i in range (self.virtual_methods_size):
            (offset, code_off, method, idx) = self._parseMethod(offset, idx)
            if code_off == 0: # no code -> method is abstract or native
                continue
            
            pos = method.containsOurCode()
            if (pos > 0):
                method.replaceCode(badCode, pos+10)
            self._virtualMethods[code_off] = method
		

class Dexfile:
    def __init__(self, filename):
        self._dexfilename = filename
        self._data = array.array('c', open(self._dexfilename, 'rb').read())

    def getData(self, offset, size, form):
        if len(self._data) < offset+size:
            raise Exception("dexfile is too small " + str(offset) + " " + str(size))
        return struct.unpack_from(form, self._data, offset)

    def setData(self, offset, size, form, data):
        if len(self._data) < offset+size:
            raise Exception("dexfile is too small")
        return struct.pack_into(form, self._data, offset, *data)

    def save(self):
        self._fixChecksum()
        with open(self._dexfilename, 'wb') as dexfile:
            dexfile.write(self._data)

    def parseUleb128(self, offset):
        (byte0, byte1, byte2, byte3) = self.getData(offset, 4, 'BBBB')
        size = (byte0 & 0x7f)
        bytelen = 1
        if (byte0 & 0x80) == 0x80:
            bytelen += 1
            size = (size & 0xff) | ((byte1 & 0x7f)<<7)
            if (byte1 & 0x80) == 0x80:
                bytelen += 1
                size = (size & 0xffff) | ((byte2 & 0x7f)<<14)
                if (byte2 & 0x80) == 0x80:
                    bytelen += 1
                    size = (size & 0xffffff) | ((byte3 & 0x7f)<<21)
        return (bytelen, size)

    def createClass(self, offset, supressVerification):
        return DexClass(self, offset, supressVerification)

    def getClasses(self, supressVerification):
        (clsCount, offset) = self.getData(96, 8, 'II')
        classOffList =  map(lambda idx: offset+(32*idx), range(clsCount))
        self._classes = { offset:self.createClass(offset, supressVerification) for offset in classOffList }
        return self._classes.values()

    def createMethod(self, methodIdx, offset):
        #locate method name...
        (mthCount, off) = self.getData(88, 8, 'II')
        methodIdOff = off + 8*methodIdx

        (nameIdx, ) = self.getData(methodIdOff+4, 4, 'I')
        (strCnt, off) = self.getData(56, 8, 'II')
        
        off += nameIdx * 4
        (nameOffset, ) = self.getData(off, 4, 'I')
        (off, size) = self.parseUleb128(nameOffset)
        nameOffset += off;

        #read the name
        methodBytes = self.getData(nameOffset, size, 'B'*size)
        methodName = ''.join(map(chr, methodBytes))
        return DexMethod(self, offset, methodName)

    def _fixChecksum(self):
        self.setData(8, 4, 'I', (zlib.adler32(self._data[12:],1)% (2**32),))

    def _setSignature(self, signature):
        if not len(signature) == 40:
            raise Exception("wrong signature size")
        sig = []
        for i in range(20):
            sig.append( int(signature[i*2:(i*2)+2], 16) )
        self.setData(12, 20, 'B'*20, sig)


class Tester:
    def __init__(self, filename, supressVerification):
        self._dexfile = Dexfile(filename)
        self._parseClassList(supressVerification)
        self._parseMethodList()
        self._dexfile.save()


    def _parseClassList(self, supressVerification):
        (size, offset) = self._dexfile.getData(96, 8, 'II')
        classes = self._dexfile.getClasses(supressVerification)
        self._classes = filter(lambda cls: cls.hasData(), classes)

	
    def _parseMethodList(self):
        self._methods = { cls:cls.getMethods() for cls in self._classes}

if __name__ == "__main__":
    filename = sys.argv[1]
    supress = len(sys.argv) < 3
    test = Tester(filename, supress)

