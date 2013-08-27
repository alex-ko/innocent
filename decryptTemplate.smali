.class public  <CLASS_NAME>
.super Ljava/lang/Object;

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

# instance fields
.field state:[B
.field x:S
.field y:S

# direct methods
.method public constructor <init>([B)V
    .registers 10
    .prologue

    const/4 v7, 0x0
    iput-short v7, p0,  <CLASS_NAME>->x:S
    iput-short v7, p0,  <CLASS_NAME>->y:S

    const/16 v6, 0x100
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    new-array v4, v6, [B
    iput-object v4, p0,  <CLASS_NAME>->state:[B

    const/4 v0, 0x0

    .local v0, counter:S

:goto_b
    if-lt v0, v6, :cond_17
    const/4 v0, 0x0
    const/4 v1, 0x0
    const/4 v2, 0x0
    goto :goto_14
    
:cond_17
    iget-object v4, p0,  <CLASS_NAME>->state:[B
    int-to-byte v5, v0
    aput-byte v5, v4, v0
    add-int/lit8 v4, v0, 0x1
    int-to-short v0, v4
    goto :goto_b

:goto_14
    if-lt v0, v6, :cond_20
    return-void

:cond_20
    iget-object v3, p0,  <CLASS_NAME>->state:[B
    aget-byte v4, v3, v0
    aget-byte v5, p1, v1
    
    add-int/2addr v4, v5
    add-int/2addr v2, v4
    add-int/lit16 v2, v2, 0x100
    rem-int/lit16 v2, v2, 0x100

    aget-byte v4, v3, v0
    aget-byte v5, v3, v2
    aput-byte v5, v3, v0
    aput-byte v4, v3, v2
    
    add-int/lit8 v4, v1, 0x1
    array-length v5, p1
    rem-int/2addr v4, v5
    int-to-short v1, v4
 
    add-int/lit8 v0, v0, 0x1

    goto :goto_14

.end method

# virtual methods
.method public <METHOD>([B)Ljava/lang/String;
    .registers 6
    .prologue
    array-length v2, p1
    new-array v0, v2, [B
    .local v0, arr:[B
    const/4 v1, 0x0
    .local v1, i:I
    
    :goto_4
    array-length v2, p1
    if-lt v1, v2, :cond_d
    new-instance v2, Ljava/lang/String;
    invoke-direct {v2, v0}, Ljava/lang/String;-><init>([B)V
    return-object v2
    :cond_d
    aget-byte v2, p1, v1
    invoke-virtual {p0},  <CLASS_NAME>->RGB()B
    move-result v3
    xor-int/2addr v2, v3
    int-to-byte v2, v2
    aput-byte v2, v0, v1
    .line 61
    add-int/lit8 v1, v1, 0x1
    goto :goto_4
.end method

.method public RGB()B
    .registers 6

    .prologue

    iget-short v1, p0,  <CLASS_NAME>->x:S
    add-int/lit8 v1, v1, 0x1
    rem-int/lit16 v1, v1, 0x100
    int-to-short v1, v1
    iput-short v1, p0,  <CLASS_NAME>->x:S

    iget-object v1, p0,  <CLASS_NAME>->state:[B
    iget-short v2, p0,  <CLASS_NAME>->x:S
    aget-byte v1, v1, v2

    iget-short v2, p0,  <CLASS_NAME>->y:S
    add-int/2addr v1, v2
    add-int/lit16 v1, v1, 0x100
    rem-int/lit16 v1, v1, 0x100
    int-to-short v1, v1
    iput-short v1, p0,  <CLASS_NAME>->y:S

    iget-object v0, p0,  <CLASS_NAME>->state:[B
    iget-short v1, p0,  <CLASS_NAME>->x:S
    iget-short v2, p0,  <CLASS_NAME>->y:S

    aget-byte v3, v0, v1
    aget-byte v4, v0, v2
    aput-byte v4, v0, v1
    aput-byte v3, v0, v2

    add-int/2addr v3, v4
    add-int/lit16 v3, v3, 0x100
    rem-int/lit16 v1, v3, 0x100
    aget-byte v1, v0, v1
    
    int-to-byte v1, v1
    return v1
.end method

.method private b()V
    .registers 2
    const/4 v0, 0x6
    const/16 v1, 0x1a
    sget-object v1, Ljava/lang/System;->out:Ljava/io/PrintStream;
    const-string v0, "abcdefghijklmnopqrstuvwxyz1234567890"
    invoke-virtual {v1, v0}, Ljava/io/PrintStream;->print(Ljava/lang/String;)V
    :goto_0
    goto :goto_1
    mul-int/2addr v1, v0
    sub-int/2addr v1, v0 
    :goto_1
    goto :goto_0
    return-void
.end method

