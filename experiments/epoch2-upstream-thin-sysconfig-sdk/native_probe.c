#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject *meaning(PyObject *self, PyObject *args) {
    (void)self; (void)args;
    return PyLong_FromLong(42);
}

static PyObject *runtime_prefix(PyObject *self, PyObject *args) {
    (void)self; (void)args;
    const wchar_t *p = Py_GetPrefix();
    if (p == NULL) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromWideChar(p, -1);
}

static PyMethodDef methods[] = {
    {"meaning", meaning, METH_NOARGS, "Return the probe sentinel."},
    {"runtime_prefix", runtime_prefix, METH_NOARGS, "Return Py_GetPrefix()."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "hw_t_native_probe",
    "HW-T native extension SDK probe.",
    -1,
    methods
};

PyMODINIT_FUNC PyInit_hw_t_native_probe(void) {
    return PyModule_Create(&module);
}
