import cv2

for i in range(10):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    opened = cap.isOpened()
    print(f"camera {i}: opened = {opened}")

    if opened:
        ret, frame = cap.read()
        print(f"camera {i}: read = {ret}")

        if ret:
            print(f"camera {i}: frame shape = {frame.shape}")

    cap.release()
