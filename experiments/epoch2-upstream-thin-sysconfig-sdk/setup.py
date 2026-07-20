from setuptools import Extension, setup

setup(
    name="hw-t-native-probe",
    version="0.1.0",
    description="HW-T Android native extension SDK probe",
    ext_modules=[Extension("hw_t_native_probe", ["native_probe.c"])],
)
