import base64
import tempfile

from rpy2.robjects.packages import importr

ribios_utils = importr("ribiosUtils")


def gen_base64_plot(plot_opr, width=15, height=15):
    plot_fd, plot_file_path = tempfile.mkstemp(suffix=".png")
    ribios_utils.openFileDevice(plot_file_path, width=width, height=height)
    plot_opr()
    ribios_utils.closeFileDevice()

    with open(plot_file_path, "rb") as image_file:
        return str(base64.b64encode(image_file.read()), "utf-8")
