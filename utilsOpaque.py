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

#------------------------------------------------------------------------#
#                           Opaque predicates                            #
#------------------------------------------------------------------------#
#									 #
# The  predicates are sorted ascendingly by the computational difficulty #
# for their automatic detection and evaluation. Whenever a predicate has #
# been  seen  previously  in  lithereature, it  is marked as well known. #
#------------------------------------------------------------------------#

# 1-1 == 0
# trivial, for testing only
# 2 registers
opaque001 = '                  \n\
    const/4 v0, 0x1            \n\
    const/4 v1, 0x1            \n\
    sub-int/2addr v0, v1       \n\
    if-eqz v0, :goto_lbl       \n\
'

# Math: 7x^2 -1 <> y^2   x,y in Z
# Java: 7*x*x - 1 != y*y
# good (well known)
# 3 registers
# note: v1, v2 = x, y
opaque002='                    \n\
    const/4 v1, 0x5            \n\
    const/4 v2, 0x4            \n\
    mul-int/lit8 v0, v1, 0x7   \n\
    mul-int/2addr v0, v1       \n\
    add-int/lit8 v0, v0, -0x1  \n\
    mul-int v1, v2, v2         \n\
    if-ne v0, v1, :goto_lbl    \n\
'

# Math: 3 | (x^3 - 3)   x in Z+
# Java: (x*x*x - x) %3 == 0
# weak (well known)
# 2 registers
# note: v1 = x
opaque003='                    \n\
    const/16 v1, 0x26          \n\
    mul-int v0, v1, v1         \n\
    mul-int/2addr v0, v1       \n\
    sub-int/2addr v0, v1       \n\
    rem-int/lit8 v0, v0, 0x3   \n\
    if-eqz v0, :goto_lbl       \n\
'

# Math: 2 | x or 8 | (x^2 -1)   x in Z+
# Java: x%2==0 || (x*x -1)%8 == 0
# weak (well known)
# 2 registers
# note: v1 = x
opaque004='                    \n\
    const/16 v1, 0xe5          \n\
    rem-int/lit8 v0, v1, 0x2   \n\
    if-eqz v0, :cond_lbl       \n\
    mul-int v0, v1, v1         \n\
    add-int/lit8 v0, v0, -0x1  \n\
    rem-int/lit8 v0, v0, 0x8   \n\
    if-nez v0, :cond_lb        \n\
    :cond_lbl                  \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Math: 2 | floor(x^2)   x in N
# Java: ((x*x)/2)%2 == 0
# weak (well known)
# 2 registers
# note: v1 = x
opaque005='                    \n\
    const/16 v1, 0xda          \n\
    mul-int v0, v1, v1         \n\
    div-int/lit8 v0, v0, 0x2   \n\
    rem-int/lit8 v0, v0, 0x2   \n\
    if-eqz v0, :goto_lbl       \n\
'

# Math: 3 | x*(x+1)*(x+2)   x in Z+
# Java: x*(x+1)*(x+2)%3 == 0
# weak (well known)
# 3 registers
# note: v2 = x 
opaque006='                    \n\
    const/16 v2, 0xa           \n\
    add-int/lit8 v0, v2, 0x1   \n\
    mul-int/2addr v0, v2       \n\
    add-int/lit8 v1, v2, 0x2   \n\
    mul-int/2addr v0, v1       \n\
    rem-int/lit8 v0, v0, 0x3   \n\
    if-nez v0, :cond_lb        \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Math: 7 | (x^2 +1)    x in Z+
# Java: (x*x+1)%7 != 0
# weak (well known)
# 2 registers
# note: v1 = x
opaque007='                    \n\
    const/16 v1, 0xbeef        \n\
    mul-int v0, v1, v1         \n\
    add-int/lit8 v0, v0, 0x1   \n\
    rem-int/lit8 v0, v0, 0x7   \n\
    if-eqz v0, :cond_lb        \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Math: 81 | (x^2 + x + 7)   x in Z+
