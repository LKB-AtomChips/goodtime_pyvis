# %%
import numpy as np
import os
# %%
commondef = "_goodtime_commondef/241128_SAROC_Commondef.sqi"

# %%
res = np.genfromtxt(commondef, encoding='utf-8',\
                            dtype='str', comments='//', delimiter = ' = ', skip_header=15, max_rows=79, usecols=(0,))
# %%
