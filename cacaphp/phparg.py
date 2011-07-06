#!/usr/bin/env python
import popen2
import sys
import re
import pickle

rx_exactly = re.compile(".*expects exactly (\d+) parameter")
rx_least = re.compile(".*at least (\d+) parameter")

phpfuncs = {}
ff = open("phpfuncs", "r")
for funcs in ff.readlines():
    print funcs[:-1]
    pf = open("caca.php", "w")
    pf.write("<?php\n")
    pf.write(funcs[:-1] + """();\n""")
    pf.write("?>")
    pf.close()
    r, i, e = popen2.popen3('php caca.php')
    for e in e.readlines():
        m = rx_exactly.match(e)
        if m:
            phpfuncs[funcs[:-1]] = int(m.group(1))
        else:
            m = rx_least.match(e)
            if m:
                phpfuncs[funcs[:-1] + "+"] = int(m.group(1))
            else:
                phpfuncs[funcs[:-1]] = 0
    r.close()
    i.close()
ff.close()

phpclasses = {}
method = "Foo"
cc = open("phpmethods", "r")
for line in cc.readlines():
    if line[0] == "+":
        method = line[1:-1]
        phpclasses[method] = {}
        continue
    print method + "->" + line[:-1]
    pf = open("caca.php", "w")
    pf.write("<?php\n")
    pf.write("$x = new " + method + "();\n")
    pf.write("$x->"  + line[:-1] + "();\n")
    pf.write("?>")
    pf.close()
    r, i, e = popen2.popen3('php caca.php')
    for e in e.readlines():
        m = rx_exactly.match(e)
        if m:
            phpclasses[method][line[:-1]] = int(m.group(1))
        else:
            m = rx_least.match(e)
            if m:
                phpclasses[method][line[:-1] + "+"] = int(m.group(1))
            else:
                phpclasses[method][line[:-1]] = 0
    r.close()
    i.close()
cc.close()

output = open('phpfuncs.pkl', 'wb')
pickle.dump(phpfuncs, output)
output.close()

output = open('phpmethods.pkl', 'wb')
pickle.dump(phpclasses, output)
output.close()
