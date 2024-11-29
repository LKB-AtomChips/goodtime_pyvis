# encoding: utf-8
# Created by Clement Raphin on Nov. 29, 2024
# A quick utility to fix undecypherable characters in file.

import numpy as np

# Path to file to fix
commondef_fname = "_goodtime_commondef/241128_SAROC_Commondef.sqi"

# Creating new file path
fixed_filepath = commondef_fname[:-4] + "_fix.sqi"

# Opening file in failsafe mode
res = ''

with open(commondef_fname, "r", errors="ignore") as f:
    for line in f.read():
        res += line

# writing clean filequit
with open(fixed_filepath, 'w') as f:
    f.write(res)