# Java: (x*x + x + 7)%81 != 0 
# weak (well known)
# 2 registers
# note: v1 = x
opaque008='                    \n\
    const/16 v1, 0xca7         \n\
    mul-int v0, v1, v1         \n\
    add-int/2addr v0, v1       \n\
    add-int/lit8 v0, v0, 0x7   \n\
    rem-int/lit8 v0, v0, 0x51  \n\
    if-eqz v0, :cond_lb        \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
 '

# Math: 19 | 4(x^2 + 1)   x in Z+
# Java: (4*x*x + 4)%19 != 0
# weak (well known)
# 2 registers
# note: v1 = x
opaque009='                    \n\
    const/16 v1, 0x1ee7        \n\
    mul-int/lit8 v0, v1, 0x4   \n\
    mul-int/2addr v0, v1       \n\
    add-int/lit8 v0, v0, 0x4   \n\
    rem-int/lit8 v0, v0, 0x13  \n\
    if-eqz v0, :cond_lb        \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Math: 7 ~| (x^2 + 1)   x in z+
# Java: (x*x+1)%7 != 0
# weak (well known)
# 2 registers
# note: v1 = x
opaque010='                    \n\
    const/16 v1, 0xdead        \n\
    mul-int v0, v1, v1         \n\
    add-int/lit8 v0, v0, 0x1   \n\
    rem-int/lit8 v0, v0, 0x7   \n\
    if-eqz v0, :cond_lbl       \n\
    goto :goto_lbl             \n\
    :cond_lbl                  \n\
'

# Math: 4 | x^2(x+1)^2   x in Z+
# Java: x*x*(x+1)*(x+1)%4 == 0
# weak (well known)
# 3 registers
# note: v1 = x
opaque011='                    \n\
    const/4 v1, 0x6            \n\
    mul-int v0, v1, v1         \n\
    add-int/lit8 v2, v1, 0x1   \n\
    mul-int/2addr v0, v2       \n\
    mul-int/2addr v0, v2       \n\
    rem-int/lit8 v0, v0, 0x4   \n\
    if-nez v0, :cond_lbl       \n\
    goto :goto_lbl              \n\
    :cond_lbl                  \n\
'

# Math: 4*(x-y) + 5*(x+y) = 7*(x+y) + 2*(x-3*y)   x,y in Z+
# Java: 4*(x-y) + 5*(x+y) == 7*(x+y) + 2*(x-3*y)
# average
# 4 registers
# note: v2, v3 = x, y
opaque012='                    \n\
    const/4 v2, 0x3            \n\
    const/16 v3, 0x204         \n\
    sub-int v0, v2, v3         \n\
    mul-int/lit8 v0, v0, 0x4   \n\
    add-int v1, v2, v3         \n\
    mul-int/lit8 v1, v1, 0x5   \n\
    add-int/2addr v0, v1       \n\
    add-int v1, v2, v3         \n\
    mul-int/lit8 v1, v1, 0x7   \n\
    mul-int/lit8 v3, v3, 0x3   \n\
    sub-int v3, v2, v3         \n\
    mul-int/lit8 v3, v3, 0x2   \n\
    add-int/2addr v1, v3       \n\
    if-ne v0, v1, :cond_lb     \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Math: x^3 + y^3 = (x+y)(x^2 -xy + y^2)    x,y in Z
# Java: x*x*x + y*y*y == (x+y)*(x*x-x*y+y*y)
# average
# 6 registers
# note: v1, v2 = x ,y
opaque013='                    \n\
    const/16 v1, 0x33          \n\
    const/4 v2, 0x5            \n\
    mul-int v0, v1, v1         \n\
    mul-int/2addr v0, v1       \n\
    mul-int v3, v2, v2         \n\
    mul-int/2addr v3, v2       \n\
    add-int/2addr v0, v3       \n\
    add-int v3, v1, v2         \n\
    mul-int v4, v1, v1         \n\
    mul-int v5, v1, v2         \n\
    sub-int/2addr v4, v5       \n\
    mul-int v5, v2, v2         \n\
    add-int/2addr v4, v5       \n\
    mul-int/2addr v3, v4       \n\
    if-ne v0, v3, :cond_lb     \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Math: (x+y)^2-(x-y)^2 = 4xy   x,y in Z
