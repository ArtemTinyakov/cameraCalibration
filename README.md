GUI App for camera calibration. Can be interactively used to find projective transform matrix and find and save x, y, z, w roi coordinates.

Usage guide:
1) install pyton, flet, opencv-python, numpy, matplotlib
2) run cameraCalibration.py
3) fill text fields: cells per row and cells per column. These fields mean that the algorithm will look for a chess pattern in video frames with specific dimensions.
For example, you filled 8 8 and there is chessplate 8x8 on some of the videoframes, it will find it (or maybe not :)), but if there is 9x12 chessplate pattern on video, it won't be found anyway.
4) algorithm will stop changing frames if pattern found. You can manually change frames pressing the button "next frame".
5) if found pattern and transform is ok then click "save matrix" and projective transform matrix will be saved to file "calibration_matrix.txt".
6) there are 4 sliders in app to find roi. Scroll them and find roi you want.
7) if you found roi you want, you can click "save roi" and x, y, z, w roi coordinates (left top corner and right bottom corner) will be saved to file "roi.txt"
