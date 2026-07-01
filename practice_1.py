import numpy as np 
from PIL import Image

print("hello")

img = Image.open('qr.png')
img_array = np.array(img)

# print(img_array) 

img_reshape = img_array.reshape(img_array.shape[0],-1)

np.savetxt("oleole.txt",img_reshape,fmt="%d")

