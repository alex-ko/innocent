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


from utilsSmali import *

#    insTypes
#    N - No instr
#    J - cond Jump
#    G - Go to
#    A - Arithmetic
#    T - geT
#    P - Put
#    S - Set value (const, move)
#    C - Cast
#    I - Invoke
#    F - Fill
#    R - Return
#    L - Label
#    M - Monitor
#    U - Unknown

def getInstructionType(line):
    if len(line) == 0 or line[0] == '.' or line[0] == '#' or line == 'nop':
        return 'N'
        
    if line.startswith('if'): 
        return 'J'
        
    if line.startswith('goto'):
        return 'G'
    
    if line.startswith('cmp') or line.startswith('new') or line.startswith('array-length'):
        return 'A'
    if line.startswith('neg') or line.startswith('rem') or line.startswith('add') or line.startswith('sub'):
        return 'A'
    if line.startswith('div')or line.startswith('mul'):
        return 'A'
    if line.startswith('and') or line.startswith('not') or line.startswith('or') or line.startswith('xor'):
        return 'A'
    if line.startswith('shl') or line.startswith('shr') or line.startswith('ushr'):
        return 'A'
    if line.startswith('packed') or line.startswith('sparse'):
        return 'A'

    if line.startswith('aget') or line.startswith('sget') or line.startswith('iget'):
        return 'T'

    if line.startswith('aput') or line.startswith('sput') or line.startswith('iput'):
        return 'P'

    if line.startswith('int-to') or line.startswith('long-to') or line.startswith('float-to') or line.startswith('double-to'):
        return 'C'

    if line.startswith('invoke') or line.startswith('execute'):
        return 'I'

    if line.startswith('filled'):
        return 'F'

    if line.startswith('move') or line.startswith('const'):
        return 'S'
    
    if line.startswith('return') or line.startswith('throw'):
        return 'R'

    if line.startswith('monitor'):
        return 'M'
    
    if line[0] == ':':
        return 'L'

    return 'U'


def getNextInstruction(lines, index):
    i = index + 1
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('.end method'):
            return -1
        if getInstructionType(line) == 'N' or getInstructionType(line) == 'L':
            i = i+1
        else:
            return i
    return -1


def getNextIndex(lines, index):
    line = lines[index].strip()
    if getInstructionType(line) == 'G':
        return locateLabel(lines, index, extractLabel(line))
    else:
        return getNextInstruction(lines, index)


def getNextLineWithRegister(lines, index, reg):
    indeces = []
    while index >= 0:
        index = getNextIndex(lines, index)
        line = lines[index].strip()
        if index in indeces: return -1
        indeces.append(index)

        if usesRegister(line, reg):
            return index
        if getInstructionType(line) == 'R':
            return -1
    return -1


def isSrcRegister(line, reg):
    t = getInstructionType(line)
    #only input
    if t in ['J', 'I', 'M', 'P', 'R']:
        return True

    #only outout
    if t in ['R', 'S']:
        return False

    #not input nor output
    if t in ['N', 'U', 'G', 'L']:
        return False

    #both
    pos = getRegisterPosition(line, reg)

    if t == 'T': return '2' in str(pos)

    if pos < 100 and pos >= 60:
        return True         
    return '3' in str(pos) or '2' in str(pos)


def isDestRegister(line, reg):
    t = getInstructionType(line)
    #only input
    if t in ['J', 'I', 'M', 'P', 'R']:
        return False

    #only outout
    if t in ['R', 'S']:
        return True

    #not input nor output
    if t in ['N', 'U', 'G', 'L']:
        return False

    #both
    pos = getRegisterPosition(line, reg)
    if t == 'T': return '1' in str(pos)

    if pos < 100 and pos >= 60:
        return False        
    return '1' in str(pos)


#   register types
#   float   'f'
#   long    'l'
#   int     'i'
#   short   's'
#   byte    'b'
#   bool    'B'
#   char    'c'
#   object  'o'
#   unknown 'u'
def extractExpectedTypeInfo(line, reg, proto):
    t = getInstructionType(line)
    pos = getRegisterPosition(line, reg)
    
    if t == 'M': return 'o'
    if t == 'J': return 'i'
    if line.startswith('cmpl') or line.startswith('cmpg'): return 'f'
    if line.startswith('cmp'): return 'l'
    if t == 'A': return 'i' #todo more precise!!!
    if t == 'R': return extractResultType(proto)
    if t == 'C':
        if line.startswith('int'): return 'i'
        if line.startswith('long'): return 'l'
        return 'f'

    if t == 'I':
        return getArgumentType(line, pos)

    if t == 'F':
        if '2' in str(pos):
            return getFillType(line)
        else:
            return 'g'

    if t == 'T':
        if '2' in str(pos):
            return 'o'
        if '3' in str(pos):
            return 'i'
        if '1' in str(pos):
            return 'g'


    if t == 'P':
        if '2' in str(pos):
            return 'o'
        if '1' in str(pos):
            if line[4] != '-': return 'i'
            line = line[5:].split()[0].strip()
            if line == 'wide': return 'l'
            if line == 'object': return 'o'
            if line == 'boolean': return 'B'
            if line == 'byte': return 'b'
            if line == 'char': return 'c'
            if line == 'short': return 's'
        if '3' in str(pos):
            return 'i'
    return 'u'


def getRegisterUsageType(lines, index, reg):
    i = index
    index = getNextLineWithRegister(lines, index, reg)
    if index > 0:
        line = lines[index].strip()
        if isSrcRegister(line, reg):
            return extractExpectedTypeInfo(line, reg, getFunctionPrototype(lines, index))
        if isDestRegister(line, reg):
            return 'g'
        return 'u'
    return 'N'


def test(f, index, reg):
    with open(f, 'r') as rf:
        lines = rf.readlines()
    line = lines[index]
    print getRegisterUsageType(lines, index, reg)
    
#test('./AppBase.smali', 185, 'v1')

