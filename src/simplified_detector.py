"""Manuscript Section 2.3 boundary detector (sigma smoothing is in the caller)."""
from scipy.signal import find_peaks


def detect_boundaries(smoothed):
    max_peaks, _ = find_peaks(smoothed, prominence=0.02)
    min_peaks, _ = find_peaks(-smoothed, prominence=0.02)
    custom_min = list(min_peaks)

    if len(max_peaks) > 0 and (len(min_peaks) == 0 or max_peaks[0] < min_peaks[0]):
        for i in range(max_peaks[0]):
            if smoothed[i] >= 0.1:
                custom_min.append(i)
                break
    if len(max_peaks) > 0 and (len(min_peaks) == 0 or max_peaks[-1] > min_peaks[-1]):
        for i in range(len(smoothed) - 1, max_peaks[-1], -1):
            if smoothed[i] >= 0.1:
                custom_min.append(i)
                break
    return max_peaks, min_peaks, sorted(custom_min)