# Java: (x+y)*(x+y)-(x-y)*(x-y)== 4*x*y
# average
# 4 registers
# note: v1, v2 = x, y
opaque014='                    \n\
    const/16 v1, 0x31          \n\
    const/4 v2, 0x4            \n\
    add-int v0, v1, v2         \n\
    mul-int/2addr v0, v0       \n\
    sub-int v3, v1, v2         \n\
    mul-int/2addr v3, v3       \n\
    sub-int/2addr v0, v3       \n\
    mul-int/lit8 v3, v1, 0x4   \n\
    mul-int/2addr v3, v2       \n\
    if-ne v0, v3, :cond_lb     \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Math: (x+y)^2 + (x+y)^2 = 2(x^2 + y^2)    x,y in Z
# Java: (x+y)*(x+y)+(x-y)*(x-y)== 2*(x*x + y*y)
# average
# 4 registers
# note: v1, v2 = x, y
opaque015='                    \n\
    const/16 v1, 0x7a          \n\
    add-int/lit16 v2, v1, 0x45 \n\
    add-int v0, v1, v2         \n\
    mul-int/2addr v0, v0       \n\
    sub-int v3, v1, v2         \n\
    mul-int/2addr v3, v3       \n\
    add-int/2addr v0, v3       \n\
    mul-int/2addr v1, v1       \n\
    mul-int/2addr v2, v2       \n\
    add-int v3, v1, v2         \n\
    mul-int/lit8 v3, v3, 0x2   \n\
    if-ne v0, v3, :cond_lb     \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Math: x(m+n) + y(n-m) = m(x-y) + n(x+y)   x,y,m,n in Z
# Java: x*(m+n) + y*(n-m) == m*(x-y) + n*(x+y)
# good
# 7 registers
# note: v3, v4, v5, v6 = x, y, m, n
opaque016='                    \n\
    const/16 v3, 0x955e        \n\
    add-int/lit8 v4, v3, 0x6   \n\
    const/16 v5, 0x340a        \n\
    sub-int v6, v3, v5         \n\
    add-int v0, v5, v6         \n\
    mul-int/2addr v0, v3       \n\
    sub-int v1, v6, v5         \n\
    mul-int/2addr v1, v4       \n\
    add-int/2addr v0, v1       \n\
    sub-int v1, v3, v4         \n\
    mul-int/2addr v1, v5       \n\
    add-int v2, v3, v4         \n\
    mul-int/2addr v2, v6       \n\
    add-int/2addr v1, v2       \n\
    if-ne v0, v1, :cond_lb     \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Brahmagupta-Fibonacci identity
# Math: (a^2 + b^2)(c^2 + d^2) = (ac -bd)^2 + (ad + bc)^2    a,b,c,d in Z
# Java: (a*a + b*b)*(c*c+d*d) == 
#       (a*c - b*d)*(a*c - b*d) + 
#       (a*d + b*c)*(a*d + b*c)
# strong
# 8 registers (10 in smali)
# note: v4, v5, v6, v7 =  a, b, c, d
opaque017='                    \n\
    const/16 v4, 0xa09         \n\
    mul-int/lit8 v5, v4, 0x2   \n\
    const/16 v6, 0x29a         \n\
    add-int/lit8 v7, v6, 0x3   \n\
    mul-int v0, v4, v4         \n\
    mul-int v1, v5, v5         \n\
    add-int/2addr v0, v1       \n\
    mul-int v1, v6, v6         \n\
    mul-int v2, v7, v7         \n\
    add-int/2addr v1, v2       \n\
    mul-int/2addr v0, v1       \n\
    mul-int v1, v4, v6         \n\
    mul-int v2, v5, v7         \n\
    sub-int/2addr v1, v2       \n\
    mul-int/2addr v1, v1       \n\
    mul-int v2, v4, v7         \n\
    mul-int v3, v5, v6         \n\
    add-int/2addr v2, v3       \n\
    mul-int/2addr v2, v2       \n\
    add-int/2addr v1, v2       \n\
    if-ne v0, v1, :cond_lb     \n\
    goto :goto_lbl             \n\
    :cond_lb                   \n\
'

