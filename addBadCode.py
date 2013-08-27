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

import sys, os
from random import randint
from utilsSmali import *
from utilsOpaque import *

junkRegs = {'junk1':2, 'junk2':3, 'junk3':4, 'junk4':2, 'junk5':2, 'junk6':2, 'junk7':2, 'junk8':2, 'junk9':2, 'junk10':2, 'junk11':2, 'junk12':2}
junk = [junk2, junk3, junk1, junk4, junk5, junk6, junk7, junk8, junk9, junk10, junk11, junk12]
opaque = [opaque003, opaque004, opaque005, opaque007, opaque008, opaque009, opaque010,  #2  regs
          opaque002, opaque006, opaque011,                                              #3  regs
          opaque012, opaque014, opaque015,                                              #4  regs
          opaque013,                                                                    #6  regs
          opaque016,                                                                    #7  regs
          opaque017,                                                                    #8  regs
          opaque018]                                                                    #12 regs
    

def buildOpaque(predicate, regs, stubInvoke, isStubInvoked):
    res = predicate

#    Uncomment the next if you want junk code in predicate (not really needed, though). 

#    if(regs >= 3):
#        res += junk2
#    elif(regs >= 4):
#        res += junk3
#    else:
#        res += junk[randint(2, len(junk)-1)]
    if not isStubInvoked:
        res += '\n' + stubInvoke
    res += '\nconst/16 v0, 0x67 \n const/16 v1, 0xa1e4 \n' + ('    nop\n'*15)
    res += ':goto_lbl\n'
    return res

def getOpaque(regs, stubInvoke, isStubInvoked):
    """Return opaque predicate code based on the number of registers needed."""
    if regs < 2:
        return ''
    elif regs >= 12:
        pos = 16
    elif regs >= 8:
        pos = 15
    elif regs >= 7:
        pos = 14
    elif regs >= 6:
        pos = 13
    elif regs >= 4:
        pos = 12
    elif regs >= 3:
        pos = 9
    elif regs == 2:
        pos = 6
    return buildOpaque(opaque[randint(0, pos)], regs, stubInvoke, isStubInvoked)

def isNotEmptyMethodProt(line):
    if line.startswith('.method'):
        if (not ' static ' in line) and (not ' native ' in line) and (not ' abstract ' in line):
            #do more checks if needed
            return True
    return False

def locateSutableMethod(lines, startFromLine):
    for index in range(startFromLine, len(lines)):
        line = lines[index].strip()
        if isNotEmptyMethodProt(line):
            return index
    return -1

def generateCrackStub():
    i1, i2 = randint(0, len(junk)/2), randint((len(junk)/2)+1, len(junk)-1)
    r1, r2 = junkRegs['junk'+str(i1+1)], junkRegs['junk'+str(i2+1)]
    regs = r1 ^ ((r1 ^ r2) & -(r1 < r2))
    stubName = generateNames(50)[randint(20,49)] + str(randint(0, 1773))
    stub = '.method private static ' + stubName+ '()V\n' + '.registers ' + str(regs) + '\n'
    stub += junk[i1] + junk[i2] + 'return-void\n' + '.end method\n'
    stubInvoke = 'invoke-static {}, Ljava/lang/Void;->'+stubName+'()V\n'
    return stub, stubInvoke

def insertOpaque(lines):
    start = 0
    crackStub, stubInvoke = generateCrackStub()
    stubInvokations = randint(2,5)
    while start >= 0 and start < len(lines):
        index = locateSutableMethod(lines, start)
        if index > 0:
            freeRegs = getFreeRegs(lines, index)
            if stubInvokations > 0:
                opaque = getOpaque(freeRegs, stubInvoke, False)
                stubInvokations = stubInvokations - 1
            else:
                opaque = getOpaque(freeRegs, stubInvoke, True)
            if opaque != '':
                insertPos = getFirstCodeLineIndex(lines, index)
                lines.insert(insertPos, opaque)
            start = index+1
        else:
            break
    lines.insert(len(lines), crackStub)
    return lines

def isInjectionApplicable(lines):
    for line in lines:
        if line.startswith('.class'):
            return ' interface ' not in line
    return False

def injectOpaqueCode(fileName):
    with open(fileName, 'r') as smaliFile:
        lines = smaliFile.readlines()

    if isInjectionApplicable(lines):
        lines = insertOpaque(lines)
            
        with open(fileName, 'w') as smaliFile:
            smaliFile.writelines(lines)
        return True
    return False

def injectOpaquePredicate(directory):
    baseDir = sys.argv[1].strip().strip('/').strip('.')
    if len(baseDir) > 0:
        baseDir += '.'
    classes = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filter(lambda x: x.endswith('.smali'), filenames):
            fullPath = os.path.join(dirpath, filename)
            if injectOpaqueCode(fullPath):
                classes += 1
    print classes

def usage():
    print "python ", sys.argv[0], " <input folder>"
    print "Please specify a path to dir with smali files."

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()      
    else:
        injectOpaquePredicate(sys.argv[1])
