# %%
import numpy as np
# %%

class Test():
    def __init__(self):
        # self.fileName = "//MOUFFETARD/goodTime_exchange"
        self.fileName = "D:/PythonProjects/goodTime_pyvis/_sampleGTfiles"
        Device1 = np.fromfile(self.fileName + '/DigBuffer1.bin', dtype=np.uint8).reshape(-1,1)
        self.Device1 = np.flip(np.unpackbits(Device1, axis=1), axis=1).reshape(-1,32)
        Device5dig = np.fromfile(self.fileName + '/DigBuffer2.bin', dtype=np.uint8).reshape(-1,1)
        self.Device5dig = np.flip(np.unpackbits(Device5dig, axis=1), axis=1).reshape(-1,32)
        

test = Test()
# %%
test.Device5dig

# %%
test.Device1

# %%
np.shape(test.Device5dig)
# %%
