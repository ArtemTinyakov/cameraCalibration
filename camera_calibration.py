import flet as ft
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart
import copy


def is_number(page, flet_container):
    try:
        res = int(flet_container.value)
        flet_container.error_text = ""
        return res
    except ValueError:
        flet_container.error_text = "incorrect value"
        page.update()
        return None


def main(page: ft.Page):
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    m, n, cap, ret, img, dst, objp, chart = None, None, None, None, None, None, None, ft.Container()
    flipped = False
    pts1, pts2 = None, None
    imgpoints = []  # 2d points in image plane.
    fig, ax = plt.subplots(1, 2)

    def next_frame(e):
        nonlocal cap, ret, img, dst, fig, ax, chart, criteria, m, n, objp, imgpoints, pts1, pts2

        ret, img = cap.read()
        ax[0].clear()
        ax[1].clear()
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        cv_ret, corners = cv.findChessboardCorners(gray, (m, n), None)
        if cv_ret:
            corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints = copy.deepcopy(corners2)
            imgpoints = np.reshape(imgpoints, (m * n, 2))
            ax[0].scatter(imgpoints.T[0], imgpoints.T[1], s=5)
            length = ((imgpoints[-1][0] - imgpoints[-2][0]) ** 2 + (imgpoints[-1][1] - imgpoints[-2][1]) ** 2) ** 0.5
            pts1 = np.float32([[int(imgpoints[0][0]), int(imgpoints[0][1])],
                               [int(imgpoints[m - 1][0]), int(imgpoints[m - 1][1])],
                               [int(imgpoints[-1][0]), int(imgpoints[-1][1])],
                               [int(imgpoints[-m][0]), int(imgpoints[-m][1])]])
            ax[0].scatter(pts1.T[0], pts1.T[1], color="red", s=8)
            pts2 = np.float32([[(pts1[0][0] + pts1[1][0]) / 2, pts1[0][1]],
                               [(pts1[0][0] + pts1[1][0]) / 2, pts1[0][1] + length * (m - 1)],
                               [(pts1[0][0] + pts1[1][0]) / 2 - length * (n - 1), pts1[0][1] + length * (m - 1)],
                               [(pts1[0][0] + pts1[1][0]) / 2 - length * (n - 1), pts1[0][1]]])
            ax[0].scatter(pts2.T[0], pts2.T[1], color="green", s=8)

            ax[0].imshow(img)

            M = cv.getPerspectiveTransform(pts1, pts2)
            dst = cv.warpPerspective(img, M, (img.shape[1], img.shape[0]))
            ax[1].imshow(dst)
            page.update()
            return

        ax[0].imshow(img)
        page.update()

    def save_matrix(e):
        nonlocal pts1, pts2, flipped

        if pts1 is not None and pts2 is not None:
            pts2_ = copy.deepcopy(pts2)
            if flipped:
                pts2_ = np.array([pts2[2], pts2[3], pts2[0], pts2[1]])
            M = cv.getPerspectiveTransform(pts1, pts2_)
            with open("calibration_matrix.txt", 'w', newline='') as fout:
                for row in M:
                    for val in row:
                        fout.write(f'{val:.12f} ')
                    fout.write('\n')

    def save_roi(e):
        nonlocal slider_roi_x, slider_roi_y, slider_roi_z, slider_roi_w

        if dst is not None:
            with open("roi.txt", 'w', newline='\n') as fout:
                fout.write(f"roi_x = {int(slider_roi_x.value)}\n")
                fout.write(f"roi_y = {int(slider_roi_y.value)}\n")
                fout.write(f"roi_z = {int(dst.shape[1] - slider_roi_z.value)}\n")
                fout.write(f"roi_w = {int(dst.shape[0] - slider_roi_w.value)}\n")

    def flip180(e):
        nonlocal dst, ax, flipped

        if dst is not None:
            cv.flip(dst, 0, dst)
            ax[1].clear()
            ax[1].imshow(dst)
            flipped = not flipped
            page.update()

    def slider_changed(e):
        nonlocal slider_roi_x, slider_roi_y, slider_roi_z, slider_roi_w

        if dst is not None:
            ax[1].clear()
            ax[1].imshow(dst)
            ax[1].plot([slider_roi_x.value, slider_roi_x.value],
                       [slider_roi_y.value, slider_roi_w.max - slider_roi_w.value], color='red', linewidth=1)
            ax[1].plot([slider_roi_z.max - slider_roi_z.value, slider_roi_z.max - slider_roi_z.value],
                       [slider_roi_y.value, slider_roi_w.max - slider_roi_w.value], color='red', linewidth=1)
            ax[1].plot([slider_roi_x.value, slider_roi_z.max - slider_roi_z.value],
                       [slider_roi_y.value, slider_roi_y.value], color='red', linewidth=1)
            ax[1].plot([slider_roi_x.value, slider_roi_z.max - slider_roi_z.value],
                       [slider_roi_w.max - slider_roi_w.value,slider_roi_w.max - slider_roi_w.value], color='red', linewidth=1)
            #ax[1].imshow(dst[int(slider_roi_y.value):int(slider_roi_w.max - slider_roi_w.value), int(slider_roi_x.value):int(slider_roi_z.max - slider_roi_z.value), :])
            page.update()

    def get_video(e: ft.FilePickerResultEvent):
        nonlocal cap, ret, img, dst, fig, ax, chart, criteria, m, n, objp, imgpoints, pts1, pts2

        m, n, cap, ret, img, objp, chart = None, None, None, None, None, None, ft.Container()
        pts1, pts2 = None, None
        imgpoints = []  # 2d points in image plane.
        fig, ax = plt.subplots(1, 2)

        if len(page.controls[0].controls) > 1:
            page.controls[0].controls = page.controls[0].controls[:-1]

        m, n = is_number(page, rows), is_number(page, columns)

        if m is None or n is None:
            page.update()
            return

        m -= 1
        n -= 1

        rows.error_text = ""
        columns.error_text = ""

        page.update()

        objp = np.zeros((n * m, 3), np.float32)
        objp[:, :2] = np.mgrid[0:m, 0:n].T.reshape(-1, 2)

        cap = cv.VideoCapture(e.files[0].path)

        ret, img = cap.read()

        if ret:
            ax[0].imshow(img)
            chart = MatplotlibChart(fig, expand=True)
            page.controls[0].controls.append(chart)
            slider_roi_x.max = img.shape[1] - 1
            slider_roi_y.max = img.shape[0] - 1
            slider_roi_z.max = img.shape[1] - 1
            slider_roi_w.max = img.shape[0] - 1
            slider_roi_x.divisions = (slider_roi_x.max + 1) / 10
            slider_roi_y.divisions = (slider_roi_y.max + 1) / 10
            slider_roi_z.divisions = (slider_roi_z.max + 1) / 10
            slider_roi_w.divisions = (slider_roi_w.max + 1) / 10
            page.update()

        while ret:
            ax[0].clear()
            ax[1].clear()
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            cv_ret, corners = cv.findChessboardCorners(gray, (m, n), None)
            if cv_ret:
                corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                imgpoints = copy.deepcopy(corners2)
                imgpoints = np.reshape(imgpoints, (m * n, 2))
                ax[0].scatter(imgpoints.T[0], imgpoints.T[1], s=5)
                length = ((imgpoints[-1][0] - imgpoints[-2][0]) ** 2 + (
                            imgpoints[-1][1] - imgpoints[-2][1]) ** 2) ** 0.5
                pts1 = np.float32([[int(imgpoints[0][0]), int(imgpoints[0][1])],
                                   [int(imgpoints[m - 1][0]), int(imgpoints[m - 1][1])],
                                   [int(imgpoints[-1][0]), int(imgpoints[-1][1])],
                                   [int(imgpoints[-m][0]), int(imgpoints[-m][1])]])
                ax[0].scatter(pts1.T[0], pts1.T[1], color="red", s=8)
                pts2 = np.float32([[(pts1[0][0] + pts1[1][0]) / 2, pts1[0][1]],
                                   [(pts1[0][0] + pts1[1][0]) / 2, pts1[0][1] + length * (m - 1)],
                                   [(pts1[0][0] + pts1[1][0]) / 2 - length * (n - 1), pts1[0][1] + length * (m - 1)],
                                   [(pts1[0][0] + pts1[1][0]) / 2 - length * (n - 1), pts1[0][1]]])
                ax[0].scatter(pts2.T[0], pts2.T[1], color="green", s=8)

                ax[0].imshow(img)

                M = cv.getPerspectiveTransform(pts1, pts2)
                dst = cv.warpPerspective(img, M, (img.shape[1], img.shape[0]))
                ax[1].imshow(dst)
                page.update()
                return

            ax[0].imshow(img)
            page.update()

            ret, img = cap.read()

    page.title = "camera calibration"

    pick_files_dialog = ft.FilePicker(on_result=get_video)

    page.overlay.append(pick_files_dialog)

    rows = ft.TextField(
        label="cells per row",
        hint_text="18",
    )

    columns = ft.TextField(
        label="cells per column",
        hint_text="13",
    )

    slider_roi_x = ft.Slider(value=0, min=0, divisions=1, label="{value}", on_change_end=slider_changed)

    slider_roi_y = ft.Slider(value=0, min=0, divisions=1, label="{value}", on_change_end=slider_changed)

    slider_roi_z = ft.Slider(value=0, min=0, divisions=1, label="{value}", on_change_end=slider_changed)

    slider_roi_w = ft.Slider(value=0, min=0, divisions=1, label="{value}", on_change_end=slider_changed)

    page.add(
        ft.Row(
            [
                ft.Column(
                    [
                        ft.ElevatedButton(
                            "Choose video",
                            icon=ft.icons.UPLOAD_FILE,
                            on_click=lambda _: pick_files_dialog.pick_files(
                                allow_multiple=False
                            ),
                        ),
                        ft.Row(
                            [
                                rows,
                                columns,
                            ]
                        ),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "next frame",
                                    on_click=next_frame,
                                ),
                                ft.ElevatedButton(
                                    "flip",
                                    on_click=flip180,
                                ),
                            ]
                        ),
                        ft.ElevatedButton(
                            "save matrix",
                            on_click=save_matrix,
                        ),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text("margin left"),
                                        slider_roi_x,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("margin top"),
                                        slider_roi_y,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text("margin right"),
                                        slider_roi_z,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ft.Column(
                                    [
                                        ft.Text("margin bottom"),
                                        slider_roi_w,
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ]
                        ),
                        ft.ElevatedButton(
                            "save roi",
                            on_click=save_roi,
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=25,
                ),
                ft.Column(
                    [
                        chart,
                    ]
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


ft.app(target=main)
