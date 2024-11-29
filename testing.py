# %%
import numpy as np
import os
# %%
commondef = "_goodtime_commondef/241128_SAROC_Commondef.sqi"

# %%
class Dummy():
    pass

self = Dummy

self.Nchannels = 106

# %%
def formattext(label: str)->str:
    """Formats a label by removing tabs, white spaces and ;"""
    return label.replace('\t', "").replace(";", "").replace(" ", "")

def formatlist(inputlist: np.ndarray)->np.ndarray:
    """Returns a formatted array of channel names.
    Input:
    inputlist: ndarray from GoodTime commondef (raw)
    Output:
    res: ndarray of channel labels"""
    res = np.full(self.Nchannels,"Inactive", dtype=object)
    for label in inputlist:
        label = formattext(label)
        split = label.split("=")
        if len(split) > 1:
            chname, chnumber = split[0], int(split[1])
            print(chname)
            res[chnumber] = chname
    return res

def getlabels(commondef_fname):
    listed_names = np.genfromtxt(commondef_fname, dtype='str', comments='//', delimiter = ' = ', skip_header=15, max_rows=106, usecols=(0,))
    return formatlist(listed_names)

# %%
getlabels(commondef)
# %%
