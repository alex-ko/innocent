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
import utilsSmali, utilsAnalysis
from random import shuffle, randint

def parseConst(line):
    num = line[line.index(',')+1:].strip()
    return int(num, 16)


def findNumbersInClass(lines, numbers):
    for line in lines:
        line = line.strip()
        if line.startswith('const/4') or line.startswith('const/16'):
            num = parseConst(line);
            if num not in numbers:
                numbers.append(num)


def okToProcessClass(className, lines):
    return not (className in g_ignoreList)

def findNumberConsts(directory):
    numbers = []
    
    baseDir = directory.strip().strip('.').strip('/').strip('.')
    if len(baseDir) > 0:
        baseDir += '.'
    
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filter(lambda x: x.endswith('.smali'), filenames):
            fullPath = os.path.join(dirpath, filename)
            className = fullPath[len(baseDir):]
            with open(fullPath, 'r') as smaliFile:
                lines = smaliFile.readlines()            
                
            if okToProcessClass(className, lines):
                findNumbersInClass(lines, numbers)

    shuffle(numbers)
    return numbers


######################################################

def xorTrans(n, a, b):
    return n^a

def generateDecoderCodeXorTrans(className, a, b):
    code  = '    const v1, ' + hex(a) + ' \n'
    code += '    xor-int/2addr v0, v1 \n'
    return code


def xor2Trans(n, a, b):
    return n^a^b

def generateDecoderCodeXor2Trans(className, a, b):
    code  = '    xor-int/lit16 v0, v0, ' + hex(a) + '\n'
    code += '    xor-int/lit16 v0, v0, ' + hex(b) + '\n'
    return code


def linearTrans(n, a, b):
    return n*a+b

def generateDecoderCodeLinTrans(className, a, b):
    code  = '    add-int/lit16 v0, v0, ' + hex(-b) + '\n'
    code += '    div-int/lit16 v0, v0, ' + hex(a) + '\n'
    code += '    int-to-short v0, v0, ' + hex(a) + '\n'
    return code
    

def idTrans(n, a, b):
    return n

def generateDecoderCodeIdTrans(className, a, b):
    return ''

######################################################

transformations = [(idTrans, generateDecoderCodeIdTrans)
                  ,(xorTrans, generateDecoderCodeXorTrans)
                  ,(xor2Trans, generateDecoderCodeXor2Trans)
                  #,(linearTrans, generateDecoderCodeLinTrans)
                  ]


def translateNums(numbers, transform, a, b):
    result = []
    for n in numbers:
        result.append(transform(n, a, b))
    return result


def generatePackerClass(baseDir, className, numbers):
    a = randint(10, 255)
    b = randint(10, 255)

    transformer = transformations[randint(0, len(transformations)-1)]
    modifiedNums = translateNums(numbers, transformer[0], a, b)
     
    code =  '.class public L' + className + ';\n'
    code += '.super Ljava/lang/Object;\n'
    code += '.field private static data:[S\n'
    code += '.method static constructor <clinit>()V\n'
    code += '.registers 4\n'
    code += '.prologue\n'
    code += '    const/16 v0, ' + hex(len(numbers)) + '\n'
    code += '    new-array v0, v0, [S \n'
    code += '    fill-array-data v0, :array_ak \n'
    code += '    sput-object v0, L' + className + ';->data:[S \n'
    code += '    return-void \n'
    code += generateLoadDataPart(modifiedNums)
    code += '.end method\n\n'

    code += '.method public static get(I)S'
    code += '.registers 4\n'
    code += '.prologue\n'
    code += '    sget-object v0, L' + className + ';->data:[S \n'
    code += '    aget-short v0, v0, p0 \n'
    code += transformer[1](className, a, b)
    code += '    return v0 \n'
    code += '.end method\n\n'
    return code


def generateLoadDataPart(numbers):
    code  = ':array_ak \n'
    code  += '.array-data 0x2\n'

    for d in numbers:
        lo = d % 256
        hi = (d/256) % 256
        code += '    ' + hex(lo) + 't ' + hex(hi) + 't\n'
        
    code += '.end array-data \n'
    return code
    