# Euler's four-square identity
# Math: (a1^2+a2^2+a3^2+a4^2)*(b1^2+b2^2+b3^2+b4^2) == 
#  (a1*b1-a2*b2-a3*b3-a4*b4)^2 + (a1*b2+a2*b1+a3*b4-a4*b3)^2 + 
#  (a1*b3-a2*b4+a3*b1+a4*b2)^2 + (a1*b4+a2*b3-a3*b2+a4*b1)^2
#
# Java: (a1*a1+a2*a2+a3*a3+a4*a4)*(b1*b1+b2*b2+b3*b3+b4*b4) == 
#  (a1*b1-a2*b2-a3*b3-a4*b4)*(a1*b1-a2*b2-a3*b3-a4*b4) +
#  (a1*b2+a2*b1+a3*b4-a4*b3)*(a1*b2+a2*b1+a3*b4-a4*b3) + 
#  (a1*b3-a2*b4+a3*b1+a4*b2)*(a1*b3-a2*b4+a3*b1+a4*b2) +
#  (a1*b4+a2*b3-a3*b2+a4*b1)*(a1*b4+a2*b3-a3*b2+a4*b1)
#
# strong
# 12 registers
# note: v4, v5, v6, v7, v8, v9, v10, v11 = a1, a2, a3, a4, b1, b2, b3, b4
opaque018='                    \n\
    const/16 v4, 0x24          \n\
    add-int/lit8 v5, v4, 0x4   \n\
    add-int/lit8 v6, v5, 0x1   \n\
    add-int/lit8 v7, v4, 0x1   \n\
    add-int/lit8 v8, v7, 0x5   \n\
    mul-int/lit8 v9, v8, 0x2   \n\
    add-int/lit8 v10, v9, 0x7  \n\
    mul-int/lit8 v11, v4, 0x3  \n\
    mul-int v0, v4, v4         \n\
    mul-int v1, v5, v5         \n\
    add-int/2addr v0, v1       \n\
    mul-int v1, v6, v6         \n\
    add-int/2addr v0, v1       \n\
    mul-int v1, v7, v7         \n\
    add-int/2addr v0, v1       \n\
    mul-int v1, v8, v8         \n\
    mul-int v2, v9, v9         \n\
    add-int/2addr v1, v2       \n\
    mul-int v2, v10, v10       \n\
    add-int/2addr v1, v2       \n\
    mul-int v2, v11, v11       \n\
    add-int/2addr v1, v2       \n\
    mul-int/2addr v0, v1       \n\
    #---end left part---#      \n\
    mul-int v1, v4, v8         \n\
    mul-int v2, v5, v9         \n\
    sub-int/2addr v1, v2       \n\
    mul-int v2, v6, v10        \n\
    sub-int/2addr v1, v2       \n\
    mul-int v2, v7, v11        \n\
    sub-int/2addr v1, v2       \n\
    mul-int/2addr v1, v1       \n\
    #---end first bracket---#  \n\
    mul-int v2, v4, v9         \n\
    mul-int v3, v5, v8         \n\
    add-int/2addr v2, v3       \n\
    mul-int v3, v6, v11        \n\
    add-int/2addr v2, v3       \n\
    mul-int v3, v7, v10        \n\
    sub-int/2addr v2, v3       \n\
    mul-int/2addr v2, v2       \n\
    #---end second bracket---# \n\
    add-int/2addr v1, v2       \n\
    #---add res in v1---#      \n\
    mul-int v2, v4, v10        \n\
    mul-int v3, v5, v11        \n\
    sub-int/2addr v2, v3       \n\
    mul-int v3, v6, v8         \n\
    add-int/2addr v2, v3       \n\
    mul-int v3, v7, v9         \n\
    add-int/2addr v2, v3       \n\
    mul-int/2addr v2, v2       \n\
    #---end third bracket---#  \n\
    add-int/2addr v1, v2       \n\
    #---add res in v1---#      \n\
    mul-int v2, v4, v11        \n\
    mul-int v3, v5, v10        \n\
    add-int/2addr v2, v3       \n\
    mul-int v3, v6, v9         \n\
    sub-int/2addr v2, v3       \n\
    mul-int v3, v7, v8         \n\
    add-int/2addr v2, v3       \n\
    mul-int/2addr v2, v2       \n\
    #---end fourth bracket---# \n\
    add-int/2addr v1, v2       \n\
    if-eq v0, v1, :goto_lbl    \n\
    :cond_lb                   \n\
'

