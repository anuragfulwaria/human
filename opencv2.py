import cv2
import numpy as np
import time

cap = cv2.VideoCapture(0)
# cap2 = cv2.VideoCapture(0)

ret,frame3 = cap.read()



while True:
    ret,frame1 = cap.read()

    # grey = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY)
    # ret2,frame2 = cap2.read()
    # print(frame.ndim,frame.shape,frame.size)
    # print("")
    # grey = cv2.GaussianBlur(grey,(11,11),0)
    # grey1 = cv2.GaussianBlur(grey,(1,1),0)
    # grey2 = cv2.GaussianBlur(grey,(9,9),0)
    # grey3 = cv2.GaussianBlur(grey,(19,19),0)

    # frame = cv2.add(frame1,grey)

    # zero = np.zeros((3,4))
    # print(zero)
    # frame = np.multiply(grey,zero)
    # cv2.imshow('frame2',frame2)
    # cv2.imshow('grey',grey)
    # cv2.imshow('grey1',grey1)
    # cv2.imshow('grey2',grey2)
    # cv2.imshow('grey3',grey3)
    cv2.imshow('frame1',frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
# cap2.release()
cv2.destroyAllWindows()
