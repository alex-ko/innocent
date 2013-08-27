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

class rc4:
    """ RC4 code from:
    http://web.archive.org/web/20080404222417/http://cypherpunks.venona.com/date/1994/09/msg00304.html """
    def __init__(self, key):
        self.x = 0
        self.y = 0
        self.state = [];
        for i in range(256):
            self.state.append(i)
            
        idx1 = 0
        idx2 = 0
        for i in range(256):
            idx2 = (key[idx1] + self.state[i] + idx2)%256
            self.state[i], self.state[idx2] = self.state[idx2], self.state[i]
            idx1 = (idx1 + 1) % len(key)
            
    def getNextEncByte(self):          
          self.x = (self.x + 1) % 256
          self.y = (self.state[self.x] + self.y) % 256
         
          self.state[self.x], self.state[self.y] = self.state[self.y], self.state[self.x]            
          xorIndex = (self.state[self.x] + self.state[self.y]) % 256
          return self.state[xorIndex]

    def encode(self, text):
        code = []
        for x in map(ord, text):
            code.append(x^self.getNextEncByte())
        return code 

    def decode(self, enc):
        code = []
        for x in enc:
            code.append(x^self.getNextEncByte())
        return "".join(map(chr, code))