#------------------------------------------------------------------------#
#              Junk code samples to inject in bogus methods              #
#------------------------------------------------------------------------#

# 2 registers
junk1 = '                \n\
    :lab1                  \n\
    goto :lab2             \n\
    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;  \n\
    const-string v1, "Value too high."   \n\
    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->print(Ljava/lang/String;)V  \n\
    if-eq v0, v1, :cond_facile  \n\
    goto :lab2             \n\
    :cond_facile           \n\
    goto :lab1             \n\
    const-string v0, "Log" \n\
    invoke-static {v0, v1}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I  \n\
    move-result v0         \n\
    :lab2                  \n\
    goto :lab1             \n\
'

# 3 registers
junk2 = '                    \n\
    new-instance v0, Ljava/lang/StringBuilder;  \n\
    const-string v1, "abcdefghijklmnopqrstuvwxyz1234567890"  \n\
    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V  \n\
    :lbb                       \n\
    goto :lab                  \n\
    const/4 v0, 0x1            \n\
    const/4 v1, 0x7            \n\
    mul-int/2addr v0, v0       \n\
    invoke-static {v0}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;  \n\
    move-result-object v0      \n\
    :lab                       \n\
    goto :lbb                  \n\
    mul-int/2addr v1, v1       \n\
'

# 4 registers
junk3 = '                                \n\
    const/4 v0, 0x7                       \n\
    const/4 v1, 0x4                        \n\
    :goto_Al0                              \n\
    goto :goto_Al1                         \n\
    mul-int v0, v1, v0                     \n\
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J  \n\
    move-result-wide v1                    \n\
    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;  \n\
    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->print(Ljava/lang/String;)V  \n\
    :goto_Al1                              \n\
    goto :goto_Al0                         \n\
    const/4 v3, 0x1                        \n\
    const/4 v2, 0x0                        \n\
    const/4 v1, 0x2                        \n\
    new-array v0, v1, [Ljava/lang/String;  \n\
    const-string v1, "Too high."           \n\
    aput-object v1, v0, v2                 \n\
    const-string v1, "Too low."            \n\
    aput-object v1, v0, v3                 \n\
    aget-object v1, v0, v2                 \n\
    aget-object v2, v0, v3                 \n\
    invoke-virtual {v1, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z  \n\
    move-result v1                         \n\
    if-eqz v1, :cond_1e13                  \n\
    :cond_1e13                             \n\
    goto :goto_Al0                         \n\
'

# 2 registers
junk4 = '                    \n\
    const/16 v0, 0xa           \n\
    const/4 v1, 0x4            \n\
    :goto_Bl0                  \n\
    goto :goto_Bl1             \n\
    const/16 v0, 0x4           \n\
    const/4 v1, 0x3            \n\
    mul-int v1, v1, v0         \n\
    if-eqz v1, :goto_Bl1       \n\
    new-instance v0, Ljava/lang/RuntimeException;  \n\
    invoke-direct {v0}, Ljava/lang/RuntimeException;-><init>()V  \n\
    throw v0                   \n\
    :goto_Bl1                  \n\
    goto :goto_Bl0             \n\
'

# 2 registers
junk5 = '                    \n\
    const/16 v0, 0xa           \n\
    const/4 v1, 0x4            \n\
    :goto_Bl0                  \n\
    goto :goto_Bl1             \n\
    const/4 v0, 0x7            \n\
    const/4 v1, 0x4            \n\
    mul-int v0, v1, v0         \n\
    :goto_Bl1                  \n\
    goto :goto_Bl0             \n\
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J  \n\
    move-result-wide v0                    \n\
    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;  \n\
    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->print(Ljava/lang/String;)V  \n\
'

