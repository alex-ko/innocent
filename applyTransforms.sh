#!/bin/bash

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

. options.config

FULL_PATH="$1"
WRAPPERS="$2"
PACK="$3"
STRENC="$4"
ADDBAD="$5"
APK=$(basename $FULL_PATH)
WORK_DIR=$(echo $FULL_PATH | sed 's|\(.*\)/.*|\1|')
BAKSMALI=$baksmali
SMALI=$smali
KEY=$key
PASS=$keypass

echo 'Extracting .dex file...'
unzip $FULL_PATH classes.dex
APK=${APK%%????}
ORIGINAL_DEX=$APK-classes.dex
OBF_DIR=baksmali_$APK
mv classes.dex $ORIGINAL_DEX

echo 'Baksmaling...'
java -jar $BAKSMALI -o $OBF_DIR $ORIGINAL_DEX

echo 'Ready to apply transformations!'

if [ $2 -eq 1 ]
  then
    echo 'Adding wrappers...'
    python addWrappers.py $OBF_DIR
fi

if [ $3 -eq 1 ]
  then
    echo 'Packing numeric constants...'
    python packNumbers.py $OBF_DIR
fi

if [ $4 -eq 1 ]
  then
    echo 'Encrypting strings...'
    python strEncrypt.py $OBF_DIR decryptTemplate.smali
fi

if [ $5 -eq 1 ]
  then
    echo 'Injecting opaque code...'
    python addBadCode.py $OBF_DIR
fi

echo 'Smaling...'
java -jar $SMALI $OBF_DIR -o new-$ORIGINAL_DEX

if [ $5 -eq 1 ]
  then
    echo 'Modifying bytecode...'
    # NOTE: If the modified app crashes, try replacing 1 with 0 in the line below.
    # Warning! This will suppress verification which is why is disabled by default.
    python dexBytecode.py new-$ORIGINAL_DEX 0
fi

rm $ORIGINAL_DEX #clear up

echo 'Replacing new .dex file...'
zip -d $FULL_PATH classes.dex
mv new-$ORIGINAL_DEX classes.dex
zip -g $FULL_PATH classes.dex
rm classes.dex #clear up
rm -r $OBF_DIR #clear up

echo 'Signing apk...'
zip -d $FULL_PATH META-INF/*
mkdir META-INF
zip -g $FULL_PATH META-INF
rm -r META-INF #clear up
jarsigner -sigalg MD5withRSA -digestalg SHA1 -keystore $KEY -storepass $PASS $FULL_PATH test

echo 'Verifying signature...'
jarsigner -verify -certs $FULL_PATH
echo 'Done!'

