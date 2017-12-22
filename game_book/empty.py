
import os

for it in os.walk("."):
        dir = it[0]
        if len(os.listdir(dir)) == 0:
                print(dir)
                os.rmdir(dir)