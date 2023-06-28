from setuptools import Extension

extensions = [Extension('mathutils.angle', ["mathutils/angle.pyx"]),
              Extension("vehicleutils.vehicleutils", ["vehicleutils/vehicleutils.pyx"]),              
              Extension('dataexchange.detection_2d', ['dataexchange/detection_2d.pyx'])]