# 2 registers
junk6 = '                    \n\
    const/4 v1, 0x3            \n\
    const/16 v0, 0x15          \n\
    mul-int v0, v1, v0         \n\
    :goto_Cl0                  \n\
    goto :goto_Cl1             \n\
    const/16 v0, 0xa           \n\
    const/4 v1, 0x4            \n\
    rem-int/lit8 v2, v1, 0x6   \n\
    mul-int v0, v1, v0         \n\
    :goto_Cl1                  \n\
    goto :goto_Cl0             \n\
'

# 2 registers
junk7 = '                    \n\
    const/16 v1, 0xa           \n\
    :goto_Dl0                  \n\
    goto :goto_Dl1             \n\
    const/4 v0, 0x4            \n\
    rem-int/lit8 v0, v1, 0x5   \n\
    if-ne v0, v1, :goto_Dl0    \n\
    mul-int v0, v1, v0         \n\
    :goto_Dl1                  \n\
    goto :goto_Dl0             \n\
'

# 2 registers
junk8 = '                    \n\
    const/4 v0, 0x2            \n\
    nop                        \n\
    :goto_El0                  \n\
    goto :goto_El1             \n\
    const/4 v0, 0x4            \n\
    const/4 v1, 0x2            \n\
    rem-int/lit8 v1, v0, 0x5   \n\
    mul-int v0, v1, v0         \n\
    :goto_El1                  \n\
    goto :goto_El0             \n\
'

# 2 registers
junk9 = '                    \n\
    const/4 v0, 0x2            \n\
    :goto_Fl0                  \n\
    goto :goto_Fl1             \n\
    rem-int/lit8 v0, v1, 0x7   \n\
    mul-int v0, v1, v0         \n\
    if-ne v0, v1, :goto_Fl0    \n\
    :goto_Fl1                  \n\
    const/4 v0, 0x3            \n\
    new-array v0, v0, [Ljava/lang/String; \n\
    const-string v1, "publish_stream" \n\
    goto :goto_Fl2             \n\
    new-instance v1, Ljava/lang/StringBuilder; \n\
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V  \n\
    :goto_Fl2                  \n\
    goto :goto_Fl0             \n\
'

# 2 registers
junk10 = '                    \n\
    new-instance v0, Ljava/lang/StringBuilder;  \n\
    const-string v1, "abcdefghijklmnopqrstuvwxyz1234567890"  \n\
    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(Ljava/lang/String;)V  \n\
    :goto_Gl0                  \n\
    goto :goto_Gl1             \n\
    const/4 v0, 0x4            \n\
    const/16 v1, 0xa           \n\
    rem-int/lit8 v2, v1, 0x3   \n\
    mul-int v0, v1, v0         \n\
    add-int/2addr v1, v0       \n\
    sub-int/2addr v0, v0       \n\
    and-int v0, v1, v1         \n\
    xor-int v1, v0, v1         \n\
    :goto_Gl1                  \n\
    goto :goto_Gl0             \n\
'

# 2 registers
junk11 = '                    \n\
    const/4 v0, 0x3            \n\
    const/16 v1, 0x23          \n\
    :goto_Hl0                  \n\
    goto :goto_Hl1             \n\
    sget-object v1, Ljava/lang/System;->out:Ljava/io/PrintStream;  \n\
    const-string v0, "Check OK."  \n\
    invoke-virtual {v1, v0}, Ljava/io/PrintStream;->print(Ljava/lang/String;)V  \n\
    :goto_Hl1                  \n\
    const/16 v1, 0xa           \n\
    goto :goto_Hl0             \n\
'

# 2registers
junk12 = '                   \n\
   :labelA                    \n\
   goto :labelC               \n\
   const/4 v0, 0x4            \n\
   const/16 v1, 0x12          \n\
   mul-int v0, v1, v0         \n\
   :labelB                    \n\
   goto :labelD               \n\
   const/4 v0, 0x5            \n\
   const/16 v1, 0x32          \n\
   :labelC                    \n\
   goto :labelB               \n\
   const/4 v0, 0x2            \n\
   const/16 v1, 0x23          \n\
   :labelD                    \n\
   goto :labelA               \n\
'
