# %%
import numpy as np
import os
# %%
commondef = "_goodtimeçcommondef/commondef_fix.sqi"

# %%
res = np.genfromtxt(commondef, encoding='utf-8',\
                            dtype='str', comments='//', delimiter = ' = ', skip_header=15, max_rows=79, usecols=(0,))
# %%

res = ''
with open(commondef, "r", errors="ignore") as f:
    line = f.read()
    res += line
# %%
with open("commondef_fix.sqi", 'w') as f:
    f.write(res)
# %%

