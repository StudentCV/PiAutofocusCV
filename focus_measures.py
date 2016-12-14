import cv2
import numpy as np


class ContrastMeasures():

    def __init__(self):
        pass

    def fm(self, img, fm_name, window_size=3, threshold=7):
        """
        applies focus measure fm_name to input image img
        fm_name must be one of the following:
        'SML', 'CMSL', 'GLV', 'TENENGRAD1', 'JAEHNE'"""
        if fm_name == 'SML':
            return self.SML(img, window_size, threshold)
        elif fm_name == 'CMSL':
            return self.CMSL(img, window_size)
        elif fm_name == 'GLV':
            return self.GLV(img, window_size)
        elif fm_name == 'TENENGRAD1':
            return self.tenengrad1(img, window_size, threshold)
        elif fm_name == 'JAEHNE':
            return self.jaehne(img, window_size)

    def CMSL(self, img, window):
        """
        Contrast Measure based on squared Laplacian according to
        'Robust Automatic Focus Algorithm for Low Contrast Images
        Using a New Contrast Measure'
        by Xu et Al. doi:10.3390/s110908281
        window: window size= window X window"""
        ky1 = np.array(([0.0, -1.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]))
        ky2 = np.array(([0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]))
        kx1 = np.array(([0.0, 0.0, 0.0], [-1.0, 1.0, 0.0], [0.0, 0.0, 0.0]))
        kx2 = np.array(([0.0, 0.0, 0.0], [0.0, 1.0, -1.0], [0.0, 0.0, 0.0]))
        g_img = abs(cv2.filter2D(img, cv2.CV_32F, kx1)) + \
                abs(cv2.filter2D(img, cv2.CV_32F, ky1)) + \
                abs(cv2.filter2D(img, cv2.CV_32F, kx2)) + \
                abs(cv2.filter2D(img, cv2.CV_32F, ky2))
        return cv2.boxFilter(
                                g_img * g_img,
                                -1,
                                (window, window),
                                normalize=True)

    def SML(self, img_in, window_size, threshold):
        """
        Sum of modified Laplacian according to
        'Depth Map Estimation Using Multi-Focus Imaging'
        by Mendapara
        """
        # kernels in x- and y -direction for Laplacian
        ky = np.array(([0.0, -1.0, 0.0], [0.0, 2.0, 0.0], [0.0, -1.0, 0.0]))
        kx = np.array(([0.0, 0.0, 0.0], [-1.0, 2.0, -1.0], [0.0, 0.0, 0.0]))
        # add absoulte of image convolved with kx to absolute
        # of image convolved with ky (modified laplacian)
        ml_img = abs(cv2.filter2D(img_in, cv2.CV_32F, kx)) + \
                abs(cv2.filter2D(img_in, cv2.CV_32F, ky))
        # sum up all values that are bigger than threshold in window
        ret, img_t = cv2.threshold(ml_img, threshold, 0.0, cv2.THRESH_TOZERO)
        return cv2.boxFilter(
                                img_t,
                                -1,
                                (window_size, window_size),
                                normalize=False)

    def GLV(self, img, window_size=3):
        """
        Gray Level Variance according to
        'Depth Map Estimation Using Multi-Focus Imaging'
        by Mendapara
        """
        # calculate mean for each window
        mean = cv2.boxFilter(
                                img,
                                cv2.CV_32F,
                                (window_size, window_size),
                                normalize=True)
        # return variance=(img[x,y]-mean[x,y])^2
        return (img - mean)**2.0

    def tenengrad1(self, img, window_size, threshold):
        """
        Tenengrad2b: squared gradient absolute thresholded and 
        summed up in each window
        according to
        'Autofocusing Algorithm Selection in Computer Microscopy'
        by Sun et Al.
        """
        # calculate gradient magnitude:
        S = cv2.Sobel(img, cv2.CV_32F, 1, 0, 3)**2.0 + \
            cv2.Sobel(img, cv2.CV_32F, 0, 1, 3)**2.0
        # threshold image
        ret, dst = cv2.threshold(S, threshold, 0.0, cv2.THRESH_TOZERO)
        # return thresholded image summed up in each window:
        return cv2.boxFilter(
                                dst,
                                -1,
                                (window_size, window_size),
                                normalize=False)

    def jaehne(self, img, window_size):
        """Only implemented for window_size 3 or 5 according to
        'Entwicklung einer fokusbasierenden Hoehenmessung mit
        dem "Depth from Focus"-Verfahren' by Dunck
        """
        if window_size == 3:
            kernel = np.array([
                            [1.0, 2.0, 1.0],
                            [2.0, 4.0, 2.0],
                            [1.0, 2.0, 1.0]])
            sum = 16
        elif window_size == 5:
            kernel = np.array([
                            [1.0, 4.0, 6.0, 4.0, 1.0],
                            [4.0, 16.0, 24.0, 16.0, 4.0],
                            [6.0, 24.0, 36.0, 24.0, 6.0],
                            [4.0, 16.0, 24.0, 16.0, 4.0],
                            [1.0, 4.0, 6.0, 4.0, 1.0]])
            sum = 256
        img_t = (img - cv2.filter2D(img, cv2.CV_32F, kernel) / sum)**2
        return cv2.filter2D(img_t, -1, kernel) / sum