def generatePackers(numbers, directory):
    packers = {}
    
    classNames = utilsSmali.extractPublicClasses(directory)
    shuffle(classNames)
    count = min(randint(3, 10), len(classNames))
    
    for i in range(count):
        classLocation = classNames[i][:classNames[i].strip('/').rfind('/')]
        
        className = utilsSmali.generateClassName(classLocation)
        while className in classNames:
            className = utilsSmali.generateClassName(classLocation)
            
        packers[className] = generatePackerClass(directory, className, numbers)
        
    return packers


def savePackers(baseDir, packers):
    for packerClass in packers.keys():
        fileName = baseDir + '/' + packerClass + '.smali'
        with open(fileName, 'w') as smaliFile:
            smaliFile.write(packers[packerClass])


def extractRegisterName(line):
    parts = line.split(' ')
    return parts[1].strip(',')


def replaceConst(lines, pos, numbers, packerClass):
    line = lines[pos].strip()
    num = parseConst(line);
    index = numbers.index(num)
    register = extractRegisterName(line)
    
    if num == 1 or num == 0 or register[0] != 'v' or int(register[1:]) >= 16:
        return line, False
    
    regUsageType = utilsAnalysis.getRegisterUsageType(lines, pos, register)
    if regUsageType in ['B', 'f', 'o', 'N']:
        return line, False
    
    code  = '    const/16 ' + register + ', ' + hex(index) + '\n'
    code += '    invoke-static {'+register+'}, L' + packerClass +';->get(I)S \n'
    code += '    move-result ' + register + '\n'

    if regUsageType == 'b':
        code += '    int-to-byte ' + register + ', ' + register + '\n'
    elif regUsageType == 's':
        code += '    int-to-short ' + register + ', ' + register + '\n'
    elif regUsageType == 'c' or (num > 0 and num < 32767):
        code += '    int-to-char ' + register + ', ' + register + '\n'
    return code, True


def replaceConsts(lines, numbers, packerClasses):
    count = 0
    for index, line in enumerate(lines):
        line = line.strip()
        if line.startswith('const/4') or line.startswith('const/16'):
            line, sucess = replaceConst(lines, index, numbers, packerClasses[randint(0, len(packerClasses)-1)])
            if sucess: 
                count += 1
                lines[index] = line
    return count


def processAllClasses(directory, numbers, packerClasses):
    count = 0

    baseDir = directory.strip().strip('.').strip('/').strip('.')
    if len(baseDir) > 0: baseDir += '.'
    
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filter(lambda x: x.endswith('.smali'), filenames):
            fullPath = os.path.join(dirpath, filename)
            className = fullPath[len(baseDir):]
            with open(fullPath, 'r') as smaliFile:
                lines = smaliFile.readlines()            
                
            if okToProcessClass(className, lines):
                numberConsts = replaceConsts(lines, numbers, packerClasses)
                count += numberConsts
                if numberConsts > 0:
                    with open(fullPath, 'w') as smali:
                        smali.writelines(lines)
    return count
                

def packNumbers(directory):
    numbers = findNumberConsts(directory)
    packers = generatePackers(numbers, directory)
    modifications = processAllClasses(directory, numbers, packers.keys())
    savePackers(directory, packers)
    print modifications
    
def loadIgnore(ignoreFile):
    res = []
    keys = {}    
    with open(ignoreFile, 'r') as igFile:
        res = igFile.readlines()
        for i in range(len(res)):
            res[i] = res[i].strip()+'.smali'
    return res
    
def usage():
    print "python ", sys.argv[0], " <input folder> [<ignore list file>]"
    print "Please specify a path to dir with smali files."

g_ignoreList = []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    else:
        if len(sys.argv) > 2:
            g_ignoreList = loadIgnore(sys.argv[2])
        packNumbers(sys.argv[1])

